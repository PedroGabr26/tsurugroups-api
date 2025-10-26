"""
Scheduling models for Tsuru Groups.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from simple_history.models import HistoricalRecords
import uuid


class MessageTemplate(models.Model):
    """Template for scheduled messages."""
    
    TEMPLATE_TYPES = [
        ('text', _('Text')),
        ('image', _('Image')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('document', _('Document')),
        ('location', _('Location')),
        ('contact', _('Contact')),
        ('menu', _('Menu')),
        ('poll', _('Poll')),
        ('list', _('List')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_templates',
        verbose_name=_('User')
    )
    
    # Template information
    name = models.CharField(_('Template name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Template content
    template_type = models.CharField(_('Template type'), max_length=20, choices=TEMPLATE_TYPES)
    content = models.TextField(_('Content'))
    
    # Media content (for media templates)
    media_url = models.URLField(_('Media URL'), blank=True)
    media_type = models.CharField(_('Media type'), max_length=50, blank=True)
    
    # Menu/Poll/List specific content
    menu_options = models.JSONField(_('Menu options'), default=list, blank=True)
    
    # Location specific content
    location_name = models.CharField(_('Location name'), max_length=200, blank=True)
    location_address = models.CharField(_('Location address'), max_length=500, blank=True)
    location_latitude = models.DecimalField(_('Latitude'), max_digits=10, decimal_places=7, null=True, blank=True)
    location_longitude = models.DecimalField(_('Longitude'), max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Contact specific content
    contact_name = models.CharField(_('Contact name'), max_length=200, blank=True)
    contact_phone = models.CharField(_('Contact phone'), max_length=20, blank=True)
    contact_email = models.EmailField(_('Contact email'), blank=True)
    contact_organization = models.CharField(_('Contact organization'), max_length=200, blank=True)
    
    # Template settings
    is_active = models.BooleanField(_('Is active'), default=True)
    usage_count = models.PositiveIntegerField(_('Usage count'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Message Template')
        verbose_name_plural = _('Message Templates')
        unique_together = ['user', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.user.full_name})"


class ScheduledMessage(models.Model):
    """Scheduled messages to be sent."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('scheduled', _('Scheduled')),
        ('sending', _('Sending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    RECIPIENT_TYPES = [
        ('groups', _('Groups')),
        ('contacts', _('Contacts')),
        ('mixed', _('Mixed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_messages',
        verbose_name=_('User')
    )
    
    whatsapp_instance = models.ForeignKey(
        'whatsapp.WhatsAppInstance',
        on_delete=models.CASCADE,
        related_name='scheduled_messages',
        verbose_name=_('WhatsApp Instance')
    )
    
    # Message information
    name = models.CharField(_('Campaign name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Template reference
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_messages',
        verbose_name=_('Template')
    )
    
    # Message content (can override template)
    message_content = models.TextField(_('Message content'))
    
    # Recipients
    recipient_type = models.CharField(_('Recipient type'), max_length=10, choices=RECIPIENT_TYPES)
    
    groups = models.ManyToManyField(
        'whatsapp.WhatsAppGroup',
        blank=True,
        related_name='scheduled_messages',
        verbose_name=_('Groups')
    )
    
    contacts = models.ManyToManyField(
        'whatsapp.WhatsAppContact',
        blank=True,
        related_name='scheduled_messages',
        verbose_name=_('Contacts')
    )
    
    # Scheduling information
    schedule_date = models.DateField(_('Schedule date'))
    schedule_time = models.TimeField(_('Schedule time'))
    timezone = models.CharField(_('Timezone'), max_length=50, default='America/Fortaleza')
    
    # Execution settings
    delay_min = models.PositiveIntegerField(
        _('Minimum delay (seconds)'),
        default=3,
        validators=[MinValueValidator(1)],
        help_text=_('Minimum delay between messages in seconds')
    )
    
    delay_max = models.PositiveIntegerField(
        _('Maximum delay (seconds)'),
        default=6,
        validators=[MinValueValidator(1)],
        help_text=_('Maximum delay between messages in seconds')
    )
    
    # Status and tracking
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    total_recipients = models.PositiveIntegerField(_('Total recipients'), default=0)
    messages_sent = models.PositiveIntegerField(_('Messages sent'), default=0)
    messages_failed = models.PositiveIntegerField(_('Messages failed'), default=0)
    
    # Task information
    task_id = models.CharField(_('Task ID'), max_length=255, blank=True)
    
    # Execution timestamps
    scheduled_at = models.DateTimeField(_('Scheduled at'), null=True, blank=True)
    started_at = models.DateTimeField(_('Started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed at'), null=True, blank=True)
    
    # Error information
    error_message = models.TextField(_('Error message'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Scheduled Message')
        verbose_name_plural = _('Scheduled Messages')
        ordering = ['-schedule_date', '-schedule_time']
        
    def __str__(self):
        return f"{self.name} - {self.schedule_date} {self.schedule_time}"
    
    @property
    def is_executed(self):
        """Check if message has been executed."""
        return self.status in ['sent', 'failed']
    
    @property
    def can_be_cancelled(self):
        """Check if message can be cancelled."""
        return self.status in ['pending', 'scheduled']
    
    @property
    def success_rate(self):
        """Calculate success rate."""
        if self.total_recipients == 0:
            return 0
        return (self.messages_sent / self.total_recipients) * 100


class MessageDelivery(models.Model):
    """Individual message delivery tracking."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered')),
        ('read', _('Read')),
        ('failed', _('Failed')),
    ]
    
    RECIPIENT_TYPES = [
        ('group', _('Group')),
        ('contact', _('Contact')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    scheduled_message = models.ForeignKey(
        ScheduledMessage,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name=_('Scheduled Message')
    )
    
    # Recipient information
    recipient_type = models.CharField(_('Recipient type'), max_length=10, choices=RECIPIENT_TYPES)
    recipient_id = models.CharField(_('Recipient ID'), max_length=255)
    recipient_name = models.CharField(_('Recipient name'), max_length=200)
    phone_number = models.CharField(_('Phone number'), max_length=20, blank=True)
    
    # Delivery information
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    whatsapp_message_id = models.CharField(_('WhatsApp Message ID'), max_length=255, blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(_('Sent at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('Delivered at'), null=True, blank=True)
    read_at = models.DateTimeField(_('Read at'), null=True, blank=True)
    failed_at = models.DateTimeField(_('Failed at'), null=True, blank=True)
    
    # Error information
    error_message = models.TextField(_('Error message'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Message Delivery')
        verbose_name_plural = _('Message Deliveries')
        unique_together = ['scheduled_message', 'recipient_type', 'recipient_id']
        
    def __str__(self):
        return f"{self.scheduled_message.name} -> {self.recipient_name}"


class QuickReply(models.Model):
    """Quick reply templates for common responses."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quick_replies',
        verbose_name=_('User')
    )
    
    # Reply information
    title = models.CharField(_('Title'), max_length=100)
    content = models.TextField(_('Content'))
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(_('Usage count'), default=0)
    
    # Settings
    is_active = models.BooleanField(_('Is active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Quick Reply')
        verbose_name_plural = _('Quick Replies')
        unique_together = ['user', 'title']
        
    def __str__(self):
        return f"{self.title} ({self.user.full_name})"