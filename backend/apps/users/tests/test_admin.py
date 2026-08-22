"""
=======================================================================
 KeDira — Admin Management & Analytics Test Suite
=======================================================================
 Covers:
   ✔ GET /api/admin/analytics → BUG 3 & 4 Fix Validation
   ✔ GET /api/admin/users → Validates Serializer (BUG 5)
   ✔ PATCH /api/admin/users/<pk> → Validates URL + PATCH Fix (BUG 6 & 7)
   ✔ Permissions → Only Staff/Admins allowed

 Run these tests with:
   python manage.py test apps.users.tests.test_admin -v 2
=======================================================================
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def section(title):
    print(f"\n{'─' * 60}")
    print(f"  👑  ADMIN │ {title}")
    print(f"{'─' * 60}")

def ok(msg):  print(f"    ✅  {msg}")
def fail(msg): print(f"    ❌  {msg}")
def info(msg): print(f"    ℹ️   {msg}")


class AdminInterfaceTests(TestCase):
    """Tests for administrative tools and metrics."""

    def setUp(self):
        self.client = APIClient()
        # Create an admin user (staff = True, student = False)
        self.admin = User.objects.create_user(
            username='admin_boss',
            email='admin@kedira.ac.ke',
            password='testpass888',
            is_staff=True,
            is_student=False,
            subscription_tier='scholar_vvip'
        )
        # Create some test data for metrics
        User.objects.create_user(username='u1', subscription_tier='mentor_elite', is_student=True)
        User.objects.create_user(username='u2', subscription_tier='scholar_vvip', is_student=True)
        User.objects.create_user(username='u3', subscription_tier='explorer', is_student=True)
        
        self.client.force_authenticate(user=self.admin)

    # ── 1. Analytics BUG 3 & 4 Validation ─────────────────────────────
    def test_analytics_calculated_correctly(self):
        section("Analytics Endpoint (BUG 3 & 4 Fix Check)")
        
        response = self.client.get('/api/admin/analytics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        info(f"Summary metrics: {data}")

        # BUG 3: conversionRate should exist and be defined
        self.assertIn('conversionRate', data)
        # BUG 4: Counts based on subscription_tier
        self.assertEqual(data['standardUsers'], 1) # mentor_elite (u1)
        self.assertEqual(data['premiumUsers'], 2)  # scholar_vvip (admin + u2)
        self.assertEqual(data['freeUsers'], 1)     # explorer (u3)
        
        ok("conversionRate is defined (BUG 3 Fix Verified)")
        ok("Subscription counts use 'subscription_tier' field (BUG 4 Fix Verified)")

    # ── 2. User Management Serializer (BUG 5) ────────────────────────
    def test_user_list_uses_valid_fields(self):
        section("User List Serializer (BUG 5 Fix Check)")
        
        response = self.client.get('/api/admin/users')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Response should contain user objects with correct fields
        user_data = response.data[0]
        self.assertIn('username', user_data)
        self.assertIn('first_name', user_data)
        self.assertIn('subscription_tier', user_data)
        
        # BUG 5: Ensure 'name' or 'full_name' are NOT causing key errors or present if invalid
        self.assertNotIn('full_name', user_data) 
        
        ok("Serializer uses valid AbstractUser fields (BUG 5 Fix Verified)")

    # ── 3. User Detail PATCH (BUG 6 & 7) ────────────────────────────
    def test_user_update_with_integer_pk(self):
        section("User Patch Endpoint (BUG 6 & 7 Fix Check)")
        
        target_user = User.objects.get(username='u3')
        original_tier = target_user.subscription_tier
        
        data = {"subscription_tier": "scholar_vvip"}
        
        # BUG 6: Verify <int:pk> works (URL was <uuid:pk> before fix)
        url = f'/api/admin/users/{target_user.id}'
        info(f"PATCHing to: {url}")
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        target_user.refresh_from_db()
        self.assertEqual(target_user.subscription_tier, 'scholar_vvip')
        
        ok("Integer PK route matched correctly (BUG 6 Fix Verified)")
        ok("Admin PATCH successful (BUG 7 Fix Verified)")

    # ── 4. Permissions ────────────────────────────────────────────────
    def test_student_cannot_access_admin_api(self):
        section("Security: Student rejected from Admin APIs")
        
        student = User.objects.get(username='u1')
        self.client.force_authenticate(user=student)
        
        response = self.client.get('/api/admin/analytics')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        ok("Student correctly forbidden from admin analytics ✔")
