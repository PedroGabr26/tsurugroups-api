"""
WhatsApp integration models for Tsuru Groups.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
import uuid


class WhatsAppInstance(models.Model):
    """WhatsApp instance for each user."""

    STATUS_CHOICES = [
        ("disconnected", _("Disconnected")),
        ("connecting", _("Connecting")),
        ("connected", _("Connected")),
        ("error", _("Error")),
        ("qr_code", _("QR Code Required")),
        ("pairing_code", _("Pairing Code Required")),
    ]

    CONNECTION_METHOD_CHOICES = [
        ("qr_code", _("QR Code")),
        ("pairing_code", _("Pairing Code")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="whatsapp_instance",
        verbose_name=_("User"),
    )

    # Instance configuration
    name = models.CharField(_("Instance name"), max_length=100)
    system_name = models.CharField(_("System name"), max_length=100, unique=True)
    whatsapp_number = models.CharField(
        _("WhatsApp number"),
        max_length=20,
        help_text=_("Number to be connected to WhatsApp (with country code)"),
        blank=True,
        null=True,
    )

    # API configuration (hidden from users, uses settings defaults)
    gateway_url = models.URLField(_("Gateway URL"), blank=True)
    api_key = models.CharField(_("API Key"), max_length=255, blank=True)

    # Connection status
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default="disconnected"
    )

    phone_number = models.CharField(
        _("Phone number"),
        max_length=20,
        blank=True,
        help_text=_("Connected WhatsApp number"),
    )

    # Connection method and data
    connection_method = models.CharField(
        _("Connection method"),
        max_length=20,
        choices=CONNECTION_METHOD_CHOICES,
        default="qr_code",
        help_text=_("Method used to connect WhatsApp"),
    )

    # QR Code for connection
    qr_code = models.TextField(_("QR Code"), blank=True)
    qr_code_expires_at = models.DateTimeField(
        _("QR Code expires at"), null=True, blank=True
    )

    # Pairing code for connection
    pairing_code = models.CharField(
        _("Pairing code"),
        max_length=10,
        blank=True,
        help_text=_("Code received on WhatsApp for pairing"),
    )

    # Connection info
    last_connected_at = models.DateTimeField(
        _("Last connected at"), null=True, blank=True
    )
    last_disconnected_at = models.DateTimeField(
        _("Last disconnected at"), null=True, blank=True
    )

    # Settings
    is_active = models.BooleanField(_("Is active"), default=True)
    webhook_url = models.URLField(_("Webhook URL"), blank=True)

    # Statistics
    messages_sent = models.PositiveIntegerField(_("Messages sent"), default=0)
    messages_received = models.PositiveIntegerField(_("Messages received"), default=0)

    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("WhatsApp Instance")
        verbose_name_plural = _("WhatsApp Instances")

    def __str__(self):
        return f"{self.user.full_name} - {self.name}"

    @property
    def is_connected(self):
        """Check if instance is connected."""
        return self.status == "connected"

    def save(self, *args, **kwargs):
        """Generate system name and set default API config if not provided."""
        if not self.system_name:
            self.system_name = f"tsuru_{self.user.id}_{uuid.uuid4().hex[:8]}"

        # Always use default settings from configuration
        self.gateway_url = getattr(settings, "DEFAULT_GATEWAY_URL", "")
        # self.api_key = getattr(settings, 'DEFAULT_UAZAPI_API_KEY', '')

        super().save(*args, **kwargs)


class WhatsAppGroup(models.Model):
    """WhatsApp groups managed by the user."""

    whatsapp_instance = models.ForeignKey(
        WhatsAppInstance,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name=_("WhatsApp Instance"),
    )

    # Group information
    group_id = models.CharField(_("Group ID"), max_length=255)
    name = models.CharField(_("Group name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)

    # Group metadata
    participant_count = models.PositiveIntegerField(_("Participant count"), default=0)
    is_admin = models.BooleanField(_("Is admin"), default=False)

    # Owner information
    owner_jid = models.CharField(_("Owner JID"), max_length=255, blank=True)
    owner_phone_number = models.CharField(_("Owner phone number"), max_length=50, blank=True)

    # Group settings from API
    is_locked = models.BooleanField(_("Is locked"), default=False)
    is_announce = models.BooleanField(_("Is announce only"), default=False)
    is_ephemeral = models.BooleanField(_("Is ephemeral"), default=False)
    disappearing_timer = models.PositiveIntegerField(_("Disappearing timer"), default=0)
    is_join_approval_required = models.BooleanField(_("Join approval required"), default=False)

    # Group creation info
    group_created = models.DateTimeField(_("Group created"), null=True, blank=True)
    creator_country_code = models.CharField(_("Creator country code"), max_length=5, blank=True)

    # Version IDs for tracking changes
    announce_version_id = models.CharField(_("Announce version ID"), max_length=100, blank=True)
    participant_version_id = models.CharField(_("Participant version ID"), max_length=100, blank=True)

    # Group settings
    invite_link = models.URLField(_("Invite link"), blank=True)
    member_add_mode = models.CharField(_("Member add mode"), max_length=50, default="all_member_add")

    # Status
    is_active = models.BooleanField(_("Is active"), default=True)

    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    last_synced_at = models.DateTimeField(_("Last synced at"), null=True, blank=True)

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("WhatsApp Group")
        verbose_name_plural = _("WhatsApp Groups")
        unique_together = ["whatsapp_instance", "group_id"]

    def __str__(self):
        return f"{self.name} ({self.whatsapp_instance.user.full_name})"


class WhatsAppGroupParticipant(models.Model):
    """Participants of WhatsApp groups."""

    group = models.ForeignKey(
        WhatsAppGroup,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name=_("Group"),
    )

    # Participant information
    jid = models.CharField(_("JID"), max_length=255)
    phone_number = models.CharField(_("Phone number"), max_length=50, blank=True)
    lid = models.CharField(_("LID"), max_length=100, blank=True)
    display_name = models.CharField(_("Display name"), max_length=200, blank=True)

    # Participant permissions
    is_admin = models.BooleanField(_("Is admin"), default=False)
    is_super_admin = models.BooleanField(_("Is super admin"), default=False)

    # Status
    error_code = models.PositiveIntegerField(_("Error code"), default=0)
    is_active = models.BooleanField(_("Is active"), default=True)

    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("WhatsApp Group Participant")
        verbose_name_plural = _("WhatsApp Group Participants")
        unique_together = ["group", "jid"]

    def __str__(self):
        return f"{self.display_name or self.phone_number} in {self.group.name}"


class WhatsAppContact(models.Model):
    """WhatsApp contacts for the user."""

    whatsapp_instance = models.ForeignKey(
        WhatsAppInstance,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name=_("WhatsApp Instance"),
    )

    # Contact information
    phone_number = models.CharField(_("Phone number"), max_length=20)
    name = models.CharField(_("Name"), max_length=200, blank=True)

    # Contact metadata
    is_business = models.BooleanField(_("Is business"), default=False)
    profile_picture_url = models.URLField(_("Profile picture URL"), blank=True)

    # Status
    is_blocked = models.BooleanField(_("Is blocked"), default=False)
    is_active = models.BooleanField(_("Is active"), default=True)

    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    last_seen_at = models.DateTimeField(_("Last seen at"), null=True, blank=True)

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("WhatsApp Contact")
        verbose_name_plural = _("WhatsApp Contacts")
        unique_together = ["whatsapp_instance", "phone_number"]

    def __str__(self):
        return f"{self.name or self.phone_number} ({self.whatsapp_instance.user.full_name})"




class WhatsAppMessage(models.Model):
    """WhatsApp messages log."""

    MESSAGE_TYPES = [
        ("text", _("Text")),
        ("image", _("Image")),
        ("video", _("Video")),
        ("audio", _("Audio")),
        ("document", _("Document")),
        ("sticker", _("Sticker")),
        ("location", _("Location")),
        ("contact", _("Contact")),
        ("menu", _("Menu")),
        ("poll", _("Poll")),
        ("list", _("List")),
    ]

    DIRECTION_CHOICES = [
        ("inbound", _("Inbound")),
        ("outbound", _("Outbound")),
    ]

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("sent", _("Sent")),
        ("delivered", _("Delivered")),
        ("read", _("Read")),
        ("failed", _("Failed")),
    ]

    whatsapp_instance = models.ForeignKey(
        WhatsAppInstance,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("WhatsApp Instance"),
    )

    # Message identification
    message_id = models.CharField(_("Message ID"), max_length=255, unique=True)

    # Message content
    message_type = models.CharField(
        _("Message type"), max_length=20, choices=MESSAGE_TYPES
    )
    content = models.TextField(_("Content"))

    # Sender/Recipient
    direction = models.CharField(
        _("Direction"), max_length=10, choices=DIRECTION_CHOICES
    )
    phone_number = models.CharField(_("Phone number"), max_length=20)
    contact_name = models.CharField(_("Contact name"), max_length=200, blank=True)

    # Group information (if applicable)
    group = models.ForeignKey(
        WhatsAppGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
        verbose_name=_("Group"),
    )

    # Message status
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default="pending"
    )       

    # Media information
    media_url = models.URLField(_("Media URL"), blank=True)
    media_type = models.CharField(_("Media type"), max_length=50, blank=True)
    media_size = models.PositiveIntegerField(_("Media size"), null=True, blank=True)

    # Timestamps
    sent_at = models.DateTimeField(_("Sent at"))
    delivered_at = models.DateTimeField(_("Delivered at"), null=True, blank=True)
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)




class WhatsAppCampaign(models.Model):
    name = models.CharField(max_length=200)
    whatsapp_instance = models.ForeignKey(
        WhatsAppInstance, on_delete=models.CASCADE, related_name="campaigns"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campaigns"
    )
    message_content = models.TextField()
    target_contacts = models.ManyToManyField(WhatsAppContact, related_name="campaigns")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name