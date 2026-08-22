"""
Django management command to test KCSE cluster points calculator
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test KCSE cluster points calculator with sample student data'

    def handle(self, *args, **options):
        # Import after Django is fully loaded
        from universities.utils.eligibility_filter import get_eligible_programmes, filter_eligible_only
        from universities.utils.points_calculator import calculate_aggregate_points
        from universities.utils.requirement_parser import CODE_TO_NAME

        # Sample student grades (using subject codes)
        # This student has strong performance in sciences/math
        sample_student_grades = {
            '101': 'B+',   # English
            '102': 'C+',   # Kiswahili
            '121': 'A-',   # Mathematics Alternative A
            '232': 'A',    # Biology
            '233': 'B+',   # Chemistry
            '231': 'B',    # Physics
            '311': 'C+',   # Geography
            '571': 'B-',   # Business Studies
        }

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("KCSE CLUSTER POINTS CALCULATOR - TEST"))
        self.stdout.write("=" * 70)

        self.stdout.write("\n[Student Grades]")
        self.stdout.write("-" * 70)
        for code, grade in sample_student_grades.items():
            subject_name = CODE_TO_NAME.get(code, code)
            self.stdout.write(f"  {subject_name:40} {grade}")

        # Calculate aggregate
        aggregate = calculate_aggregate_points(sample_student_grades)
        self.stdout.write(f"\n[Total Aggregate Points]: {aggregate}/84")

        self.stdout.write("\n[Finding eligible programmes...]")
        self.stdout.write("-" * 70)

        # Get all programmes (eligible and not eligible)
        all_programmes = get_eligible_programmes(sample_student_grades, target_year=2024)

        self.stdout.write(f"\n[OK] Total programmes analyzed: {len(all_programmes)}")

        # Filter to only eligible
        eligible = filter_eligible_only(all_programmes)

        self.stdout.write(self.style.SUCCESS(f"[OK] Eligible programmes (student meets cutoff): {len(eligible)}"))
        self.stdout.write(self.style.WARNING(f"[X] Not eligible (below cutoff): {len(all_programmes) - len(eligible)}"))

        # Show top 10 eligible programmes
        if eligible:
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("TOP 10 ELIGIBLE PROGRAMMES"))
            self.stdout.write("=" * 70)

            for i, prog_dict in enumerate(eligible[:10], 1):
                prog = prog_dict['programme']
                inst = prog_dict['institution']
                cluster_subjects = prog_dict['cluster_subjects']

                self.stdout.write(f"\n{i}. {self.style.SUCCESS(prog.name)}")
                self.stdout.write(f"   Institution: {inst.name}")
                self.stdout.write(f"   Cluster: {prog_dict['cluster'].name}")
                self.stdout.write(f"   Subcluster: {prog_dict['subcluster'].code}")
                self.stdout.write(f"   Student Points: {self.style.SUCCESS(str(prog_dict['student_points']))}")
                self.stdout.write(f"   Cutoff Points: {prog_dict['cutoff_points']} ({prog_dict['cutoff_year']})")
                margin_text = f"+{prog_dict['points_margin']} points above cutoff"
                self.stdout.write(f"   Margin: {self.style.SUCCESS(margin_text)}")
                self.stdout.write(f"   Cluster Subjects Used:")
                for code, grade, points in cluster_subjects:
                    subj_name = CODE_TO_NAME.get(code, code)
                    self.stdout.write(f"      - {subj_name} ({grade}): {points} pts")
        else:
            self.stdout.write("\n" + self.style.ERROR("❌ No eligible programmes found for this student."))
            self.stdout.write("\nShowing why student was disqualified for first 5 clusters:")

            # Get unique clusters that were checked
            from universities.models import ClusterGroup, ProgrammeLevel
            from universities.utils.requirement_parser import parse_all_cluster_requirements
            from universities.utils.subject_matcher import find_best_subject_combination
            from universities.utils.points_calculator import calculate_cluster_points

            degree_level = ProgrammeLevel.objects.get(name='DEGREE')
            clusters = ClusterGroup.objects.filter(level=degree_level)[:5]

            for cluster in clusters:
                reqs = parse_all_cluster_requirements(cluster)
                cluster_subjects = find_best_subject_combination(sample_student_grades, reqs)

                if cluster_subjects:
                    points = calculate_cluster_points(cluster_subjects, aggregate)
                    self.stdout.write(f"\n  ✅ {cluster.name}: {points} points")
                else:
                    self.stdout.write(f"\n  {self.style.ERROR('❌')} {cluster.name}: Requirements NOT met")
                    self.stdout.write(f"     Required:")
                    self.stdout.write(f"       1. {cluster.subject_1}")
                    self.stdout.write(f"       2. {cluster.subject_2}")
                    self.stdout.write(f"       3. {cluster.subject_3}")
                    self.stdout.write(f"       4. {cluster.subject_4}")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("TEST COMPLETE"))
        self.stdout.write("=" * 70)
