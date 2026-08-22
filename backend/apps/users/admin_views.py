from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from apps.users.admin_serializers import AdminUserSerializer
from apps.students.models import PromptSubmission, StudentProfile
from apps.users.permissions import IsStaffNonStudent

User = get_user_model()

class AdminAnalyticsView(APIView):
    permission_classes = [IsStaffNonStudent]

    @extend_schema(
        summary="Admin Dashboard Analytics",
        description="Returns key performance indicators and growth metrics for the admin dashboard.",
        responses={200: serializers.Serializer} # Generic response as it's a dynamic dict
    )
    def get(self, request):
        """
        Returns analytics data for the admin dashboard.
        Supports 'period' query param: 7d, 30d, 90d, 1y (default: 30d)
        """
        period = request.query_params.get('period', '30d')
        now = timezone.now()
        
        # Calculate start date
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '90d':
            start_date = now - timedelta(days=90)
        elif period == '1y':
            start_date = now - timedelta(days=365)
        else: # 30d default
            start_date = now - timedelta(days=30)

        # 1. Total Users & Growth
        total_users = User.objects.count()
        new_users_period = User.objects.filter(date_joined__gte=start_date).count()
        
        # Comparison for trend (previous period)
        period_days = (now - start_date).days
        prev_start_date = start_date - timedelta(days=period_days)
        new_users_prev = User.objects.filter(date_joined__gte=prev_start_date, date_joined__lt=start_date).count()
        
        user_growth_trend = self._calculate_trend(new_users_period, new_users_prev)

        # 2. Active Users (Users who logged in recently or have activity)
        # For now, we'll use last_login as a proxy if available, or just recently joined
        active_threshold = now - timedelta(days=60)
        active_users = User.objects.filter(last_login__gte=active_threshold).count()
        active_users_prev = User.objects.filter(last_login__gte=active_threshold - timedelta(days=60), last_login__lt=active_threshold).count()
        active_rate_trend = self._calculate_trend(active_users, active_users_prev)
        
        active_rate = round((active_users / total_users * 100), 1) if total_users > 0 else 0

        # 3. Subscriptions — filter by actual subscription_tier field
        free_users = User.objects.filter(subscription_tier='explorer').count()
        standard_users = User.objects.filter(subscription_tier='mentor_elite').count()
        premium_users = User.objects.filter(subscription_tier='scholar_vvip').count()

        # 4. Prompt Submissions (AI Usage)
        total_prompts = PromptSubmission.objects.count()
        total_prompts_prev = PromptSubmission.objects.filter(created_at__lt=start_date).count()

        # 5. Conversion rate = paid users / total users
        paid_users = standard_users + premium_users
        conversion_rate = round((paid_users / total_users * 100), 1) if total_users > 0 else 0

        # 6. Time-series data for charts
        growth_data = self._get_growth_data(start_date, now)

        return Response({
            # Dashboard stats
            "totalUsers": total_users,
            "userGrowth": user_growth_trend,
            "activeUsers": active_users,
            "activeGrowth": active_rate_trend,
            "freeUsers": free_users,
            "standardUsers": standard_users,
            "premiumUsers": premium_users,
            "totalPrompts": total_prompts,
            # Analytics-specific fields
            "totalSignups": total_users,
            "newUsers": new_users_period,
            "newUsersTrend": user_growth_trend,
            "activeRate": active_rate,
            "activeRateTrend": active_rate_trend,
            "conversionRate": conversion_rate,
            "conversionTrend": 0,
            "growthData": growth_data
        })

    def _get_growth_data(self, start_date, end_date):
        """
        Returns a list of {label, value} objects for user signups over time.
        """
        # Group by day if period <= 90 days, else month
        days_diff = (end_date - start_date).days
        
        from django.db.models.functions import TruncDay, TruncMonth
        
        if days_diff <= 90:
            growth = User.objects.filter(date_joined__gte=start_date)\
                .annotate(label=TruncDay('date_joined'))\
                .values('label')\
                .annotate(value=Count('id'))\
                .order_by('label')
            
            return [{"label": g['label'].strftime('%b %d'), "value": g['value']} for g in growth]
        else:
            growth = User.objects.filter(date_joined__gte=start_date)\
                .annotate(label=TruncMonth('date_joined'))\
                .values('label')\
                .annotate(value=Count('id'))\
                .order_by('label')
            
            return [{"label": g['label'].strftime('%b %Y'), "value": g['value']} for g in growth]

    def _calculate_trend(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)

