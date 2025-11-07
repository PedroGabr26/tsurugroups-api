"""
Serializers for WhatsApp app.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import WhatsAppInstance, WhatsAppGroup, WhatsAppGroupParticipant, WhatsAppContact, WhatsAppMessage, WhatsAppCampaign


class WhatsAppInstanceSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp instances."""
    
    user = serializers.StringRelatedField(read_only=True)
    is_connected = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = WhatsAppInstance
        fields = [
            'id', 'user', 'name', 'system_name', 'whatsapp_number',
            'connection_method', 'status', 'phone_number', 'qr_code', 
            'qr_code_expires_at', 'pairing_code', 'last_connected_at', 
            'last_disconnected_at', 'is_active', 'webhook_url', 
            'messages_sent', 'messages_received', 'is_connected', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'system_name', 'status', 'phone_number', 
            'qr_code', 'qr_code_expires_at', 'pairing_code', 'last_connected_at',
            'last_disconnected_at', 'messages_sent', 'messages_received',
            'is_connected', 'created_at', 'updated_at'
        ]
        # Campos sensíveis são omitidos (gateway_url, api_key)
    
    def create(self, validated_data):
        """Create instance with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WhatsAppGroupParticipantSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp group participants."""
    
    class Meta:
        model = WhatsAppGroupParticipant
        fields = [
            'id', 'jid', 'phone_number', 'lid', 'display_name',
            'is_admin', 'is_super_admin', 'error_code', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]


class WhatsAppGroupSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp groups."""
    # Porque mudei o nome de instance para whatsapp_instance ?
    instance_name = serializers.CharField(source='whatsapp_instance.name', read_only=True)
    participants = WhatsAppGroupParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = WhatsAppGroup
        fields = [
            'id', 'whatsapp_instance', 'instance_name', 'group_id', 'name', 
            'description', 'participant_count', 'is_admin', 'owner_jid',
            'owner_phone_number', 'is_locked', 'is_announce', 'is_ephemeral',
            'disappearing_timer', 'is_join_approval_required', 'group_created',
            'creator_country_code', 'announce_version_id', 'participant_version_id',
            'invite_link', 'member_add_mode', 'is_active', 'participants',
            'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = [
            'id', 'instance_name', 'participant_count', 'is_admin', 'owner_jid',
            'owner_phone_number', 'is_locked', 'is_announce', 'is_ephemeral',
            'disappearing_timer', 'is_join_approval_required', 'group_created',
            'creator_country_code', 'announce_version_id', 'participant_version_id',
            'invite_link', 'member_add_mode', 'participants',
            'created_at', 'updated_at', 'last_synced_at'
        ]


class WhatsAppContactSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp contacts."""
    
    instance_name = serializers.CharField(source='whatsapp_instance.name', read_only=True)
    
    class Meta:
        model = WhatsAppContact
        fields = [
            'id', 'whatsapp_instance', 'instance_name', 'phone_number', 'name',
            'is_business', 'profile_picture_url', 'is_blocked', 'is_active',
            'created_at', 'updated_at', 'last_seen_at'
        ]
        read_only_fields = [
            'id', 'instance_name', 'is_business', 'profile_picture_url',
            'created_at', 'updated_at', 'last_seen_at'
        ]


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp messages."""
    
    instance_name = serializers.CharField(source='instance.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'instance', 'instance_name', 'message_id', 'message_type',
            'content', 'direction', 'phone_number', 'contact_name',
            'group', 'group_name', 'status', 'media_url', 'media_type',
            'media_size', 'sent_at', 'delivered_at', 'read_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'instance_name', 'group_name', 'delivered_at', 'read_at',
            'created_at', 'updated_at'
        ]


# Request/Response serializers for specific endpoints
class ConnectInstanceSerializer(serializers.Serializer):
    """Serializer for connecting WhatsApp instance."""
    
    CONNECTION_METHOD_CHOICES = [
        ('qr_code', 'QR Code'),
        ('pairing_code', 'Pairing Code'),
    ]
    
    connection_method = serializers.ChoiceField(
        choices=CONNECTION_METHOD_CHOICES,
        default='qr_code',
        help_text='Choose connection method: QR Code or Pairing Code'
    )


class SendTextMessageSerializer(serializers.Serializer):
    """Serializer for sending text messages."""
    
    instance_id = serializers.UUIDField()
    number = serializers.CharField(max_length=20)
    message = serializers.CharField()
    quote_id = serializers.CharField(required=False)


class SendMediaMessageSerializer(serializers.Serializer):
    """Serializer for sending media messages."""
    
    instance_id = serializers.UUIDField()
    number = serializers.CharField(max_length=20)
    message = serializers.CharField()
    media_url = serializers.URLField()
    media_type = serializers.ChoiceField(choices=[
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('sticker', 'Sticker')
    ])
    quote_id = serializers.CharField(required=False)


class SendLocationMessageSerializer(serializers.Serializer):
    """Serializer for sending location messages."""
    
    instance_id = serializers.UUIDField()
    number = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=200)
    address = serializers.CharField(max_length=500)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class SendContactMessageSerializer(serializers.Serializer):
    """Serializer for sending contact messages."""
    
    instance_id = serializers.UUIDField()
    number = serializers.CharField(max_length=20)
    contact_name = serializers.CharField(max_length=200)
    contact_number = serializers.CharField(max_length=20)


class SendMenuMessageSerializer(serializers.Serializer):
    """Serializer for sending menu messages."""
    
    instance_id = serializers.UUIDField()
    number = serializers.CharField(max_length=20)
    message = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())
    menu_type = serializers.ChoiceField(
        choices=[('list', 'List'), ('button', 'Button'), ('poll', 'Poll')],
        default='list'
    )


class BulkSendSerializer(serializers.Serializer):
    """Serializer for bulk sending messages."""
    
    instance_id = serializers.UUIDField()
    recipients = serializers.ListField(child=serializers.CharField())
    message = serializers.CharField()
    campaign_name = serializers.CharField(max_length=200, default='Bulk Campaign')
    delay_min = serializers.IntegerField(default=3, min_value=1)
    delay_max = serializers.IntegerField(default=6, min_value=1)


class ValidateNumbersSerializer(serializers.Serializer):
    """Serializer for validating WhatsApp numbers."""
    
    instance_id = serializers.UUIDField()
    numbers = serializers.ListField(child=serializers.CharField())


class WebhookSetupSerializer(serializers.Serializer):
    """Serializer for webhook setup."""
    
    instance_id = serializers.UUIDField()
    webhook_url = serializers.URLField()


class QRCodeSerializer(serializers.Serializer):
    """Serializer for QR code response."""
    
    qr_code = serializers.CharField()
    expires_at = serializers.DateTimeField()
    status = serializers.CharField()


class InstanceStatusSerializer(serializers.Serializer):
    """Serializer for instance status response."""
    
    status = serializers.CharField()
    phone_number = serializers.CharField(required=False)
    last_seen = serializers.DateTimeField(required=False)
    battery = serializers.IntegerField(required=False)


class WhatsAppStatsSerializer(serializers.Serializer):
    """Serializer for WhatsApp statistics."""
    
    total_instances = serializers.IntegerField()
    connected_instances = serializers.IntegerField()
    total_groups = serializers.IntegerField()
    total_contacts = serializers.IntegerField()
    messages_sent_today = serializers.IntegerField()
    messages_sent_this_month = serializers.IntegerField()
    success_rate = serializers.FloatField()


class MessageStatsSerializer(serializers.Serializer):
    """Serializer for message statistics."""
    
    date = serializers.DateField()
    messages_sent = serializers.IntegerField()
    messages_delivered = serializers.IntegerField()
    messages_read = serializers.IntegerField()
    messages_failed = serializers.IntegerField()
    success_rate = serializers.FloatField()


class GroupMembersSerializer(serializers.Serializer):
    """Serializer for group members."""
    
    members = serializers.ListField(child=serializers.DictField())
    total_count = serializers.IntegerField()
    admin_count = serializers.IntegerField()



class WhatsappCampaignSerializer(serializers.ModelSerializer):
    """Serializer para campanhas de WhatsApp."""

    # Campos extras de leitura
    instance_name = serializers.CharField(source='whatsapp_instance.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    target_contacts = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=WhatsAppContact.objects.all()
    )

    class Meta:
        model = WhatsAppCampaign
        fields = [
            'name', 'whatsapp_instance', 'created_by', 'message_content', 
            'target_contacts', 'scheduled_at', 'is_active','created_at', 'created_by_name','instance_name' 
        ]
        read_only_fields = [
            'id',
            'instance_name',
            'created_by_name',
            'created_at'
        ]   
    
    def create(self, validated_data):
        """Define o usuário criador automaticamente."""
        user = self.context['request'].user
        validated_data['created_by'] = user
        campaign = super().create(validated_data)
        return campaign
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context  