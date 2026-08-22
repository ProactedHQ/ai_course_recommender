from django.db import transaction
from django.utils import timezone
from apps.students.models import (
    StudentProfile, Subject, AcademicResult, 
    StudentAttribute, Influence, DecisionPriority, CareerGoal
)

def persist_student_profile_from_wizard(user, payload):
    """
    Persists the multi-step wizard data into normalized student tables.
    Does NOT create PromptSubmission (that is handled by the ViewSet).
    
    Args:
        user: The authenticated user instance.
        payload: The full JSON payload from the wizard.
        
    Returns:
        The updated StudentProfile instance.
    """
    
    # Extract the actual student_profile data from the nested structure
    # Frontend sends: {"payload": {"student_profile": {...}}}
    data = payload.get('payload', payload)
    student_profile_data = data.get('student_profile', data)
    
    # Extract major sections
    kcse_data = student_profile_data.get('kcse', {})
    personal_cognitive = student_profile_data.get('personal_cognitive', {})
    practical_factors = student_profile_data.get('practical_factors', {})
    interests_exposure = student_profile_data.get('interests_exposure', {})
    influences_list = student_profile_data.get('influences', [])
    decision_priorities_data = student_profile_data.get('decision_priorities', {})

    with transaction.atomic():
        # 1. Get or Create Profile
        profile, created = StudentProfile.objects.get_or_create(user=user)
        
        # 2. Update Profile Fields from personal_cognitive
        profile.self_description = personal_cognitive.get('self_description')
        
        # Process short-term goals: trim, dedupe, default to []
        raw_short_term_goals = personal_cognitive.get('short_term_goals_1_3_years', [])
        if raw_short_term_goals and isinstance(raw_short_term_goals, list):
            # Trim whitespace and remove empty strings
            cleaned_goals = [g.strip() for g in raw_short_term_goals if g and str(g).strip()]
            # Deduplicate while preserving order
            seen = set()
            profile.short_term_goals = [g for g in cleaned_goals if not (g in seen or seen.add(g))]
        else:
            profile.short_term_goals = []
        
        profile.long_term_goals = personal_cognitive.get('long_term_goals_career')
        
        # Extract career aspirations for later processing
        raw_career_aspirations = personal_cognitive.get('career_aspirations', [])
        
        # 3. Update Profile Fields from practical_factors
        profile.time_hours_per_week = practical_factors.get('time_hours_per_week')
        profile.budget_kes_estimate = practical_factors.get('budget_kes_estimate')
        profile.preferred_location = practical_factors.get('preferred_location')
        profile.constraints_notes = practical_factors.get('constraints_notes')
        
        # 4. Update Profile Fields from interests_exposure
        profile.exposure_notes = interests_exposure.get('exposure_notes')
        
        # 5. Update KCSE summary if available
        kcse_summary = kcse_data.get('summary', {})
        if kcse_summary.get('mean_grade'):
            profile.mean_grade = kcse_summary.get('mean_grade')
        
        if kcse_summary.get('kcse_points'):
            try:
                profile.kcse_points = float(kcse_summary.get('kcse_points'))
            except (ValueError, TypeError):
                pass
        
        profile.updated_from_prompt_at = timezone.now()
        profile.save()

        # 6. Upsert Academic Results from kcse.subjects[]
        # Format: [{"name": "English", "grade": "A"}, ...]
        subjects_list = kcse_data.get('subjects', [])
        
        for item in subjects_list:
            name = item.get('name')
            grade = item.get('grade')
            
            if not name or not grade:
                continue

            # Subject Resolution - try to find by name
            subject = Subject.objects.filter(name__iexact=name).first()
            
            if not subject:
                # Create Custom Subject
                import uuid
                generated_code = f"CUST-{str(uuid.uuid4())[:8].upper()}"
                subject = Subject.objects.create(
                    name=name, 
                    code=generated_code,
                    category='GPX' # Custom/Other
                )

            # Upsert Result
            AcademicResult.objects.update_or_create(
                student=profile,
                subject=subject,
                defaults={"grade": grade}
            )

        # 7. Replace StudentAttributes
        # Clear all existing attributes for this student
        StudentAttribute.objects.filter(student=profile).delete()
        
        attrs_to_create = []
        
        # 7.1 Strengths from personal_cognitive.strengths[]
        strengths = personal_cognitive.get('strengths', [])
        for strength in strengths:
            if strength:
                attrs_to_create.append(StudentAttribute(
                    student=profile,
                    attribute_type='STRENGTH',
                    name=strength,
                    weight=5
                ))
        
        # 7.2 Weaknesses from personal_cognitive.weaknesses[]
        weaknesses = personal_cognitive.get('weaknesses', [])
        for weakness in weaknesses:
            if weakness:
                attrs_to_create.append(StudentAttribute(
                    student=profile,
                    attribute_type='WEAKNESS',
                    name=weakness,
                    weight=5
                ))
        
        # 7.3 Technical Skills from personal_cognitive.current_skills.technical[]
        current_skills = personal_cognitive.get('current_skills', {})
        technical_skills = current_skills.get('technical', [])
        for skill in technical_skills:
            if skill:
                attrs_to_create.append(StudentAttribute(
                    student=profile,
                    attribute_type='SKILL_TECH',
                    name=skill,
                    weight=5
                ))
        
        # 7.4 Soft Skills from personal_cognitive.current_skills.soft[]
        soft_skills = current_skills.get('soft', [])
        for skill in soft_skills:
            if skill:
                attrs_to_create.append(StudentAttribute(
                    student=profile,
                    attribute_type='SKILL_SOFT',
                    name=skill,
                    weight=5
                ))
        
        # 7.5 Learning Styles from personal_cognitive.preferred_learning_styles[]
        learning_styles = personal_cognitive.get('preferred_learning_styles', [])
        for style_obj in learning_styles:
            if isinstance(style_obj, dict):
                label = style_obj.get('label') or style_obj.get('style')
                if label:
                    attrs_to_create.append(StudentAttribute(
                        student=profile,
                        attribute_type='STYLE',
                        name=label,
                        weight=5
                    ))
            elif isinstance(style_obj, str):
                attrs_to_create.append(StudentAttribute(
                    student=profile,
                    attribute_type='STYLE',
                    name=style_obj,
                    weight=5
                ))
        
        # 7.6 Interests/Hobbies from interests_exposure.interests_hobbies[]
        interests_hobbies = interests_exposure.get('interests_hobbies', [])
        for item in interests_hobbies:
            if item:
                attrs_to_create.append(StudentAttribute(
                    student=profile,
                    attribute_type='INTEREST',
                    name=item,
                    weight=5
                ))
        
        # Bulk create all attributes
        if attrs_to_create:
            StudentAttribute.objects.bulk_create(attrs_to_create)

        # 8. Replace Influences from student_profile.influences[]
        Influence.objects.filter(student=profile).delete()
        
        influences_to_create = []
        for inf in influences_list:
            if inf:
                influences_to_create.append(Influence(
                    student=profile,
                    influencer_type=inf.get('influencer_type', 'other'),
                    direction_field=inf.get('direction_field', 'General'),
                    general_path=inf.get('general_path', 'university'),
                    strength=inf.get('strength', 1),
                    reason=inf.get('reason'),
                    student_alignment=inf.get('student_alignment', 'neutral'),
                    notes=inf.get('notes', '')
                ))
        
        if influences_to_create:
            Influence.objects.bulk_create(influences_to_create)

        # 9. Replace Decision Priorities from student_profile.decision_priorities.items[]
        DecisionPriority.objects.filter(student=profile).delete()
        
        priorities_items = decision_priorities_data.get('items', [])
        priorities_to_create = []
        
        for idx, priority in enumerate(priorities_items):
            if priority and priority.get('key'):
                priorities_to_create.append(DecisionPriority(
                    student=profile,
                    key=priority.get('key'),
                    weight=priority.get('weight', 50),
                    order_index=idx
                ))
        
        if priorities_to_create:
            DecisionPriority.objects.bulk_create(priorities_to_create)

        # 10. Replace Career Aspirations from personal_cognitive.career_aspirations[]
        CareerGoal.objects.filter(student=profile).delete()
        
        career_goals_to_create = []
        if raw_career_aspirations and isinstance(raw_career_aspirations, list):
            # Trim whitespace and remove empty strings
            cleaned_aspirations = [a.strip() for a in raw_career_aspirations if a and str(a).strip()]
            # Deduplicate while preserving order
            seen = set()
            unique_aspirations = [a for a in cleaned_aspirations if not (a in seen or seen.add(a))]
            
            for aspiration in unique_aspirations:
                career_goals_to_create.append(CareerGoal(
                    student=profile,
                    title=aspiration,
                    description=None
                ))
        
        if career_goals_to_create:
            CareerGoal.objects.bulk_create(career_goals_to_create)

    return profile
