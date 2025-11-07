"""
URL patterns for WhatsApp app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'whatsapp'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'instances', views.WhatsAppInstanceViewSet, basename='whatsappinstance')
router.register(r'groups', views.WhatsAppGroupViewSet, basename='whatsappgroup')
router.register(r'contacts', views.WhatsAppContactViewSet, basename='whatsappcontact')
router.register(r'messages', views.WhatsAppMessageViewSet, basename='whatsappmessage')
router.register(r'instance', views.AllWhatsappInstanceActivateView, basename='allinstances')

urlpatterns = [
    # Instance management endpoints
    path('instances/<uuid:pk>/connect/', views.ConnectInstanceView.as_view(), name='connect_instance'),
    path('instances/<uuid:pk>/disconnect/', views.DisconnectInstanceView.as_view(), name='disconnect_instance'),
    path('instances/<uuid:pk>/status/', views.InstanceStatusView.as_view(), name='instance_status'),
    path('instances/<uuid:pk>/qr-code/', views.QRCodeView.as_view(), name='qr_code'),

    
    # Sync endpoints
    path('instances/<uuid:pk>/sync-groups/', views.SyncGroupsView.as_view(), name='sync_groups'),
    path('instances/<uuid:pk>/sync-contacts/', views.SyncContactsView.as_view(), name='sync_contacts'),
    path('instances/<uuid:pk>/sync-status/', views.SyncStatusView.as_view(), name='sync_status'),
    
    # Message sending endpoints (API)
    path('send/text/', views.SendTextMessageView.as_view(), name='send_text'),
    path('send/media/', views.SendMediaMessageView.as_view(), name='send_media'),
    path('send/location/', views.SendLocationMessageView.as_view(), name='send_location'),
    path('send/contact/', views.SendContactMessageView.as_view(), name='send_contact'),
    path('send/menu/', views.SendMenuMessageView.as_view(), name='send_menu'),
    
    # WhatsApp connection management
    path('connect/', views.whatsapp_connect_view, name='connect'),
    path('instances/', views.whatsapp_instances_list_view, name='instances_list'),
    
    # Web pages for message sending and scheduling
    path('send-message/', views.send_message_view, name='send_message'),
    path('schedule-message/', views.schedule_message_view, name='schedule_message'),
    path('scheduled-messages/', views.scheduled_messages_list_view, name='scheduled_messages_list'),
    path('scheduled-messages/<uuid:message_id>/cancel/', views.cancel_scheduled_message, name='cancel_scheduled_message'),
    
    # AJAX endpoints
    path('ajax/get-recipients/', views.get_recipients_ajax, name='get_recipients_ajax'),
    path('ajax/get-qr-code/', views.get_qr_code_ajax, name='get_qr_code_ajax'),
    path('ajax/sync-data/<uuid:pk>/', views.sync_whatsapp_data_ajax, name='sync_data_ajax'),
    
    # Webhook endpoint
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
    path('webhook/setup/', views.SetupWebhookView.as_view(), name='setup_webhook'),
    
    # Bulk operations
    path('bulk/send/', views.BulkSendView.as_view(), name='bulk_send'),
    path('bulk/validate-numbers/', views.ValidateNumbersView.as_view(), name='validate_numbers'),
    
    # Group management
    path('groups/', views.groups_list_view, name='groups_list'),
    path('groups/<int:pk>/members/', views.GroupMembersView.as_view(), name='group_members'),
    path('groups/<int:pk>/invite-link/', views.GroupInviteLinkView.as_view(), name='group_invite_link'),
    # path('groups/alls/', views.AllWhatsappGroupViewSet.as_view(), name='all_groups'),
    
    
    # Statistics
    path('stats/dashboard/', views.WhatsAppStatsView.as_view(), name='whatsapp_stats'),
    path('stats/messages/', views.MessageStatsView.as_view(), name='message_stats'),

    # Instance Activate
    path('instances/active/', views.WhatsappInstanceActivateView.as_view(), name='active_instances'),
    path('all/groups/', views.ActiveGroupsView.as_view(), name='groups_active'),
    path('all/contacts/',views.ActivateContatsInstancesView.as_view(), name='contats_active'),

    # CONFIGURAR URLS RESTANTES
    # path('settings/groups', views.SettingsWhatsappGroupsViews.as_view(), name='settinggs_groups'),
    # path('groups/mention/', views.MentionParticipantsView.as_view(), name="mention_participants"),
    path('dashboard/summary/', views.dashboard_summary, name='dashboard_summary'),
    path('instances/details/', views.get_instances_details, name='details_instances'),
    path('campaigns/', views.campaings_details, name='details_campaings'),
    # Router URLs
    path('', include(router.urls)),
]