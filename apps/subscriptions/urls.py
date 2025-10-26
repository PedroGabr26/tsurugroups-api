"""
URLs for subscriptions app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'subscriptions'

# DRF router for API endpoints
# router = DefaultRouter()
# Add viewsets here when they are created

urlpatterns = [
    # API endpoints will be added here
    # path('', include(router.urls)),
    path('', views.plans_view, name='plans'),
]
