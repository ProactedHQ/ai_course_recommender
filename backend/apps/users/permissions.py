"""
Custom permission classes for role-based access control.

Usage:
    from apps.users.permissions import IsStaffNonStudent

    class MyAdminView(APIView):
        permission_classes = [IsStaffNonStudent]
"""
from rest_framework import permissions


class IsStaffNonStudent(permissions.BasePermission):
    """
    Admin/API access: staff users who are NOT students.
    Superusers pass automatically because is_staff=True is required for superuser.
    
    Denies:
      - Unauthenticated requests
      - Students (is_student=True)
      - Non-staff users (is_staff=False)
    """

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and u.is_staff
            and not getattr(u, "is_student", False)
        )
