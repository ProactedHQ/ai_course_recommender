from django.conf import settings
from django.urls import path
from . import views

# Mounted at /api/subscriptions/
urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('confirmation/', views.confirmation, name='confirmation'),  # PayHero callback
    path('status/', views.payment_status, name='payment_status'),
    path('generate-coupon/', views.generate_my_coupon, name='generate_coupon'),
]

# Mock payment completion: never routed in production (the view also refuses unless PAYMENT_PROVIDER=mock).
if not settings.IS_PRODUCTION:
    urlpatterns += [
        path('mock/complete/', views.mock_complete_payment, name='mock_complete_payment'),
    ]
