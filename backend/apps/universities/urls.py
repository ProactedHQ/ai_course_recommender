"""
URL configuration for Universities app
"""
from django.urls import path
from .views import CheckEligibilityView, CheckEligibilityAllView

app_name = 'universities'

urlpatterns = [
    # Eligibility checking endpoints
    path(
        'check-eligibility/',
        CheckEligibilityView.as_view(),
        name='check-eligibility'
    ),
    path(
        'check-eligibility/all/',
        CheckEligibilityAllView.as_view(),
        name='check-eligibility-all'
    ),
]
