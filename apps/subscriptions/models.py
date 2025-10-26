"""
Subscription and payment models for Tsuru Groups.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords
from decimal import Decimal
import uuid


class Plan(models.Model):
    """Subscription plans available."""
    
    PLAN_TYPES = [
        ('basic', _('Basic')),
        ('premium', _('Premium')),
        ('enterprise', _('Enterprise')),
    ]
    
    BILLING_CYCLES = [
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Plan information
    name = models.CharField(_('Plan name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'))
    
    # Plan type and pricing
    plan_type = models.CharField(_('Plan type'), max_length=20, choices=PLAN_TYPES)
    billing_cycle = models.CharField(_('Billing cycle'), max_length=20, choices=BILLING_CYCLES)
    
    price = models.DecimalField(
        _('Price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Plan limits
    max_whatsapp_instances = models.PositiveIntegerField(
        _('Max WhatsApp instances'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    max_scheduled_messages_per_month = models.PositiveIntegerField(
        _('Max scheduled messages per month'),
        default=100,
        validators=[MinValueValidator(1)]
    )
    
    max_groups_per_instance = models.PositiveIntegerField(
        _('Max groups per instance'),
        default=10,
        validators=[MinValueValidator(1)]
    )
    
    max_contacts_per_instance = models.PositiveIntegerField(
        _('Max contacts per instance'),
        default=1000,
        validators=[MinValueValidator(1)]
    )
    
    max_templates = models.PositiveIntegerField(
        _('Max templates'),
        default=10,
        validators=[MinValueValidator(1)]
    )
    
    # Features
    has_api_access = models.BooleanField(_('Has API access'), default=False)
    has_webhook_support = models.BooleanField(_('Has webhook support'), default=False)
    has_advanced_scheduling = models.BooleanField(_('Has advanced scheduling'), default=False)
    has_analytics = models.BooleanField(_('Has analytics'), default=False)
    has_priority_support = models.BooleanField(_('Has priority support'), default=False)
    
    # Stripe integration
    stripe_price_id = models.CharField(_('Stripe Price ID'), max_length=255, blank=True, null=True)
    stripe_product_id = models.CharField(_('Stripe Product ID'), max_length=255, blank=True, null=True)
    
    # Plan status
    is_active = models.BooleanField(_('Is active'), default=True)
    is_featured = models.BooleanField(_('Is featured'), default=False)
    
    # Display order
    sort_order = models.PositiveIntegerField(_('Sort order'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')
        ordering = ['sort_order', 'price']
        
    def __str__(self):
        return f"{self.name} - {self.get_billing_cycle_display()} (${self.price})"


class Subscription(models.Model):
    """User subscriptions."""
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('trialing', _('Trialing')),
        ('past_due', _('Past Due')),
        ('canceled', _('Canceled')),
        ('unpaid', _('Unpaid')),
        ('incomplete', _('Incomplete')),
        ('incomplete_expired', _('Incomplete Expired')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('User')
    )
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Plan')
    )
    
    # Subscription details
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES)
    
    # Stripe integration
    stripe_subscription_id = models.CharField(_('Stripe Subscription ID'), max_length=255, unique=True, blank=True, null=True)
    stripe_customer_id = models.CharField(_('Stripe Customer ID'), max_length=255, blank=True, null=True)
    
    # Subscription periods
    current_period_start = models.DateTimeField(_('Current period start'))
    current_period_end = models.DateTimeField(_('Current period end'))
    
    # Trial information
    trial_start = models.DateTimeField(_('Trial start'), null=True, blank=True)
    trial_end = models.DateTimeField(_('Trial end'), null=True, blank=True)
    
    # Cancellation information
    cancel_at = models.DateTimeField(_('Cancel at'), null=True, blank=True)
    canceled_at = models.DateTimeField(_('Canceled at'), null=True, blank=True)
    
    # Usage tracking
    messages_sent_this_month = models.PositiveIntegerField(_('Messages sent this month'), default=0)
    last_usage_reset = models.DateTimeField(_('Last usage reset'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        
    def __str__(self):
        return f"{self.user.full_name} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is active."""
        return self.status in ['active', 'trialing']
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period."""
        return self.status == 'trialing'
    
    @property
    def can_send_messages(self):
        """Check if user can send more messages this month."""
        return self.messages_sent_this_month < self.plan.max_scheduled_messages_per_month
    
    def increment_usage(self, count=1):
        """Increment monthly usage counter."""
        self.messages_sent_this_month += count
        self.save(update_fields=['messages_sent_this_month'])
    
    def reset_usage(self):
        """Reset monthly usage counter."""
        self.messages_sent_this_month = 0
        self.last_usage_reset = models.timezone.now()
        self.save(update_fields=['messages_sent_this_month', 'last_usage_reset'])


class Invoice(models.Model):
    """Subscription invoices."""
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('open', _('Open')),
        ('paid', _('Paid')),
        ('uncollectible', _('Uncollectible')),
        ('void', _('Void')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('Subscription')
    )
    
    # Invoice details
    invoice_number = models.CharField(_('Invoice number'), max_length=100, unique=True)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES)
    
    # Amounts
    amount_due = models.DecimalField(_('Amount due'), max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(_('Amount paid'), max_digits=10, decimal_places=2, default=0)
    amount_remaining = models.DecimalField(_('Amount remaining'), max_digits=10, decimal_places=2, default=0)
    
    # Stripe integration
    stripe_invoice_id = models.CharField(_('Stripe Invoice ID'), max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(_('Stripe Payment Intent ID'), max_length=255, blank=True)
    
    # Invoice dates
    invoice_date = models.DateTimeField(_('Invoice date'))
    due_date = models.DateTimeField(_('Due date'))
    paid_at = models.DateTimeField(_('Paid at'), null=True, blank=True)
    
    # Invoice period
    period_start = models.DateTimeField(_('Period start'))
    period_end = models.DateTimeField(_('Period end'))
    
    # Invoice URLs
    invoice_pdf_url = models.URLField(_('Invoice PDF URL'), blank=True)
    hosted_invoice_url = models.URLField(_('Hosted invoice URL'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-invoice_date']
        
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.subscription.user.full_name}"


class UsageLimit(models.Model):
    """Usage limits and quota management."""
    
    LIMIT_TYPES = [
        ('messages', _('Messages')),
        ('instances', _('WhatsApp Instances')),
        ('groups', _('Groups')),
        ('contacts', _('Contacts')),
        ('templates', _('Templates')),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='usage_limits',
        verbose_name=_('Subscription')
    )
    
    # Limit details
    limit_type = models.CharField(_('Limit type'), max_length=20, choices=LIMIT_TYPES)
    limit_value = models.PositiveIntegerField(_('Limit value'))
    current_usage = models.PositiveIntegerField(_('Current usage'), default=0)
    
    # Reset information
    reset_period = models.CharField(
        _('Reset period'),
        max_length=20,
        choices=[
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
            ('yearly', _('Yearly')),
            ('never', _('Never')),
        ],
        default='monthly'
    )
    
    last_reset = models.DateTimeField(_('Last reset'), null=True, blank=True)
    next_reset = models.DateTimeField(_('Next reset'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Usage Limit')
        verbose_name_plural = _('Usage Limits')
        unique_together = ['subscription', 'limit_type']
        
    def __str__(self):
        return f"{self.subscription} - {self.get_limit_type_display()}: {self.current_usage}/{self.limit_value}"
    
    @property
    def usage_percentage(self):
        """Calculate usage percentage."""
        if self.limit_value == 0:
            return 0
        return (self.current_usage / self.limit_value) * 100
    
    @property
    def is_limit_exceeded(self):
        """Check if limit is exceeded."""
        return self.current_usage >= self.limit_value
    
    def increment_usage(self, count=1):
        """Increment usage counter."""
        self.current_usage += count
        self.save(update_fields=['current_usage'])
    
    def reset_usage(self):
        """Reset usage counter."""
        self.current_usage = 0
        self.last_reset = models.timezone.now()
        self.save(update_fields=['current_usage', 'last_reset'])