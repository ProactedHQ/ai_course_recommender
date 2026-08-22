#!/usr/bin/env python
import os
import sys
import json

import django


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
    django.setup()

    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    User = get_user_model()

    username = "wizard_tester"
    email = "[REDACTED_EMAIL]"
    password = "[REDACTED_CREDENTIAL]"

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_student": True,
        },
    )
    if created:
        user.set_password(password)
        user.save()

    client = APIClient(SERVER_NAME='localhost')
    client.force_authenticate(user=user)

    payload = {
        "version": "test-1",
        "student_profile": {
            "kcse": {
                "subjects": [
                    {"name": "English", "grade": "B+"},
                    {"name": "Kiswahili", "grade": "C+"},
                    {"name": "Mathematics Alternative A", "grade": "A-"},
                    {"name": "Biology", "grade": "A"},
                    {"name": "Chemistry", "grade": "B+"},
                    {"name": "Physics", "grade": "B"},
                    {"name": "Geography", "grade": "C+"},
                    {"name": "Business Studies", "grade": "B-"},
                ],
                "custom_subjects": [],
                "summary": {
                    "mean_grade": "B+",
                    "total_subjects": 8,
                },
            },
            "personal_cognitive": {
                "self_description": "I enjoy math, coding and solving analytical problems.",
                "strengths": ["Analytical", "Persistent"],
                "weaknesses": ["Procrastination"],
                "short_term_goals_1_3_years": [
                    "Join a strong CS or data-related programme"
                ],
                "long_term_goals_career": "Become a data scientist or AI engineer working in Africa.",
                "current_skills": {
                    "Programming": ["Python", "basic web"],
                    "Data": ["Spreadsheets", "simple statistics"],
                },
                "preferred_learning_styles": ["visual", "project-based"],
                "career_aspirations": ["Technology leadership", "AI for social impact"],
            },
            "practical_factors": {
                "time_hours_per_week": 35,
                "budget_kes_estimate": 250000,
                "preferred_location": "Nairobi",
                "constraints_notes": "Prefer public universities due to cost.",
            },
            "interests_exposure": {
                "interests_hobbies": [
                    "Programming",
                    "Machine learning",
                    "Gaming",
                    "Robotics club",
                ],
                "extracurriculars": ["Science club", "Math contest"],
                "exposure_notes": "Attended coding bootcamps and tech fairs.",
            },
            "influences": [
                {
                    "type": "parent",
                    "direction": "supportive",
                    "path": "STEM",
                    "strength": 4,
                    "reason": "Parents work in engineering and IT.",
                    "alignment": "high",
                }
            ],
            "decision_priorities": {
                "mode": "weights",
                "items": [
                    {"key": "passion", "label": "Passion & interest alignment", "weight": 35},
                    {"key": "job_market", "label": "Job market demand", "weight": 25},
                    {"key": "fees", "label": "Affordability", "weight": 20},
                    {"key": "location", "label": "Location", "weight": 10},
                    {"key": "prestige", "label": "Institution prestige", "weight": 10},
                ],
                "total_weight": 100,
            },
        },
        "client_meta": {
            "source": "script_test",
        },
    }

    body = {
        "payload": payload,
    }

    print("POST /api/prompts/ with test wizard payload")
    resp = client.post("/api/prompts/", data=json.dumps(body), content_type="application/json")

    print("Status:", resp.status_code)
    try:
        print("Response JSON:")
        print(json.dumps(resp.json(), indent=2, default=str))
    except Exception:
        print("Raw content:")
        print(resp.content)


if __name__ == "__main__":
    main()
