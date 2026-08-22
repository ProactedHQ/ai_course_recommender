"""
Management command to clear all non-user data from the database.
Usage: python manage.py clear_non_user_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from students.models import (
    Subject, AcademicResult, StudentAttribute, 
    CareerGoal, PromptSubmission
)
from universities.models import (
    Institution, ProgrammeLevel, ClusterGroup, Programme,
    ProgrammeOffering, ProgrammeRequirement, CutOffPoint
)
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Clear all non-user data from the database (preserves user accounts)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("DATABASE CLEANUP - NON-USER DATA")
        self.stdout.write("="*60)
        
        # Count existing data
        self.stdout.write("\nCURRENT DATA COUNTS:")
        self.stdout.write(f"  Users: {CustomUser.objects.count()}")
        self.stdout.write(f"  Subjects: {Subject.objects.count()}")
        self.stdout.write(f"  Institutions: {Institution.objects.count()}")
        self.stdout.write(f"  Programme Levels: {ProgrammeLevel.objects.count()}")
        self.stdout.write(f"  Cluster Groups: {ClusterGroup.objects.count()}")
        self.stdout.write(f"  Programmes: {Programme.objects.count()}")
        self.stdout.write(f"  Programme Offerings: {ProgrammeOffering.objects.count()}")
        self.stdout.write(f"  Programme Requirements: {ProgrammeRequirement.objects.count()}")
        self.stdout.write(f"  Cut-off Points: {CutOffPoint.objects.count()}")
        self.stdout.write(f"  Academic Results: {AcademicResult.objects.count()}")
        self.stdout.write(f"  Student Attributes: {StudentAttribute.objects.count()}")
        self.stdout.write(f"  Career Goals: {CareerGoal.objects.count()}")
        self.stdout.write(f"  Prompt Submissions: {PromptSubmission.objects.count()}")
        
        self.stdout.write("\nWARNING: This will DELETE all data listed above.")
        self.stdout.write("   USER ACCOUNTS will be PRESERVED.")
        
        # Confirmation
        if not options['force']:
            confirm = input("\nType 'DELETE' to confirm deletion: ")
            if confirm != "DELETE":
                self.stdout.write(self.style.WARNING("\nDeletion cancelled. No changes made."))
                return
        
        self.stdout.write("\nStarting deletion process...")
        
        try:
            with transaction.atomic():
                # Delete in order to avoid foreign key constraints
                
                # 1. Delete student-related data
                deleted_prompt_submissions = PromptSubmission.objects.all().delete()[0]
                deleted_career_goals = CareerGoal.objects.all().delete()[0]
                deleted_attributes = StudentAttribute.objects.all().delete()[0]
                deleted_results = AcademicResult.objects.all().delete()[0]
                
                # 2. Delete university/programme data (order matters due to FK constraints)
                deleted_cutoffs = CutOffPoint.objects.all().delete()[0]
                deleted_requirements = ProgrammeRequirement.objects.all().delete()[0]
                deleted_offerings = ProgrammeOffering.objects.all().delete()[0]
                deleted_programmes = Programme.objects.all().delete()[0]
                deleted_clusters = ClusterGroup.objects.all().delete()[0]
                deleted_levels = ProgrammeLevel.objects.all().delete()[0]
                deleted_institutions = Institution.objects.all().delete()[0]
                
                # 3. Delete subjects
                deleted_subjects = Subject.objects.all().delete()[0]
                
                self.stdout.write(self.style.SUCCESS("\nDELETION COMPLETE!"))
                self.stdout.write("\nDELETED COUNTS:")
                self.stdout.write(f"  Subjects: {deleted_subjects}")
                self.stdout.write(f"  Institutions: {deleted_institutions}")
                self.stdout.write(f"  Programme Levels: {deleted_levels}")
                self.stdout.write(f"  Cluster Groups: {deleted_clusters}")
                self.stdout.write(f"  Programmes: {deleted_programmes}")
                self.stdout.write(f"  Programme Offerings: {deleted_offerings}")
                self.stdout.write(f"  Programme Requirements: {deleted_requirements}")
                self.stdout.write(f"  Cut-off Points: {deleted_cutoffs}")
                self.stdout.write(f"  Academic Results: {deleted_results}")
                self.stdout.write(f"  Student Attributes: {deleted_attributes}")
                self.stdout.write(f"  Career Goals: {deleted_career_goals}")
                self.stdout.write(f"  Prompt Submissions: {deleted_prompt_submissions}")
                
                # Verify user accounts preserved
                user_count = CustomUser.objects.count()
                self.stdout.write(self.style.SUCCESS(f"\nUSER ACCOUNTS PRESERVED: {user_count}"))
                
                self.stdout.write("\n" + "="*60)
                self.stdout.write(self.style.SUCCESS("Database is now clean and ready for new migrations!"))
                self.stdout.write("="*60 + "\n")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nERROR during deletion: {e}"))
            self.stdout.write(self.style.ERROR("Transaction rolled back. No changes made."))
            raise
