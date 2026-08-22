from django.urls import path
from .views import BlogStatsView, LikeToggleView, RecordView

urlpatterns = [
    path('stats/<str:slug>/', BlogStatsView.as_view(), name='blog-stats'),
    path('like/<str:slug>/', LikeToggleView.as_view(), name='blog-like-toggle'),
    path('view/<str:slug>/', RecordView.as_view(), name='blog-record-view'),
]
