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

    @patch('apps.students.views.WizardPayloadSerializer')
    @patch('apps.students.views.PromptSubmissionViewSet.get_serializer')
    @patch('apps.students.views.async_to_sync', side_effect=lambda x: x)
    @patch('channels.layers.get_channel_layer')
    def test_prompt_usage_increments(self, mock_get_channel, mock_async, mock_ser, mock_wizard):
        section("Usage counter increments after successful submission")
        
        # Setup mocks to let create() succeed
        mock_get_channel.return_value = MagicMock()
        mock_wizard.return_value.is_valid.return_value = True
        mock_ser.return_value.is_valid.return_value = True
        mock_ser.return_value.save.return_value = MagicMock(id=101)
        
        # Payload must match WizardPayloadSerializer structure
        data = {
            "payload": {
                "student_profile": {
                    "kcse": {"subjects": []},
                    "personal_cognitive": {},
                    "practical_factors": {},
                    "interests_exposure": {},
                    "decision_priorities": {"items": []}
                }
            }
        }
        
        initial_usage = self.user.prompts_used_in_period
        response = self.client.post('/api/prompts/', data, format='json')
        
        # We need to refresh from DB
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.prompts_used_in_period, initial_usage + 1)
        ok(f"Usage: {initial_usage} → {self.user.prompts_used_in_period} ✔")

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
        
        # Using a minimal mock to avoid full AI call
        with patch('apps.students.views.WizardPayloadSerializer') as mock_wizard:
            with patch('apps.students.views.PromptSubmissionViewSet.get_serializer') as mock_ser:
                with patch('apps.students.views.async_to_sync', side_effect=lambda x: x):
                    with patch('channels.layers.get_channel_layer'):
                        mock_wizard.return_value.is_valid.return_value = True
                        mock_ser.return_value.is_valid.return_value = True
                        mock_ser.return_value.save.return_value = MagicMock(id=202)
                        
                        # Valid payload
                        payload = {
                            "payload": {
                                "student_profile": {
                                    "kcse": {"subjects": []},
                                    "personal_cognitive": {},
                                    "practical_factors": {},
                                    "interests_exposure": {},
                                    "decision_priorities": {"items": []}
                                }
                            }
                        }
                        response = self.client.post('/api/prompts/', payload, format='json')
                        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
        ok("Mentor Elite allowed at 4 prompts (limit is 5) ✔")

    def test_scholar_vvip_is_unlimited(self):
        section("Scholar VVIP is unlimited")
        
        self.user.subscription_tier = 'scholar_vvip'
        self.user.prompts_used_in_period = 100 # Way beyond others
        self.user.save()
        
        with patch('apps.students.views.WizardPayloadSerializer') as mock_wizard:
            with patch('apps.students.views.PromptSubmissionViewSet.get_serializer') as mock_ser:
                with patch('apps.students.views.async_to_sync', side_effect=lambda x: x):
                    with patch('channels.layers.get_channel_layer'):
                        mock_wizard.return_value.is_valid.return_value = True
                        mock_ser.return_value.is_valid.return_value = True
                        mock_ser.return_value.save.return_value = MagicMock(id=303)
                        
                        payload = {
                            "payload": {
                                "student_profile": {
                                    "kcse": {"subjects": []},
                                    "personal_cognitive": {},
                                    "practical_factors": {},
                                    "interests_exposure": {},
                                    "decision_priorities": {"items": []}
                                }
                            }
                        }
                        response = self.client.post('/api/prompts/', payload, format='json')
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
