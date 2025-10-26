"""
Views for accounts app.
"""
from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.core.models import User, UserProfile, UserApiKey
from .serializers import (
    UserSerializer, UserProfileSerializer, UserApiKeySerializer,
    RegisterSerializer, LoginSerializer, ChangePasswordSerializer,
    UpdateProfileSerializer, VerifyEmailSerializer
)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Create authentication token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """User login endpoint."""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, email=email, password=password)
        
        if user:
            if not user.is_active:
                return Response({
                    'error': 'Account is deactivated.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            login(request, user)
            
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Login successful.'
            })
        
        return Response({
            'error': 'Invalid credentials.'
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(generics.GenericAPIView):
    """User logout endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            # Delete the user's token
            Token.objects.filter(user=request.user).delete()
            logout(request)
            
            return Response({
                'message': 'Logout successful.'
            })
        except Exception as e:
            return Response({
                'error': 'Logout failed.'
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(generics.GenericAPIView):
    """Email verification endpoint."""
    serializer_class = VerifyEmailSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid verification link.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            
            return Response({
                'message': 'Email verified successfully.'
            })
        
        return Response({
            'error': 'Invalid or expired verification link.'
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(generics.GenericAPIView):
    """Resend email verification endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        if user.is_verified:
            return Response({
                'message': 'Email is already verified.'
            })
        
        # Here you would send the verification email again
        # Implementation depends on your email backend
        
        return Response({
            'message': 'Verification email sent.'
        })


class ChangePasswordView(generics.GenericAPIView):
    """Change password endpoint."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Invalid current password.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully.'
        })


class PasswordResetView(generics.GenericAPIView):
    """Password reset request endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            # Here you would send the password reset email
            # Implementation depends on your email backend
            
            return Response({
                'message': 'Password reset email sent.'
            })
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            return Response({
                'message': 'Password reset email sent.'
            })


class PasswordResetConfirmView(generics.GenericAPIView):
    """Password reset confirmation endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        uidb64 = request.data.get('uidb64')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uidb64, token, new_password]):
            return Response({
                'error': 'All fields are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password reset successfully.'
            })
        
        return Response({
            'error': 'Invalid or expired reset link.'
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveAPIView):
    """Get user profile endpoint."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UpdateProfileView(generics.UpdateAPIView):
    """Update user profile endpoint."""
    serializer_class = UpdateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class DeleteAccountView(generics.DestroyAPIView):
    """Delete user account endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, *args, **kwargs):
        user = request.user
        
        # Perform soft delete or actual delete based on your requirements
        user.is_active = False
        user.save()
        
        return Response({
            'message': 'Account deactivated successfully.'
        })


class DashboardView(generics.GenericAPIView):
    """User dashboard data endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get dashboard statistics
        dashboard_data = {
            'user': UserSerializer(user).data,
            'statistics': {
                'whatsapp_instances': user.whatsapp_instance.count() if hasattr(user, 'whatsapp_instance') else 0,
                'scheduled_messages': user.scheduled_messages.count(),
                'message_templates': user.message_templates.count(),
                'total_messages_sent': user.scheduled_messages.aggregate(
                    total=models.Sum('messages_sent')
                )['total'] or 0,
            },
            'subscription': None
        }
        
        # Add subscription info if user has one
        if user.has_active_subscription:
            subscription = user.current_subscription
            dashboard_data['subscription'] = {
                'plan_name': subscription.plan.name,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'messages_sent_this_month': subscription.messages_sent_this_month,
                'messages_limit': subscription.plan.max_scheduled_messages_per_month,
                'usage_percentage': (subscription.messages_sent_this_month / subscription.plan.max_scheduled_messages_per_month) * 100
            }
        
        return Response(dashboard_data)


class UserViewSet(viewsets.ModelViewSet):
    """User management viewset."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own profile
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile management viewset."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


class UserApiKeyViewSet(viewsets.ModelViewSet):
    """User API key management viewset."""
    serializer_class = UserApiKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserApiKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key."""
        api_key = self.get_object()
        
        # Generate new key
        import secrets
        api_key.key = secrets.token_urlsafe(32)
        api_key.save()
        
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)