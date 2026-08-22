from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from apps.users.models import CustomUser, SubscriptionTransaction
from apps.users.services.subscription import sync_subscription_period, get_remaining_prompts
from apps.students.models import PromptSubmission

class SubscriptionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_reset_logic(self):
        # Set period to last month
        today = date.today()
        last_month_end = today.replace(day=1) - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        self.user.prompt_period_start = last_month_start
        self.user.prompts_used_in_period = 5
        self.user.save()
        
        # Sync
        u = sync_subscription_period(self.user)
        
        # Should be reset to this month
        self.assertEqual(u.prompt_period_start, today.replace(day=1))
        self.assertEqual(u.prompts_used_in_period, 0)

    def test_remaining_prompts(self):
        self.user.subscription_tier = 'explorer'
        self.user.prompts_used_in_period = 0
        self.assertEqual(get_remaining_prompts(self.user), 1)
        
        self.user.subscription_tier = 'mentor_elite'
        self.assertEqual(get_remaining_prompts(self.user), 5)
        
        self.user.subscription_tier = 'scholar_vvip'
        self.assertIsNone(get_remaining_prompts(self.user))

    def test_upgrade_flow(self):
        # 1. Initiate
        url_upgrade = reverse('subscription_upgrade')
        response = self.client.post(url_upgrade, {'target_tier': 'mentor_elite'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        txn_id = response.data['id']
        
        # 2. Confirm
        url_confirm = reverse('subscription_confirm')
        response = self.client.post(url_confirm, {'transaction_id': txn_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Verify user tier
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_tier, 'mentor_elite')

    def test_prompt_enforcement(self):
        # Explorer limit is 1
        self.user.subscription_tier = 'explorer'
        self.user.prompts_used_in_period = 1
        self.user.save()
        
        url = reverse('promptsubmission-list')
        payload = {
            "version": "test",
            "student_profile": {"kcse": {"subjects": []}},
            "client_meta": {"device": "test"}
        }
        
        response = self.client.post(url, payload, format='json')
        
        # Should be blocked
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'PROMPT_LIMIT_REACHED')
