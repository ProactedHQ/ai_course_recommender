"""
=======================================================================
 KeDira — AI Prompt & Tier Limits Test Suite
=======================================================================
 Covers:
   ✔ Prompt usage incrementing
   ✔ TIER_LIMITS enforcement (Atomic checked)
   ✔ 403 Forbidden when limit reached
   ✔ Monthly usage reset logic

 Run these tests with:
   python manage.py test apps.students.tests.test_prompts -v 2
=======================================================================
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

User = get_user_model()

def section(title):
    print(f"\n{'─' * 60}")
    print(f"  🤖  PROMPTS │ {title}")
    print(f"{'─' * 60}")

def ok(msg):  print(f"    ✅  {msg}")
def fail(msg): print(f"    ❌  {msg}")
def info(msg): print(f"    ℹ️   {msg}")


class PromptUsageTests(TestCase):
    """Tests for subscription-based usage limits on AI prompts."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='usage_test_user',
            email='usage@kedira.ac.ke',
            password='testpass123',
            is_student=True,
            subscription_tier='explorer' # Default limit is usually 5
        )
        self.client.force_authenticate(user=self.user)
        # We don't mock 'create' globally anymore, as we want to test its internal usage enforcement logic.
        # Instead, we mock the heavy components inside it during tests.

    # The recommendation pipeline with every heavy step mocked out:
    # one eligible programme (code 1234567) and an LLM that recommends it.
    SHORTLIST = [{
        'course': 'Bachelor of Science (Computer Science)', 'university': 'University of Nairobi',
        'public_private': 'PUBLIC_UNIVERSITY', 'level': 'DEGREE', 'cluster': 'Engineering',
        'location': 'Nairobi', 'latest_cutoff': 40.1, 'latest_year': 2024,
        'prev_cutoff': 39.5, 'prev_year': 2023, 'student_cluster_points': 42.0,
        'programme_code': '1234567',
    }]

    def _llm_result(self, code='1234567'):
        return {
            'recommendations': [{
                'rank': 1, 'course': 'Made-up name', 'university': 'University of Nairobi',
                'latest_cutoff': 99.9, 'programme_code': code, 'insight': 'Fits your maths strength.',
            }],
            'premium_details': [],
        }

    def _post_with_pipeline_mocked(self, eligible=True, llm_result=None, submission_id=101):
        payload = {"payload": {"student_profile": {}}}
        with patch('apps.students.views.WizardPayloadSerializer') as mock_wizard, \
             patch('apps.students.views.PromptSubmissionViewSet.get_serializer') as mock_ser, \
             patch('apps.students.views._extract_student_grades', return_value={'121': 'A', 'MEAN': 'A'}), \
             patch('apps.students.views.get_eligible_programmes', return_value=[{}] if eligible else []), \
             patch('apps.students.views.filter_eligible_only', side_effect=lambda progs: progs), \
             patch('apps.students.views._serialize_programmes_for_llm', return_value=self.SHORTLIST), \
             patch('apps.students.views._build_user_profile_for_llm', return_value={}), \
             patch('apps.students.views._build_cluster_summary', return_value=[]), \
             patch('apps.students.views.persist_student_profile_from_wizard'), \
             patch('apps.students.views.run_recommendation_graph',
                   return_value=llm_result if llm_result is not None else self._llm_result()):
            mock_wizard.return_value.is_valid.return_value = True
            mock_wizard.return_value.validated_data = {}
            mock_ser.return_value.is_valid.return_value = True
            mock_ser.return_value.save.return_value = MagicMock(id=submission_id)
            return self.client.post('/api/prompts/', payload, format='json')

    # ── 1. Usage Tracking ─────────────────────────────────────────────
    def test_prompt_usage_increments(self):
        section("Usage counter increments after successful submission")

        initial_usage = self.user.prompts_used_in_period
        response = self._post_with_pipeline_mocked()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.prompts_used_in_period, initial_usage + 1)
        ok(f"Usage: {initial_usage} → {self.user.prompts_used_in_period} ✔")

    def test_failed_submission_refunds_prompt(self):
        section("No eligible programmes → 422 and prompt refunded")

        response = self._post_with_pipeline_mocked(eligible=False)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error'], 'NO_ELIGIBLE_PROGRAMMES')
        self.user.refresh_from_db()
        self.assertEqual(self.user.prompts_used_in_period, 0)
        ok("Student keeps their prompt ✔")

    def test_llm_facts_are_replaced_with_db_values(self):
        section("LLM course/cutoff text is overwritten by DB values")

        response = self._post_with_pipeline_mocked()

        rec = response.data['recommendations']['top_5'][0]
        self.assertEqual(rec['course'], 'Bachelor of Science (Computer Science)')
        self.assertEqual(rec['cutoff_points'], 40.1)
        self.assertEqual(rec['insight'], 'Fits your maths strength.')
        ok("Grounded in shortlist ✔")

    def test_invented_programme_is_dropped(self):
        section("LLM-invented programme code → ADVISOR_FAILURE and refund")

        response = self._post_with_pipeline_mocked(llm_result=self._llm_result(code='0000000'))

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'ADVISOR_FAILURE')
        self.user.refresh_from_db()
        self.assertEqual(self.user.prompts_used_in_period, 0)
        ok("Nothing invented reaches the student ✔")

    # ── 2. Limit Enforcement ──────────────────────────────────────────
    def test_explorer_limit_reached(self):
        section("Explorer tier (limit reached) → 403 Forbidden")
        
        # Explorer limit is 1
        self.user.prompts_used_in_period = 1 
        self.user.save()
        
        data = {"payload": {"step1": {"mean_grade": "A"}}}
        response = self.client.post('/api/prompts/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "PROMPT_LIMIT_REACHED")
        
        ok("Explorer correctly rejected at 1 prompt ✔")

    # ── 3. Higher Tiers have higher limits ──────────────────────────
    def test_mentor_elite_handles_more_prompts(self):
        section("High tier (Mentor Elite) allowed more prompts")

        self.user.subscription_tier = 'mentor_elite'
        self.user.prompts_used_in_period = 4 # Limit is 5
        self.user.save()

        response = self._post_with_pipeline_mocked(submission_id=202)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ok("Mentor Elite allowed at 4 prompts (limit is 5) ✔")

    def test_scholar_vvip_is_unlimited(self):
        section("Scholar VVIP is unlimited")

        self.user.subscription_tier = 'scholar_vvip'
        self.user.prompts_used_in_period = 100 # Way beyond others
        self.user.save()

        response = self._post_with_pipeline_mocked(submission_id=303)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ok("Scholar VVIP allowed even at 100 prompts ✔")


    # ── 4. Usage Reset Logic ───────────────────────────────────────────
    def test_usage_reset_at_start_of_month(self):
        section("Usage resets when period start date is in the past month")
        
        from apps.users.services.subscription import sync_subscription_period
        
        # Simulate last month's data
        last_month = timezone.now().date().replace(day=1) - timedelta(days=5)
        self.user.prompt_period_start = last_month
        self.user.prompts_used_in_period = 50
        self.user.save()
        
        # Sync should reset it
        synced_user = sync_subscription_period(self.user)
        
        self.assertEqual(synced_user.prompts_used_in_period, 0)
        self.assertEqual(synced_user.prompt_period_start, timezone.now().date().replace(day=1))
        
        ok("Usage reset to 0 for new month ✔")
        ok(f"New period start: {synced_user.prompt_period_start} ✔")
