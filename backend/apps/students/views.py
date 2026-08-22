from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, response, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiExample
import json
import os
import sys
import time
import logging

# Recommendation Engine Imports
from apps.users.models import CustomUser
from apps.users.services.subscription import sync_subscription_period, get_remaining_prompts
from apps.students.services.profile_persistence import persist_student_profile_from_wizard
from .models import StudentProfile, Subject, AcademicResult, PromptSubmission
from .serializers import StudentProfileSerializer, SubjectSerializer, AcademicResultSerializer, PromptSubmissionSerializer
from .serializers_wizard import WizardPayloadSerializer
from .eligibility_engine import (
    _extract_student_grades,
    get_eligible_programmes,
    filter_eligible_only,
    _serialize_programmes_for_llm,
    _build_user_profile_for_llm,
    _build_cluster_summary,
    _build_top_recommendations_from_llm,
    _fallback_top_recommendations
)
from apps.proacted_recommender_engine.langgraph_workflow import run_recommendation_graph
from utils.rate_limit import rate_limit
from utils.cache_utils import get_subject_cache_key

# Optional WebSocket support
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False

logger = logging.getLogger(__name__)

@extend_schema(tags=['Students'])
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists all available KCSE subjects (Math, Eng, etc.)
    WITH CACHING - subjects rarely change
    """
    queryset = Subject.objects.all()  # Required for router registration
    serializer_class = SubjectSerializer
    pagination_class = None  # Show all subjects at once

    def get_queryset(self):
        return Subject.objects.all()

    @rate_limit(key_prefix='subjects', rate='60/m', methods=['GET'])
    def list(self, request, *args, **kwargs):
        # Try to get from cache first
        cache_key = get_subject_cache_key()
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return response.Response(cached_data)
        
        # Cache miss - fetch from database
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Store in cache
        cache_ttl = settings.CACHE_TTL.get('SUBJECTS', 60 * 60 * 24)
        cache.set(cache_key, serializer.data, cache_ttl)
        
        return response.Response(serializer.data)

@extend_schema(tags=['Students'])
class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    Allows students to create/view/update their OWN profile.
    """
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated] # Must be logged in
    queryset = StudentProfile.objects.all()

    def get_queryset(self):
        # Only return the profile of the logged-in user
        return StudentProfile.objects.filter(user=self.request.user)

    @rate_limit(key_prefix='profile_write', rate='10/m', methods=['POST', 'PUT', 'PATCH'])
    def perform_create(self, serializer):
        # Automatically assign the logged-in user when creating a profile
        serializer.save(user=self.request.user)

    @rate_limit(key_prefix='profile_write', rate='10/m', methods=['POST', 'PUT', 'PATCH'])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @rate_limit(key_prefix='profile_write', rate='10/m', methods=['POST', 'PUT', 'PATCH'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def full(self, request):
        """
        Returns the full student profile tree for wizard prefilling.
        GET /api/students/profile/full/ (or mapped via router)
        """
        user = request.user
        try:
            profile = user.student_profile
        except StudentProfile.DoesNotExist:
            return response.Response({"detail": "Profile not found"}, status=404)
        
        # Serialize Profile
        profile_data = StudentProfileSerializer(profile).data
        
        # Academic Results
        results = profile.academic_results.select_related('subject').all()
        results_data = []
        for r in results:
            results_data.append({
                "code": r.subject.code,
                "name": r.subject.name,
                "grade": r.grade,
                "points": r.points
            })

        # Attributes Grouped
        attributes = profile.attributes.all()
        grouped_attrs = {
            "skills_tech": [], "skills_soft": [], "strengths": [], 
            "weaknesses": [], "interests": [], "hobbies": [], 
            "values": [], "learning_styles": [] 
        }
        type_map = {
            'SKILL_TECH': 'skills_tech', 'SKILL_SOFT': 'skills_soft',
            'STRENGTH': 'strengths', 'WEAKNESS': 'weaknesses',
            'INTEREST': 'interests', 'HOBBY': 'hobbies',
            'VALUE': 'values', 'STYLE': 'learning_styles'
        }
        for attr in attributes:
            key = type_map.get(attr.attribute_type)
            if key:
                grouped_attrs[key].append(attr.name)

        # Influences
        influences_data = list(profile.influences.values())
        
        # Priorities
        priorities_data = list(profile.decision_priorities.values())

        # Career Goals
        goals = profile.career_goals.all()
        goals_data = [{"title": g.title, "description": g.description} for g in goals]
        
        return response.Response({
            "profile": profile_data,
            "academic_results": results_data,
            "attributes": grouped_attrs,
            "influences": influences_data,
            "decision_priorities": priorities_data,
            "career_goals": goals_data
        })

@extend_schema(tags=['Students'])
class AcademicResultViewSet(viewsets.ModelViewSet):
    """
    Allows adding/updating grades.
    """
    serializer_class = AcademicResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AcademicResult.objects.all()

    def get_queryset(self):
        return AcademicResult.objects.filter(student__user=self.request.user)

    @rate_limit(key_prefix='academic_result_write', rate='10/m', methods=['POST', 'PUT', 'PATCH'])
    def perform_create(self, serializer):
        # Ensure the grade is attached to the correct student profile
        student_profile = self.request.user.student_profile
        serializer.save(student=student_profile)

    @rate_limit(key_prefix='academic_result_write', rate='10/m', methods=['POST', 'PUT', 'PATCH'])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @rate_limit(key_prefix='academic_result_write', rate='10/m', methods=['POST', 'PUT', 'PATCH'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

@extend_schema(
    tags=['AI Recommendations'],
    summary="Submit Wizard data and get recommendations",
    description="Handles the submission of the multi-step prompt wizard. Currently returns dummy recommendations for UI testing.",
    examples=[
        OpenApiExample(
            'Wizard Submission Example',
            summary='Standard payload from frontend wizard',
            value={
                "payload": {
                    "step1": {"mean_grade": "B+", "kcse_points": 65},
                    "step2": {"subjects": {"MAT": "A", "ENG": "B+", "CHE": "B"}},
                    "step3": {"interests": ["Artificial Intelligence", "Software Engineering"], "hobbies": ["Chess", "Gaming"]},
                    "step4": {"personal_statement": "I want to be a tech leader in Africa."}
                }
            },
            request_only=True,
        ),
        OpenApiExample(
            'Recommendation Response Example',
            summary='Format of returned recommendations',
            value={
                "received": True,
                "submission_id": 42,
                "recommendations": {
                    "top_5": [
                        {"course": "BSc Computer Science", "reason": "Math + tech interest alignment", "score": 0.86},
                        {"course": "BSc Data Science", "reason": "Analytical strengths match", "score": 0.82}
                    ]
                }
            },
            response_only=True,
        ),
    ]
)
class PromptSubmissionViewSet(viewsets.ModelViewSet):
    """
    Handles prompt submissions and history.
    """
    serializer_class = PromptSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PromptSubmission.objects.all()

    def get_queryset(self):
        return PromptSubmission.objects.filter(user=self.request.user, is_deleted=False).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Create a new prompt submission and send real-time updates via WebSocket.
        Includes rate limiting (5 per minute) and comprehensive logging.
        """
        user_id = request.user.id
        user_tier = request.user.subscription_tier or 'explorer'
        
        # 1. Subscription Tier & Usage Enforcement (Atomic)
        try:
            with transaction.atomic():
                # Lock user record for atomic update to prevent concurrency issues
                u = CustomUser.objects.select_for_update().get(id=request.user.id)
                
                # Sync period (resets usage if month changed)
                logger.info("Syncing subscription period for user %s", user_id)
                u = sync_subscription_period(u)
                
                # Check remaining prompts
                remaining = get_remaining_prompts(u)
                logger.info(
                    "Remaining prompts for user %s after sync: %s",
                    user_id,
                    remaining,
                )
                
                if remaining is not None and remaining <= 0:
                    logger.warning(f"Subscription limit reached for user {u.id} (Tier: {u.subscription_tier})")
                    return response.Response({
                        "error": "PROMPT_LIMIT_REACHED",
                        "tier": u.subscription_tier,
                        "reset_date": u.prompt_period_start,
                        "detail": f"You have reached your monthly AI prompt limit for the {u.get_subscription_tier_display()} plan."
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Increment usage atomically
                u.prompts_used_in_period += 1
                u.save(update_fields=['prompts_used_in_period'])
                
                logger.info(f"Prompt usage incremented for user {u.id}. New count: {u.prompts_used_in_period}")
        except CustomUser.DoesNotExist:
            return response.Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        # (debug DB logging removed for production safety)
        
        # 3. Get channel layer for WebSocket (if available)
        redis_available = CHANNELS_AVAILABLE and getattr(settings, 'REDIS_AVAILABLE', False)
        if redis_available:
            channel_layer = get_channel_layer()
            user_group = f'recommendations_{request.user.id}'
            
            # Send initial status
            async_to_sync(channel_layer.group_send)(
                user_group,
                {
                    'type': 'recommendation_status',
                    'submission_id': 'pending',
                    'status': 'processing',
                    'progress': 0,
                    'message': 'Starting recommendation engine...',
                }
            )
            logger.info(f"Sent initial WebSocket status for user {user_id}")
        
        # 4. Validate data using Strict Wizard Serializer
        time.sleep(0.5)
        if redis_available:
            async_to_sync(channel_layer.group_send)(
                user_group,
                {
                    'type': 'recommendation_status',
                    'submission_id': 'pending',
                    'status': 'processing',
                    'progress': 25,
                    'message': 'Analyzing your grades...',
                }
            )
        
        # [NEW] Strict Validation
        # Extract payload from request (frontend sends { payload: ... })
        payload_data = request.data.get('payload', request.data)
        logger.info("Extracted payload_data keys for user %s: %s", user_id, list(payload_data.keys()))
        
        # ── FRONTEND PAYLOAD AUDIT ── (log the full raw payload for debugging)
        import json as _json
        try:
            raw_payload_str = _json.dumps(payload_data, default=str)
            # Truncate to 3000 chars to keep logs readable
            logger.info("[PAYLOAD AUDIT] User %s raw payload (first 3000 chars):\n%s",
                        user_id, raw_payload_str[:3000])
        except Exception as _e:
            logger.warning("[PAYLOAD AUDIT] Could not serialize payload for user %s: %s", user_id, _e)
        
        payload_serializer = WizardPayloadSerializer(data=payload_data)
        if not payload_serializer.is_valid():
            logger.error(f"Wizard Validation Failed: {payload_serializer.errors}")
            return response.Response({
                'error': 'Validation Error',
                'details': payload_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_payload = payload_serializer.validated_data
        logger.info("Wizard payload validated successfully for user %s", user_id)

        student_grades = _extract_student_grades(validated_payload)
        if not student_grades:
            logger.error("No valid KCSE grades found in payload for user %s", user_id)
            return response.Response(
                {
                    "error": "NO_GRADES",
                    "detail": "No valid KCSE grades were found in the submission.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # ── GRADE EXTRACTION AUDIT ──
        mean_in_grades = student_grades.get('MEAN', '*** NOT FOUND ***')
        subject_grades_only = {k: v for k, v in student_grades.items() if k != 'MEAN'}
        logger.info(
            "[GRADES AUDIT] User %s: MEAN Grade = %s | Subject grades: %s",
            user_id, mean_in_grades, subject_grades_only
        )
        logger.info(
            "Extracted %s KCSE subjects + MEAN for user %s: %s",
            len(subject_grades_only),
            user_id,
            sorted(subject_grades_only.keys()),
        )

        eligible_programmes_all = get_eligible_programmes(student_grades)
        eligible_programmes = filter_eligible_only(eligible_programmes_all)

        logger.info(
            "Eligibility engine returned %s total programmes, %s eligible for user %s",
            len(eligible_programmes_all),
            len(eligible_programmes),
            user_id,
        )

        eligibility_meta = {
            "total_programmes_analyzed": len(eligible_programmes_all),
            "eligible_programmes_count": len(eligible_programmes),
        }

        shortlisted_programmes = _serialize_programmes_for_llm(eligible_programmes)
        logger.info(
            "Serialized %s shortlisted programmes for LLM for user %s",
            len(shortlisted_programmes),
            user_id,
        )
        user_profile_for_llm = _build_user_profile_for_llm(
            validated_payload, eligibility_meta, student_grades, user_tier=user_tier
        )
        logger.info(
            "Built user_profile_for_llm for user %s with keys: %s",
            user_id,
            list(user_profile_for_llm.keys()),
        )

        llm_result = None
        if shortlisted_programmes:
            time.sleep(0.5)
            if redis_available:
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'recommendation_status',
                        'submission_id': 'pending',
                        'status': 'processing',
                        'progress': 50,
                        'message': 'Matching with programmes...',
                    }
                )

            try:
                llm_result = run_recommendation_graph(
                    user_profile=user_profile_for_llm,
                    shortlisted_programs=shortlisted_programmes,
                    user_tier=user_tier
                )
                logger.info("LangGraph recommendations generated for user %s", user_id)
            except Exception as e:
                logger.error(
                    "LangGraph recommendation failed for user %s: %s",
                    user_id,
                    str(e),
                    exc_info=True,
                )
                print("\n\nthe llm returned the following\n: ", llm_result)
        else:
            logger.warning(
                "No shortlisted programmes available for LLM for user %s", user_id
            )

        if redis_available:
            time.sleep(0.5)
            async_to_sync(channel_layer.group_send)(
                user_group,
                {
                    'type': 'recommendation_status',
                    'submission_id': 'pending',
                    'status': 'processing',
                    'progress': 75,
                    'message': 'Calculating match scores...',
                }
            )

        # ── Strict LLM path guard ─────────────────────────────────────────────
        # Enter LLM path ONLY when the result contains at least one recommendation.
        # A truthy-only check (if llm_result:) is insufficient - an empty dict or
        # a dict with an empty recommendations list would still pass.
        llm_recs = (
            llm_result.get('recommendations', [])
            if (llm_result and isinstance(llm_result, dict))
            else []
        )
        if llm_recs and len(llm_recs) > 0:
            path_used = 'llm'
            top_recommendations = _build_top_recommendations_from_llm(llm_result)
            logger.info(
                "LLM path used for user %s - %s recommendations returned by model",
                user_id,
                len(llm_recs),
            )
        else:
            logger.error("LLM failed to return recommendations for user %s and fallback is disabled.", user_id)
            return response.Response({
                "error": "ADVISOR_FAILURE",
                "detail": "Our AI advisor could not generate recommendations for your profile at this time. Please try again later.",
                "path_used": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ── Tier-based Slicing ──────────────────────────────────────────────
        if user_tier == 'scholar_vvip':
            slice_count = 10
        elif user_tier == 'mentor_elite':
            slice_count = 5
        else:
            slice_count = 3
        
        sliced_recs = top_recommendations[:slice_count]

        # ── Correlation Data ────────────────────────────────────────────────
        # Include metadata in the recommendations dict so the UI can log/find it easily.
        final_recommendations = {
            "top_5": sliced_recs,
            "submission_id": "pending", # will be updated after save
            "path_used": path_used,
        }

        # ── VVIP Premium Injection ──────────────────────────────────────────
        if user_tier == 'scholar_vvip':
            final_recommendations["cluster_summary"] = _build_cluster_summary(eligible_programmes)

        if top_recommendations:
            first = top_recommendations[0]
            logger.info("TOP RECOMMENDATION [0] PREPARED: Course='%s', Uni='%s', Keys=%s", 
                        first.get('course'), first.get('university'), list(first.keys()))
            logger.info("TOP RECOMMENDATION [0] INSIGHT: %s", first.get('insight'))

        logger.info(
            "Final recommendations prepared for user %s via '%s' path: %s",
            user_id,
            path_used,
            [item.get("course") for item in top_recommendations],
        )

        serializer = self.get_serializer(data={'payload': request.data.get('payload', request.data)})
        serializer.is_valid(raise_exception=True)
        
        # 5. Persist Profile Changes (Service Layer)
        try:
            profile = persist_student_profile_from_wizard(request.user, request.data)
            logger.debug(f"Profile persisted for user {user_id}")
        except Exception as e:
            logger.warning(f"Profile persistence failed for user {user_id}: {e}")
            # We continue anyway as per local logic
            pass
        
        # Create instance first to get ID
        instance = serializer.save(user=self.request.user, result=final_recommendations)
        
        # Update metadata for future-proofing (though not strictly needed if we return correctly)
        final_recommendations["submission_id"] = str(instance.id)
        instance.result = final_recommendations
        instance.save(update_fields=['result'])

        logger.info("Created submission %s for user %s", instance.id, user_id)
        
        # 8. Send completion via WebSocket
        if redis_available:
            async_to_sync(channel_layer.group_send)(
                user_group,
                {
                    'type': 'recommendation_complete',
                    'submission_id': str(instance.id),
                    'recommendations': final_recommendations,
                }
            )
            logger.info(
                "Sent completion WebSocket for submission %s", instance.id
            )
        
        # 9. Return custom response format
        return response.Response({
            "received": True,
            "submission_id": instance.id,
            "path_used": path_used,   # 'llm' | 'fallback'
            "recommendations": final_recommendations
        }, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Soft delete the submission.
        """
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        logger.info(f"Soft deleted submission {instance.id} for user {instance.user.id}")
