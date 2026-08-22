"""
=======================================================================
 KeDira — Authentication Test Suite
=======================================================================
 Covers:
   ✔ /api/auth/me/        → Role endpoint (source of truth for RBAC)
   ✔ Role invariants      → student/staff/superuser constraints
   ✔ Subscription fields  → tier, prompts_used, period synced in /me/
   ✔ Unauthenticated access is rejected on protected endpoints

 Run these tests with:
   python manage.py test apps.users.tests.test_auth -v 2
=======================================================================
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# ──────────────────────────────────────────────────────────────────────
#  Helper: clear log separator for terminal readability
# ──────────────────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'─' * 60}")
    print(f"  🔐  AUTH │ {title}")
    print(f"{'─' * 60}")


def ok(msg):  print(f"    ✅  {msg}")
def fail(msg): print(f"    ❌  {msg}")
def info(msg): print(f"    ℹ️   {msg}")


# ──────────────────────────────────────────────────────────────────────
#  /api/auth/me/  ─  Role Endpoint Tests
# ──────────────────────────────────────────────────────────────────────
class MeEndpointTests(TestCase):
    """Tests for GET /api/auth/me/ — the RBAC source of truth."""

    def setUp(self):
        self.client = APIClient()

    # ── 1. Unauthenticated ──────────────────────────────────────────
    def test_me_rejects_unauthenticated(self):
        section("Unauthenticated request → 403")
        response = self.client.get('/api/auth/me/')
        # Supabase middleware/DRF mix returns 403 for forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        ok("Unauthenticated /api/auth/me/ correctly returns 403")

    # ── 2. Student user ─────────────────────────────────────────────
    def test_me_returns_correct_fields_for_student(self):
        section("Student user → correct role flags returned")
        user = User.objects.create_user(
            username='student_user',
            email='student@kedira.ac.ke',
            password='securepass123',
            is_student=True,
            is_staff=False,
        )
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        info(f"Response: {dict(data)}")

        self.assertEqual(data['email'], 'student@kedira.ac.ke')
        self.assertTrue(data['is_student'], "Expected is_student=True")
        self.assertFalse(data['is_staff'], "Expected is_staff=False")
        self.assertIn('subscription_tier', data)
        self.assertIn('prompts_remaining', data)
        self.assertIn('prompts_used_in_period', data)

        ok(f"Student /me/ returns all expected fields")
        ok(f"Subscription tier: '{data['subscription_tier']}'")
        ok(f"Prompts remaining: {data['prompts_remaining']}")

    # ── 3. Admin (staff) user ───────────────────────────────────────
    def test_me_returns_correct_flags_for_admin(self):
        section("Admin user → is_staff=True, is_student=False")
        admin = User.objects.create_user(
            username='admin_user',
            email='admin@kedira.ac.ke',
            password='adminpass123',
            is_staff=True,
            is_student=False,
        )
        self.client.force_authenticate(user=admin)
        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertTrue(data['is_staff'])
        self.assertFalse(data['is_student'])

        ok("Admin /me/ correctly reports is_staff=True, is_student=False")

    # ── 4. Subscription fields in /me/ ──────────────────────────────
    def test_me_includes_subscription_data(self):
        section("Subscription tier data is included in /me/ response")
        user = User.objects.create_user(
            username='explorer_user',
            email='explorer@kedira.ac.ke',
            password='test123',
            is_student=True,
            subscription_tier='explorer',
        )
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/auth/me/')
        data = response.data

        self.assertEqual(data['subscription_tier'], 'explorer')
        self.assertIsNotNone(data.get('prompt_period_start'))

        ok(f"Subscription tier: {data['subscription_tier']}")
        ok(f"Period start: {data['prompt_period_start']}")
        ok("/me/ correctly exposes subscription info for frontend")


# ──────────────────────────────────────────────────────────────────────
#  Role Invariant Tests (CustomUser model)
# ──────────────────────────────────────────────────────────────────────
class RoleInvariantTests(TestCase):
    """Tests that invalid role combinations are rejected at the model level."""

    def test_student_cannot_be_staff(self):
        section("Role invariant: student + staff → ValidationError")
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            user = User(
                username='bad_user',
                email='bad@kedira.ac.ke',
                is_student=True,
                is_staff=True,
            )
            user.set_password('pass')
            user.full_clean()
        ok("Model rejects is_student=True AND is_staff=True ✔")

    def test_superuser_must_be_staff(self):
        section("Role invariant: superuser without staff → ValidationError")
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            user = User(
                username='bad_super',
                email='badsuper@kedira.ac.ke',
                is_superuser=True,
                is_staff=False,
            )
            user.set_password('pass')
            user.full_clean()
        ok("Model rejects is_superuser=True AND is_staff=False ✔")

    def test_valid_student_user_passes(self):
        section("Valid student user → saves without error")
        user = User(
            username='good_student',
            email='good@kedira.ac.ke',
            is_student=True,
            is_staff=False,
        )
        user.set_password('pass')
        user.full_clean()  # Should NOT raise
        user.save()
        ok("Valid student (is_student=True, is_staff=False) saved successfully")

    def test_valid_admin_user_passes(self):
        section("Valid admin user → saves without error")
        user = User(
            username='good_admin',
            email='goodadmin@kedira.ac.ke',
            is_student=False,
            is_staff=True,
        )
        user.set_password('pass')
        user.full_clean()
        user.save()
        ok("Valid admin (is_student=False, is_staff=True) saved successfully")

    def test_default_subscription_tier_is_explorer(self):
        section("New user gets 'explorer' tier by default")
        user = User.objects.create_user(
            username='fresh_user',
            email='fresh@kedira.ac.ke',
            password='password123',
            is_student=True,
        )
        self.assertEqual(user.subscription_tier, 'explorer')
        self.assertEqual(user.prompts_used_in_period, 0)
        ok(f"Default tier: '{user.subscription_tier}' ✔")
        ok(f"Default prompts_used: {user.prompts_used_in_period} ✔")
