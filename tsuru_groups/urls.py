"""
URL Configuration for Tsuru Groups project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.core.views import (
    HomeView, CustomLoginView, CustomRegisterView, 
    CustomPasswordResetView, CustomPasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetCompleteView,
    dashboard_view, logout_view
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Frontend routes
    path('', HomeView.as_view(), name='home'),
    path('test/', TemplateView.as_view(template_name='test.html'), name='test'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Password reset
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Profile and subscription (placeholder routes)
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('subscription/', TemplateView.as_view(template_name='subscription.html'), name='subscription'),
    
    # API routes
    # path('api/v1/auth/', include('apps.accounts.urls'), name='api_auth'),
    path('auth/', include('apps.accounts.urls'), name='auth'),
    path('api/v1/whatsapp/', include('apps.whatsapp.urls'), name='whatsapp'),
    path('api/v1/scheduling/', include('apps.scheduling.urls'), name='scheduling'),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls', namespace='api_subscriptions')),
    path('api/v1/core/', include('apps.core.urls'), name='core'),
    
    # Django Allauth
    path('accounts/', include('allauth.urls'), name='allauth'),
    
    # Plans
    path('plans/', include('apps.subscriptions.urls', namespace='subscriptions')),
    
    # RQ Dashboard (only in development)
    path('django-rq/', include('django_rq.urls'), name='django_rq'),
    
    # Health check
    path('health/', TemplateView.as_view(
        template_name='health.html',
        extra_context={'status': 'ok'}
    )),
    
    # Root API info
    path('api/', TemplateView.as_view(
        template_name='api_info.html',
        extra_context={
            'title': 'Tsuru Groups API',
            'version': 'v1.0.0'
        }
    )),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site configuration
admin.site.site_header = "Tsuru Groups Admin"
admin.site.site_title = "Tsuru Groups"
admin.site.index_title = "Welcome to Tsuru Groups Administration"