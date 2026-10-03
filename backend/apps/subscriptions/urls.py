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

# Diagnostic endpoints: only routed when DEBUG=True, never in production.
if settings.DEBUG:
    urlpatterns += [
        path('test-stk/', views.test_stk, name='test_stk'),
        path('debug-headers/', views.debug_headers, name='debug_headers'),
    ]
