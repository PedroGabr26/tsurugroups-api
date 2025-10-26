"""
User and profile models for Tsuru Groups.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserManager(BaseUserManager):
    """Custom user manager that uses email instead of username."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model."""
    
    email = models.EmailField(_('Email address'), unique=True)
    first_name = models.CharField(_('First name'), max_length=150)
    last_name = models.CharField(_('Last name'), max_length=150)
    phone = models.CharField(_('Phone number'), max_length=20, blank=True)
    
    # Account status
    is_verified = models.BooleanField(_('Is verified'), default=False)
    is_active = models.BooleanField(_('Is active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'auth_user'
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def has_active_subscription(self):
        """Check if user has an active subscription."""
        return self.subscriptions.filter(status__in=['active', 'trialing']).exists()
    
    @property
    def current_subscription(self):
        """Get user's current active subscription."""
        return self.subscriptions.filter(status__in=['active', 'trialing']).first()

class UserProfile(models.Model):
    """Extended user profile information."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    
    # Business information
    company_name = models.CharField(_('Company name'), max_length=200, blank=True)
    website = models.URLField(_('Website'), blank=True)
    
    # Profile settings
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='America/Fortaleza',
        help_text=_('User timezone for scheduling')
    )
    
    language = models.CharField(
        _('Language'),
        max_length=10,
        default='pt-br',
        choices=[
            ('pt-br', _('Portuguese (Brazil)')),
            ('en', _('English')),
        ]
    )
    
    # Preferences
    email_notifications = models.BooleanField(
        _('Email notifications'),
        default=True,
        help_text=_('Receive email notifications')
    )
    
    whatsapp_notifications = models.BooleanField(
        _('WhatsApp notifications'),
        default=False,
        help_text=_('Receive WhatsApp notifications')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        
    def __str__(self):
        return f"Profile of {self.user.full_name}"


class UserApiKey(models.Model):
    """API keys for external integrations."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name=_('User')
    )
    
    name = models.CharField(_('Name'), max_length=100, help_text=_('API key name'))
    key = models.CharField(_('Key'), max_length=255, unique=True)
    
    # Permissions
    is_active = models.BooleanField(_('Is active'), default=True)
    
    # Usage tracking
    last_used_at = models.DateTimeField(_('Last used at'), null=True, blank=True)
    usage_count = models.PositiveIntegerField(_('Usage count'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('User API Key')
        verbose_name_plural = _('User API Keys')
        unique_together = ['user', 'name']
        
    def __str__(self):
        return f"{self.user.full_name} - {self.name}"



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)
