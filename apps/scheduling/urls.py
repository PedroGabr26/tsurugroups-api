"""
URLs for scheduling app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'scheduling'

# DRF router for API endpoints
router = DefaultRouter()
# Add viewsets here when they are created

urlpatterns = [
    # API endpoints will be added here
    path('', include(router.urls)),
]
