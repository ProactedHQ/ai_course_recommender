from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.views import profile, me
from apps.users import admin_views

from apps.universities import views as uni_views
from apps.students import views as student_views

from apps.subscriptions import views as sub_views

# Creating a router to register our viewsets with it.                  
router = DefaultRouter()

# University APIs
router.register(r'institutions', uni_views.InstitutionViewSet)
router.register(r'programmes', uni_views.ProgrammeViewSet)
router.register(r'clusters', uni_views.ClusterGroupViewSet)

# Student APIs
router.register(r'subjects', student_views.SubjectViewSet)
router.register(r'profiles', student_views.StudentProfileViewSet, basename='studentprofile')
router.register(r'grades', student_views.AcademicResultViewSet, basename='academicresult')
router.register(r'prompts', student_views.PromptSubmissionViewSet, basename='promptsubmission')

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), # to include all the routes above
    
    # Universities app - Eligibility checking
    path('api/universities/', include('apps.universities.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # AUTHENTICATION ENDPOINTS (Supabase Integrated)
    path('api/auth/me/', me, name='auth_me'),  # Backend-verified role (source of truth)
    path('api/auth/profile/', profile, name='auth_profile'),
    
    # SUBSCRIPTION & PAYMENTS (Old Daraja - Hashed out)
    # path('api/subscription/upgrade/', upgrade_plan, name='subscription_upgrade'),
    # path('api/subscription/confirm/', confirm_payment, name='subscription_confirm'),
    # path('api/subscription/callback/', mpesa_callback, name='subscription_callback'),

    # STUDENT PROFILE (Wizard Prefill)
    path('api/profile/', student_views.StudentProfileViewSet.as_view({'get': 'full'}), name='student_profile_full'),

    # ADMIN ENDPOINTS
    path('api/admin/analytics', admin_views.AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('api/admin/chats', admin_views.AdminChatLogsView.as_view(), name='admin_chat_logs'),
    path('api/admin/chats/<int:pk>', admin_views.AdminChatDetailView.as_view(), name='admin_chat_detail'),
    path('api/admin/users', admin_views.AdminUserListView.as_view(), name='admin_user_list'),
    path('api/admin/users/<int:pk>', admin_views.AdminUserListView.as_view(), name='admin_user_detail'),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/blog/', include('apps.blog.urls')),
]