from django.contrib import admin
from .models import WhatsAppInstance, WhatsAppGroup, WhatsAppContact, WhatsAppMessage, WhatsAppGroupParticipant


@admin.register(WhatsAppGroupParticipant)
class WhatsAppGroupParticipantAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'jid', 'phone_number', 'display_name', 'is_admin', 'is_super_admin', 'error_code', 'is_active']
    list_filter = ['group', 'is_admin', 'is_super_admin', 'is_active']
    search_fields = ['group__name', 'jid', 'phone_number', 'display_name']
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ['is_admin', 'is_super_admin', 'is_active']
    list_display_links = ['id', 'group', 'jid', 'phone_number', 'display_name']
    list_select_related = ['group']
    ordering = ['group__name', 'jid', 'phone_number', 'display_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['group__name', 'jid', 'phone_number', 'display_name']
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ['is_admin', 'is_super_admin', 'is_active']
    list_display_links = ['id', 'group', 'jid', 'phone_number', 'display_name']
    list_select_related = ['group']
    ordering = ['group__name', 'jid', 'phone_number', 'display_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

admin.site.register(WhatsAppInstance)
admin.site.register(WhatsAppGroup)
admin.site.register(WhatsAppContact)
admin.site.register(WhatsAppMessage)


