"""
Clear all non-user data from the database.

This script deletes:
- Subjects, Institutions, Clusters, Programmes, Offerings, Cut-offs
- Student academic results, attributes, career goals, prompt submissions

This script PRESERVES:
- User accounts (CustomUser)
- StudentProfile records linked to users

Usage:
    python manage.py shell < scripts/clear_non_user_data.py

Or from Django shell:
    exec(open('scripts/clear_non_user_data.py').read())
"""

import sys
import os

# Ensure Django is setup
import django
django.setup()

from django.db import transaction
from apps.students.models import (
    Subject, AcademicResult, StudentAttribute, 
    CareerGoal, PromptSubmission
)
from apps.universities.models import (
    Institution, ProgrammeLevel, ClusterGroup, Programme,
    ProgrammeOffering, ProgrammeRequirement, CutOffPoint
)
from apps.users.models import CustomUser

def clear_non_user_data():
    """Clear all non-user data from the database."""
    
    print("\n" + "="*60)
    print("DATABASE CLEANUP - NON-USER DATA")
    print("="*60)
    
    # Count existing data
    print("\n📊 CURRENT DATA COUNTS:")
    print(f"  Users: {CustomUser.objects.count()}")
    print(f"  Subjects: {Subject.objects.count()}")
    print(f"  Institutions: {Institution.objects.count()}")
    print(f"  Programme Levels: {ProgrammeLevel.objects.count()}")
    print(f"  Cluster Groups: {ClusterGroup.objects.count()}")
    print(f"  Programmes: {Programme.objects.count()}")
    print(f"  Programme Offerings: {ProgrammeOffering.objects.count()}")
    print(f"  Programme Requirements: {ProgrammeRequirement.objects.count()}")
    print(f"  Cut-off Points: {CutOffPoint.objects.count()}")
    print(f"  Academic Results: {AcademicResult.objects.count()}")
    print(f"  Student Attributes: {StudentAttribute.objects.count()}")
    print(f"  Career Goals: {CareerGoal.objects.count()}")
    print(f"  Prompt Submissions: {PromptSubmission.objects.count()}")
    
    print("\n⚠️  WARNING: This will DELETE all data listed above.")
    print("   USER ACCOUNTS will be PRESERVED.")
    
    # Confirmation
    confirm = input("\nType 'DELETE' to confirm deletion: ")
    
    if confirm != "DELETE":
        print("\n❌ Deletion cancelled. No changes made.")
        return
    
    print("\n🗑️  Starting deletion process...")
    
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
            
            print("\n✅ DELETION COMPLETE!")
            print("\n📊 DELETED COUNTS:")
            print(f"  Subjects: {deleted_subjects}")
            print(f"  Institutions: {deleted_institutions}")
            print(f"  Programme Levels: {deleted_levels}")
            print(f"  Cluster Groups: {deleted_clusters}")
            print(f"  Programmes: {deleted_programmes}")
            print(f"  Programme Offerings: {deleted_offerings}")
            print(f"  Programme Requirements: {deleted_requirements}")
            print(f"  Cut-off Points: {deleted_cutoffs}")
            print(f"  Academic Results: {deleted_results}")
            print(f"  Student Attributes: {deleted_attributes}")
            print(f"  Career Goals: {deleted_career_goals}")
            print(f"  Prompt Submissions: {deleted_prompt_submissions}")
            
            # Verify user accounts preserved
            user_count = CustomUser.objects.count()
            print(f"\n✅ USER ACCOUNTS PRESERVED: {user_count}")
            
            print("\n" + "="*60)
            print("Database is now clean and ready for new migrations!")
            print("="*60 + "\n")
            
    except Exception as e:
        print(f"\n❌ ERROR during deletion: {e}")
        print("Transaction rolled back. No changes made.")
        raise

if __name__ == "__main__":
    clear_non_user_data()
