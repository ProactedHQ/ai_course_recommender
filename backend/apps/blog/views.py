from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import BlogLike, BlogView
from .serializers import BlogStatsSerializer
from django.contrib.auth import get_user_model
import hashlib
import random

User = get_user_model()

def get_engagement_boost(slug):
    """
    Returns a deterministic offset for likes and views based on the slug.
    This ensures counts always start above 50 and are consistent for the same post.
    """
    # Create a stable seed from the slug
    seed = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 1000000
    rng = random.Random(seed)
    
    # Random offsets between 50 and 180
    view_boost = rng.randint(85, 180)
    like_boost = rng.randint(52, 120)
    
    return view_boost, like_boost

class BlogStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        real_likes = BlogLike.objects.filter(blog_slug=slug).count()
        real_views = BlogView.objects.filter(blog_slug=slug).count()
        
        view_boost, like_boost = get_engagement_boost(slug)
        
        is_liked_by_user = False
        if request.user.is_authenticated:
            is_liked_by_user = BlogLike.objects.filter(
                blog_slug=slug, user=request.user
            ).exists()
        else:
            # Check for guest like via session or IP
            session_id = request.session.session_key
            ip_address = self.get_client_ip(request)
            if session_id:
                is_liked_by_user = BlogLike.objects.filter(
                    blog_slug=slug, session_id=session_id
                ).exists()
            elif ip_address:
                is_liked_by_user = BlogLike.objects.filter(
                    blog_slug=slug, ip_address=ip_address, user__isnull=True
                ).exists()

        # Get unique viewers (real users)
        viewer_ids = BlogView.objects.filter(
            blog_slug=slug, user__isnull=False
        ).values_list('user_id', flat=True).distinct()
        viewers = User.objects.filter(id__in=viewer_ids)

        # Get likers (real users)
        liker_ids = BlogLike.objects.filter(
            blog_slug=slug, user__isnull=False
        ).values_list('user_id', flat=True).distinct()
        likers = User.objects.filter(id__in=liker_ids)

        serializer = BlogStatsSerializer({
            'likes_count': real_likes + like_boost,
            'views_count': real_views + view_boost,
            'is_liked_by_user': is_liked_by_user,
            'viewers': viewers,
            'likers': likers
        })
        return Response(serializer.data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class LikeToggleView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key if not user else None
        ip_address = self.get_client_ip(request) if not user else None

        if user:
            like, created = BlogLike.objects.get_or_create(
                user=user, blog_slug=slug
            )
        else:
            # Handle guest like
            if session_id:
                like, created = BlogLike.objects.get_or_create(
                    blog_slug=slug, session_id=session_id, defaults={'ip_address': ip_address}
                )
            else:
                # Fallback to IP if no session (less ideal but works for truly anonymous)
                like, created = BlogLike.objects.get_or_create(
                    blog_slug=slug, ip_address=ip_address, user__isnull=True
                )
        
        if not created:
            like.delete()
            return Response({'status': 'unliked'}, status=status.HTTP_200_OK)
        
        return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RecordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        user = request.user if request.user.is_authenticated else None
        
        # Ensure session exists for guest views
        if not user and not request.session.session_key:
            request.session.create()

        BlogView.objects.create(
            user=user,
            blog_slug=slug,
            ip_address=self.get_client_ip(request),
            session_id=request.session.session_key
        )
        
        return Response({'status': 'view_recorded'}, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
