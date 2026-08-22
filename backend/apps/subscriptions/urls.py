from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('status/', views.payment_status, name='payment_status'),
    # Optional test endpoints (remove in full production if not needed)
    path('test-stk/', views.test_stk, name='test_stk'),
    path('debug-headers/', views.debug_headers, name='debug_headers'),
    path('generate-coupon/', views.generate_my_coupon, name='generate_coupon'),
]