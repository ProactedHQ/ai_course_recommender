import os
import django
import sys
import json

# Setup Django Architecture
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()
settings.ALLOWED_HOSTS += ['testserver'] # Whitelist test client host

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from students.models import StudentProfile, AcademicResult, StudentAttribute, Influence, DecisionPriority, PromptSubmission

User = get_user_model()

def run_verification():
    print(">>> STARTING QA VERIFICATION FOR STUDENT PERSISTENCE")
    
    # 0. CLEANUP (Ensure fresh state)
    email = "qa_test_user@example.com"
    existing = User.objects.filter(username=email).first()
    if existing:
        print(f"> Cleaning up previous test user: {email}")
        existing.delete()

    # Clean up custom subjects from previous runs to prevent ambiguity
    from students.models import Subject
    deleted_count, _ = Subject.objects.filter(code__startswith="CUST-").delete()
    if deleted_count > 0:
        print(f"> Cleaned up {deleted_count} stale custom subjects")

    # 1. SETUP USER
    user = User.objects.create_user(username=email, email=email, password="testpass123")
    print(f"> Created Test User: {email}")

    client = APIClient()
    client.force_authenticate(user=user)

    # 2. CONSTRUCT PAYLOAD
    payload = {
        "payload": {
            "personal_cognitive": {
                "self_description": "I am a driven student interested in tech and solving problems.",
                "short_term_goals_1_3_years": ["Learn Python", "Pass KCSE with A"],
                "long_term_goals_career": "Become a Software Engineer at Google",
                "time_commitment_hours_per_week": 24,
                "financial_budget_kes": 3242342,
                "preferred_location": "Eastern",
                "constraints_notes": "Cannot travel far due to family.",
                "exposure_notes": "Visited iHub in Nairobi."
            },
            "subjects": {
                "ENG": "A", "KIS": "A-", "MAT": "A", "BIO": "A-", 
                "PHY": "B+", "CHE": "A-", "GEO": "A-", "BST": "B+" # Using BST instead of CMP just in case, or CMP if existing
            },
            "attributes": {
                "strengths": ["Analytical thinking", "Teamwork", "Resilience"],
                "weaknesses": ["Poor time management", "Lack of focus", "Stress management", "Public speaking fear"],
                "skills_tech": ["MS Word/Excel/PowerPoint", "Email writing"],
                "skills_soft": ["Communication", "Leadership"],
                "interests": ["Technology", "Health", "Construction"],
                "hobbies": ["Gaming", "Chess"],
                "learning_style": "Visual",
                "values": ["Innovation", "Integrity"]
            },
            "influences": [
                {
                    "type": "parent", "direction": "eryretretre", "path": "university", 
                    "strength": 3, "reason": "advice", "alignment": "neutral"
                }
            ],
            "priorities": [
                {"key": "salary_potential", "weight": 35},
                {"key": "passion_interest", "weight": 5},
                {"key": "job_stability", "weight": 20},
                {"key": "work_life_balance", "weight": 20},
                {"key": "social_impact", "weight": 20}
            ]
        }
    }

    # 3. TEST 1: POST /api/prompts/
    print("\n>>> TEST 1: POST /api/prompts/")
    response = client.post('/api/prompts/', payload, format='json')
    if response.status_code != 201:
        print(f"FAILED: {response.status_code} - {response.data}")
        sys.exit(1)
    print("SUCCESS: Prompt Submitted (201 Created)")

    # 4. VERIFY DB STATE
    print("\n>>> VERIFYING DB STATE...")
    
    # Profile
    profile = StudentProfile.objects.get(user=user)
    assert profile.self_description == payload['payload']['personal_cognitive']['self_description'], "Self Desc Mismatch"
    assert profile.long_term_goals == payload['payload']['personal_cognitive']['long_term_goals_career'], "Goal Mismatch"
    assert profile.time_hours_per_week == 24
    assert profile.budget_kes_estimate == 3242342
    print(f"✓ Profile Fields Verified ({profile.preferred_location})")

    # Academics
    results = AcademicResult.objects.filter(student=profile)
    print(f"✓ Academic Results Count: {results.count()} (Expected 8)")
    assert results.count() == 8

    # Attributes
    attrs = StudentAttribute.objects.filter(student=profile)
    print(f"✓ Total Attributes: {attrs.count()}")
    tech_skills = attrs.filter(attribute_type='SKILL_TECH').count()
    assert tech_skills == 2, f"Expected 2 Tech Skills, got {tech_skills}"

    # Influences
    infs = Influence.objects.filter(student=profile)
    assert infs.count() == 1
    i = infs.first()
    assert i.influencer_type == 'parent'
    print(f"✓ Influence Verified: {i}")

    # Priorities
    priorities = DecisionPriority.objects.filter(student=profile)
    assert priorities.count() == 5
    p_sal = priorities.get(key='salary_potential')
    assert p_sal.weight == 35
    print(f"✓ Priorities Verified")

    # Submission
    subs = PromptSubmission.objects.filter(user=user)
    print(f"✓ Submission History Count: {subs.count()}")


    # 5. TEST 2: REPLACE STRATEGY
    print("\n>>> TEST 2: MODIFY & REPLACE")
    # Change payload: Remove 1 subject, change strength, change priority
    payload_v2 = payload.copy()
    payload_v2['payload']['subjects'] = {"ENG": "A", "MAT": "B"} # Only 2 subjects now
    payload_v2['payload']['attributes']['strengths'] = ["Super Strength"] # Replace 3 with 1
    
    response = client.post('/api/prompts/', payload_v2, format='json')
    assert response.status_code == 201
    
    # Re-verify
    results_v2 = AcademicResult.objects.filter(student=profile)
    # NOTE: Our service UPSERTS academic results, it DOES NOT DELETE missing ones by default in the loop unless we explicitly coded that.
    # Checking implementation: "Upsert Result... for item in subject_list".
    # It does NOT delete subjects not in the list. So count should be 8 (original) + 0 new (since they overlap).
    # Wait, if I change grade MAT A -> B, it should update.
    from students.models import Subject
    print(f"DEBUG: All Subjects in DB: {[(s.name, s.code) for s in Subject.objects.all()]}")
    mat_res = results_v2.get(subject__name__iexact="Subject MAT")
    print(f"✓ Updated MAT Grade: {mat_res.grade} (Expected B)")
    assert mat_res.grade == "B"
    
    # Attributes SHOULD be replaced (delete all -> create new)
    strengths_v2 = StudentAttribute.objects.filter(student=profile, attribute_type='STRENGTH')
    print(f"✓ Updated Strengths Count: {strengths_v2.count()} (Expected 1)")
    assert strengths_v2.count() == 1
    assert strengths_v2.first().name == "Super Strength"

    # 6. TEST 3: FULL PROFILE ENDPOINT
    print("\n>>> TEST 3: GET /api/profile/")
    resp_prof = client.get('/api/profile/')
    assert resp_prof.status_code == 200
    data = resp_prof.json()
    
    assert 'profile' in data
    assert 'academic_results' in data
    assert 'attributes' in data
    assert 'influences' in data
    
    print("✓ Full Profile Structure Verified")
    # print(json.dumps(data, indent=2))

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY")

if __name__ == "__main__":
    run_verification()
