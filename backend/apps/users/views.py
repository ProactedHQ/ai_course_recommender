from django.db import transaction
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import CustomUser
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    RegisterSerializer, 
)
from .services.subscription import sync_subscription_period, get_remaining_prompts
from utils.rate_limit import rate_limit
import logging

logger = logging.getLogger('apps')

# ============================================================================
# AUTH: /api/auth/me/ — Backend-verified role endpoint (source of truth)
# ============================================================================

@extend_schema(
    summary="Get or update authenticated user role (source of truth)",
    description=(
        "GET: Returns the authenticated user's role flags directly from the Django database.\n"
        "PUT: Updates the authenticated user's profile (first_name, last_name, bio)."
    ),
    responses={
        200: UserSerializer,
        401: {"type": "object", "properties": {"detail": {"type": "string"}}}
    }
)
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Returns or updates the authenticated user's profile and role details.
    """
    u = request.user
    logger.info(f"[AUTH_ME] Request Method: {request.method} User: {u.email}")
    
    if request.method == "PUT":
        logger.info(f"[AUTH_ME] PUT Data: {request.data}")
        # 1. Update User (Phone Number)
        user_serializer = UserUpdateSerializer(u, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Update Student Bio (self_description)
        bio = request.data.get('bio')
        if bio is not None and u.is_student:
            from apps.students.models import StudentProfile
            profile, _ = StudentProfile.objects.get_or_create(user=u)
            if len(bio) > 500:
                 return Response({"bio": "Bio must be a maximum of 500 characters."}, status=status.HTTP_400_BAD_REQUEST)
            profile.self_description = bio
            profile.save()

    # 1. Sync period lazily (resets usage if month changed)
    u = sync_subscription_period(u)
    
    # 2. Get computed stats
    remaining = get_remaining_prompts(u)
    
    # 3. Get Student Profile Bio
    bio = ""
    if u.is_student:
        try:
            bio = u.student_profile.self_description or ""
        except:
            pass

    return Response({
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "phone_number": u.phone_number,
        "bio": bio,
        "is_student": u.is_student,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
        "is_institution_admin": getattr(u, "is_institution_admin", False),
        
        # Subscription Data
        "subscription_tier": u.subscription_tier,
        "prompts_used_in_period": u.prompts_used_in_period,
        "prompt_period_start": u.prompt_period_start,
        "prompts_remaining": remaining,
        "DEBUG_VERSION": "2026-03-04-V2"
    })


# ============================================================================
# AUTH: Registration
# ============================================================================

@extend_schema(
    summary="Register a new user",
    description="Creates a new CustomUser instance. Note: Currently mostly handled via Supabase in frontend.",
    request=RegisterSerializer,
    responses={201: RegisterSerializer}
)
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,) # Allow anyone to sign up
    serializer_class = RegisterSerializer

    @rate_limit(key_prefix='auth_register', rate='5/m', methods=['POST'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

@extend_schema(
    summary="Get authenticated user profile",
    description="Returns basic profile information for the currently logged-in user (authenticated via Supabase JWT).",
    responses={
        200: {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "is_student": {"type": "boolean"},
            }
        },
        401: {"type": "object", "properties": {"detail": {"type": "string"}}}
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@rate_limit(key_prefix='auth_profile', rate='60/m', methods=['GET'])
def profile(request):
    user = request.user
    return Response({
        "id": str(getattr(user, "id", "")),
        "username": getattr(user, "username", ""),
        "email": getattr(user, "email", ""),
        "is_student": getattr(user, "is_student", False),
    })