class AdminChatLogsView(APIView):
    permission_classes = [IsStaffNonStudent]

    @extend_schema(
        summary="Recent AI Chat Logs",
        description="Returns a list of the 50 most recent AI prompt submissions for admin monitoring.",
        responses={200: serializers.Serializer(many=True)}
    )
    def get(self, request):
        """
        Returns list of recent AI Prompt Submissions.
        Pagination support can be added later.
        """
        submissions = PromptSubmission.objects.select_related('user').order_by('-created_at')[:50]
        data = []
        for sub in submissions:
            data.append({
                "id": sub.id,
                "user_email": sub.user.email,
                "user": {
                    "id": sub.user.id,
                    "username": sub.user.username,
                    "email": sub.user.email
                },
                "created_at": sub.created_at.isoformat(),
                "description": self._summarize_payload(sub.payload),
                "activity_type": "ai_prompt",
                "payload_summary": self._summarize_payload(sub.payload),
                "result_summary": self._summarize_result(sub.result),
                "details": {
                    "response": self._summarize_result(sub.result)
                }
            })
        return Response(data)

    def _summarize_payload(self, payload):
        """
        Extracts key info from the current WizardPayload structure.
        student_profile -> kcse, personal_cognitive, interests_exposure, etc.
        """
        try:
            profile = payload.get('student_profile', {})
            
            # Extract Mean Grade from KCSE Summary
            mean_grade = profile.get('kcse', {}).get('summary', {}).get('mean_grade', 'Unknown')
            
            # Extract Interests from Interests & Exposure
            interests = profile.get('interests_exposure', {}).get('interests_hobbies', [])
            
            return f"{mean_grade}, Interests: {', '.join(interests[:2])}" if interests else f"{mean_grade}, No interests listed"
        except Exception as e:
            return f"N/A (Parse Error)"

    def _summarize_result(self, result):
        """
        Extracts top recommendation from the current dummy_recommendations.json structure.
        Starts directly at 'top_5'.
        """
        try:
            top_course = result.get('top_5', [])[0]['course']
            return f"Top: {top_course}"
        except:
            return "No recommendations"

class AdminChatDetailView(APIView):
    permission_classes = [IsStaffNonStudent]

    @extend_schema(
        summary="AI Chat Submission Detail",
        description="Returns the full payload and AI result for a specific prompt submission.",
        responses={200: serializers.Serializer}
    )
    def get(self, request, pk):
        try:
            sub = PromptSubmission.objects.select_related('user').get(pk=pk)
            return Response({
                "id": sub.id,
                "user": {
                    "id": sub.user.id,
                    "username": sub.user.username,
                    "email": sub.user.email
                },
                "created_at": sub.created_at,
                "payload": sub.payload,
                "result": sub.result
            })
        except PromptSubmission.DoesNotExist:
            return Response({"error": "Submission not found"}, status=404)
from apps.users.admin_serializers import AdminUserSerializer

class AdminUserListView(APIView):
    permission_classes = [IsStaffNonStudent]
    serializer_class = AdminUserSerializer

    @extend_schema(
        summary="List/Manage Users",
        description="Returns a list of all registered users or updates a user's status/roles.",
    )
    def get(self, request):
        """
        Returns a list of all users.
        """
        users = User.objects.all().order_by('-date_joined')
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data)

    def patch(self, request, pk):
        """
        Update user status or roles.
        """
        try:
            user = User.objects.get(pk=pk)
            serializer = AdminUserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        """
        Permanently delete a user (Only the first admin can do this).
        """
        first_admin = User.objects.order_by('id').first()
        
        if request.user.id != first_admin.id:
            return Response({"error": "Permission denied. Only the root administrator can completely delete users."}, status=status.HTTP_403_FORBIDDEN)
            
        if str(request.user.id) == str(pk) or request.user.id == int(pk):
            return Response({"error": "You cannot delete your own root account."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_user = User.objects.get(pk=pk)
            target_user.delete()
            return Response({"message": "User permanently deleted."}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
