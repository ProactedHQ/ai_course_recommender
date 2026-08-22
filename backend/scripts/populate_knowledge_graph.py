
import os
import sys
import django

# Add project root and apps to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.universities.models import KnowledgeNode, KnowledgeLink, Programme
from apps.students.models import Subject

def populate():
    print("Seeding Knowledge Graph...")

    # 1. Create Subject Area Nodes
    subjects = Subject.objects.all()
    for sub in subjects:
        KnowledgeNode.objects.get_or_create(
            name=sub.name,
            node_type='SUBJECT_AREA',
            defaults={'description': f"KCSE Subject: {sub.name}"}
        )

    # 2. Create sample Career Outcome Nodes
    outcomes = [
        ("Software Engineer", "Develops applications, systems, and software solutions."),
        ("Civil Engineer", "Designs and oversees construction of infrastructure like roads and bridges."),
        ("Medical Doctor", "Diagnoses and treats illnesses and injuries."),
        ("Data Scientist", "Analyzes complex data to help organizations make decisions."),
        ("Mechanical Engineer", "Designs and manufactures mechanical systems and tools."),
        ("Electrical Engineer", "Designs and develops electrical systems and equipment."),
        ("Architect", "Designs buildings and structures."),
        ("Accountant", "Manages financial records and taxes."),
        ("Lawyer", "Provides legal advice and represents clients in legal matters."),
        ("Nurse", "Provides care and support to patients in healthcare settings."),
        ("Teacher", "Educates students in various subjects and levels."),
    ]

    for name, desc in outcomes:
        KnowledgeNode.objects.get_or_create(
            name=name,
            node_type='CAREER_OUTCOME',
            defaults={'description': desc}
        )

    # 3. Create sample Skills
    skills = [
        ("Programming", "Writing and testing code in various languages."),
        ("Problem Solving", "Identifying and resolving complex issues."),
        ("Critical Thinking", "Analyzing information objectively to make judgments."),
        ("Communication", "Expressing ideas clearly and effectively."),
        ("Data Analysis", "Extracting insights from raw data."),
    ]

    for name, desc in skills:
        KnowledgeNode.objects.get_or_create(
            name=name,
            node_type='SKILL',
            defaults={'description': desc}
        )

    # 4. Create Links (Prerequisites & Leads To)
    links = [
        ("Mathematics Alt A", "Software Engineer", "PREREQUISITE"),
        ("Mathematics Alt A", "Civil Engineer", "PREREQUISITE"),
        ("Physics", "Mechanical Engineer", "PREREQUISITE"),
        ("Biology", "Medical Doctor", "PREREQUISITE"),
        ("Chemistry", "Medical Doctor", "PREREQUISITE"),
        ("Programming", "Software Engineer", "LEADS_TO"),
        ("Problem Solving", "Software Engineer", "LEADS_TO"),
    ]

    for source_name, target_name, link_type in links:
        try:
            source = KnowledgeNode.objects.get(name=source_name)
            target = KnowledgeNode.objects.get(name=target_name)
            KnowledgeLink.objects.get_or_create(
                source=source,
                target=target,
                link_type=link_type
            )
        except KnowledgeNode.DoesNotExist:
            print(f"Skipping link: {source_name} -> {target_name} (Node not found)")

    # 5. Link Programmes to Career Outcomes
    print("Mapping Programmes to Career Outcomes...")
    from apps.universities.models import ProgrammeOutcomeMapping
    
    # Simple mapping based on name overlap
    all_programmes = Programme.objects.all()
    all_outcomes = KnowledgeNode.objects.filter(node_type='CAREER_OUTCOME')
    
    mapping_count = 0
    for prog in all_programmes:
        for outcome in all_outcomes:
            # Check if outcome name is in programme name (e.g. "Civil Engineer" in "Civil Engineering")
            # We use a simple fuzzy match (removing "ing", "er", etc.)
            clean_prog = prog.name.lower().replace("engineering", "engineer").replace("nursing", "nurse")
            if outcome.name.lower() in clean_prog:
                ProgrammeOutcomeMapping.objects.get_or_create(
                    programme=prog,
                    outcome=outcome
                )
                mapping_count += 1
                
    print(f"Knowledge Graph seeding complete. Mapped {mapping_count} programmes.")

if __name__ == "__main__":
    populate()
