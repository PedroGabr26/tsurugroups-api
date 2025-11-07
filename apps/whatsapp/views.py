"""
Views for WhatsApp app.
"""
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import django_rq
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from django.utils.timezone import now


from .models import (
    WhatsAppInstance,
    WhatsAppGroup,
    WhatsAppGroupParticipant,
    WhatsAppContact,
    WhatsAppMessage,
    WhatsAppCampaign,
)
from .serializers import (
    WhatsAppInstanceSerializer,
    WhatsAppGroupSerializer,
    WhatsAppContactSerializer,
    WhatsAppMessageSerializer,
    ConnectInstanceSerializer,
    SendTextMessageSerializer,
    SendMediaMessageSerializer,
    SendLocationMessageSerializer,
    SendContactMessageSerializer,
    SendMenuMessageSerializer,
    BulkSendSerializer,
    ValidateNumbersSerializer,
    WebhookSetupSerializer,
    QRCodeSerializer,
    InstanceStatusSerializer,
    WhatsAppStatsSerializer,
    MessageStatsSerializer,
    GroupMembersSerializer,
    WhatsappCampaignSerializer,
)
from .services import WhatsAppAPIService, WhatsAppInstanceManager


class WhatsAppInstanceViewSet(viewsets.ModelViewSet):
    """ViewSet for WhatsApp instances."""

    serializer_class = WhatsAppInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WhatsAppInstance.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)

        # Create instance via API
        success, result = WhatsAppAPIService.create_instance(instance)
        if not success:
            instance.delete()
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def connect(self, request, pk=None):
        """Connect WhatsApp instance."""
        instance = self.get_object()
        serializer = ConnectInstanceSerializer(data=request.data)

        if serializer.is_valid():
            phone = serializer.validated_data.get("phone")
            success, result = WhatsAppAPIService.connect_instance(instance, phone)

            if success:
                instance.status = "connecting"
                instance.save()
                return Response({"message": "Connection initiated", "data": result})
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        """Disconnect WhatsApp instance."""
        instance = self.get_object()
        success, result = WhatsAppAPIService.disconnect_instance(instance)

        if success:
            instance.status = "disconnected"
            instance.last_disconnected_at = timezone.now()
            instance.save()
            return Response({"message": "Disconnected successfully"})
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Get instance status."""
        instance = self.get_object()
        WhatsAppInstanceManager.sync_instance_status(instance)

        serializer = InstanceStatusSerializer(
            {
                "status": instance.status,
                "phone_number": instance.phone_number,
                "last_seen": instance.last_connected_at,
            }
        ) 

        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def qr_code(self, request, pk=None):
        """Get QR code for connection."""
        instance = self.get_object()
        print("INSTANCE AQUII",)

        if instance.qr_code and instance.status == "qr_code":
            serializer = QRCodeSerializer(
                {
                    "qr_code": instance.qr_code,
                    "expires_at": instance.qr_code_expires_at,
                    "status": instance.status,
                }
            )
            return Response(serializer.data)

        return Response(
            {"error": "QR code not available"}, status=status.HTTP_404_NOT_FOUND
        )


class WhatsAppGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for WhatsApp groups."""

    serializer_class = WhatsAppGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WhatsAppGroup.objects.filter(
            instance__user=self.request.user
        ).select_related("instance")


class WhatsAppContactViewSet(viewsets.ModelViewSet):
    """ViewSet for WhatsApp contacts."""

    serializer_class = WhatsAppContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WhatsAppContact.objects.filter(
            instance__user=self.request.user
        ).select_related("instance")


class WhatsAppMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WhatsApp messages (read-only)."""

    serializer_class = WhatsAppMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            WhatsAppMessage.objects.filter(instance__user=self.request.user)
            .select_related("instance", "group")
            .order_by("-sent_at")
        )


class ConnectInstanceView(generics.GenericAPIView):
    """Connect WhatsApp instance."""

    serializer_class = ConnectInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            phone = serializer.validated_data.get("phone")
            success, result = WhatsAppAPIService.connect_instance(instance, phone)

            if success:
                instance.status = "connecting"
                instance.save()
                return Response({"message": "Connection initiated", "data": result})
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisconnectInstanceView(generics.GenericAPIView):
    """Disconnect WhatsApp instance."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)
        success, result = WhatsAppAPIService.disconnect_instance(instance)

        if success:
            instance.status = "disconnected"
            instance.last_disconnected_at = timezone.now()
            instance.save()
            return Response({"message": "Disconnected successfully"})
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class InstanceStatusView(generics.GenericAPIView):
    """Get instance status."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)
        WhatsAppInstanceManager.sync_instance_status(instance)

        serializer = InstanceStatusSerializer(
            {
                "status": instance.status,
                "phone_number": instance.phone_number,
                "last_seen": instance.last_connected_at,
            }
        )

        return Response(serializer.data)


class QRCodeView(generics.GenericAPIView):
    """Get QR code for connection."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)

        if instance.qr_code and instance.status == "qr_code":
            serializer = QRCodeSerializer(
                {
                    "qr_code": instance.qr_code,
                    "expires_at": instance.qr_code_expires_at,
                    "status": instance.status,
                }
            )
            return Response(serializer.data)

        return Response(
            {"error": "QR code not available"}, status=status.HTTP_404_NOT_FOUND
        )


class SyncGroupsView(generics.GenericAPIView):
    """Sync groups from WhatsApp API."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)

        if not instance.is_connected:
            return Response(
                {"error": "Instance is not connected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Queue sync task
        queue = django_rq.get_queue("default")
        job = queue.enqueue(
            "apps.scheduling.tasks.sync_whatsapp_groups", str(instance.id)
        )

        return Response({"message": "Group sync queued", "job_id": job.id})


class SyncContactsView(generics.GenericAPIView):
    """Sync contacts from WhatsApp API."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)

        if not instance.is_connected:
            return Response(
                {"error": "Instance is not connected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Queue sync task
        queue = django_rq.get_queue("default")
        job = queue.enqueue(
            "apps.scheduling.tasks.sync_whatsapp_contacts", str(instance.id)
        )

        return Response({"message": "Contact sync queued", "job_id": job.id})


class SyncStatusView(generics.GenericAPIView):
    """Sync instance status."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        instance = get_object_or_404(WhatsAppInstance, pk=pk, user=request.user)

        # Queue sync task
        queue = django_rq.get_queue("default")
        job = queue.enqueue(
            "apps.scheduling.tasks.sync_whatsapp_instance_status", str(instance.id)
        )

        return Response({"message": "Status sync queued", "job_id": job.id})


class SendTextMessageView(generics.GenericAPIView):
    """Send text message."""

    serializer_class = SendTextMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            instance = get_object_or_404(
                WhatsAppInstance,
                pk=serializer.validated_data["instance_id"],
                user=request.user,
            )

            success, result = WhatsAppAPIService.send_text_message(
                instance=instance,
                number=serializer.validated_data["number"],
                message=serializer.validated_data["message"],
                quote_id=serializer.validated_data.get("quote_id"),
            )

            if success:
                return Response(
                    {"message": "Message sent successfully", "data": result}
                )
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendMediaMessageView(generics.GenericAPIView):
    """Send media message."""

    serializer_class = SendMediaMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            instance = get_object_or_404(
                WhatsAppInstance,
                pk=serializer.validated_data["instance_id"],
                user=request.user,
            )

            success, result = WhatsAppAPIService.send_media_message(
                instance=instance,
                number=serializer.validated_data["number"],
                message=serializer.validated_data["message"],
                media_url=serializer.validated_data["media_url"],
                media_type=serializer.validated_data["media_type"],
                quote_id=serializer.validated_data.get("quote_id"),
            )

            if success:
                return Response(
                    {"message": "Media message sent successfully", "data": result}
                )
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendLocationMessageView(generics.GenericAPIView):
    """Send location message."""

    serializer_class = SendLocationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            instance = get_object_or_404(
                WhatsAppInstance,
                pk=serializer.validated_data["instance_id"],
                user=request.user,
            )

            result = WhatsAppAPIService.send_location_message(
                instance=instance,
                number=serializer.validated_data["number"],
                name=serializer.validated_data["name"],
                address=serializer.validated_data["address"],
                latitude=serializer.validated_data["latitude"],
                longitude=serializer.validated_data["longitude"],
            )

            if "error" not in result:
                return Response(
                    {"message": "Location sent successfully", "data": result}
                )
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendContactMessageView(generics.GenericAPIView):
    """Send contact message."""

    serializer_class = SendContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            instance = get_object_or_404(
                WhatsAppInstance,
                pk=serializer.validated_data["instance_id"],
                user=request.user,
            )

            result = WhatsAppAPIService.send_contact_message(
                instance=instance,
                number=serializer.validated_data["number"],
                contact_name=serializer.validated_data["contact_name"],
                contact_number=serializer.validated_data["contact_number"],
            )

            if "error" not in result:
                return Response(
                    {"message": "Contact sent successfully", "data": result}
                )
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendMenuMessageView(generics.GenericAPIView):
    """Send menu message."""

    serializer_class = SendMenuMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            instance = get_object_or_404(
                WhatsAppInstance,
                pk=serializer.validated_data["instance_id"],
                user=request.user,
            )

            success, result = WhatsAppAPIService.send_menu_message(
                instance=instance,
                number=serializer.validated_data["number"],
                message=serializer.validated_data["message"],
                options=serializer.validated_data["options"],
                menu_type=serializer.validated_data["menu_type"],
            )

            if success:
                return Response({"message": "Menu sent successfully", "data": result})
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkSendView(generics.GenericAPIView):
    """Send bulk messages."""

    serializer_class = BulkSendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            instance = get_object_or_404(
                WhatsAppInstance,
                pk=serializer.validated_data["instance_id"],
                user=request.user,
            )

            result = WhatsAppAPIService.send_bulk_message(
                instance=instance,
                recipients=serializer.validated_data["recipients"],
                message=serializer.validated_data["message"],
                campaign_name=serializer.validated_data["campaign_name"],
                delay_min=serializer.validated_data["delay_min"],
                delay_max=serializer.validated_data["delay_max"],
            )

            if "error" not in result:
                return Response(
                    {"message": "Bulk message sent successfully", "data": result}
                )
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebhookView(generics.GenericAPIView):
    """Webhook view."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # TODO: Implement webhook view
        return Response({"message": "Webhook received"})


class SetupWebhookView(generics.GenericAPIView):
    """Setup webhook view."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # TODO: Implement setup webhook view
        return Response({"message": "Webhook setup received"})


class ValidateNumbersView(generics.GenericAPIView):
    """Validate numbers view."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # TODO: Implement validate numbers view
        return Response({"message": "Numbers validated"})


class GroupMembersView(generics.GenericAPIView):
    """Group members view."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # TODO: Implement group members view
        return Response({"message": "Group members received"})


class GroupInviteLinkView(generics.GenericAPIView):
    """Group invite link view."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # TODO: Implement group invite link view
        return Response({"message": "Group invite link received"})


class WhatsAppStatsView(generics.GenericAPIView):
    """WhatsApp stats view."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # TODO: Implement WhatsApp stats view
        return Response({"message": "WhatsApp stats received"})


class MessageStatsView(generics.GenericAPIView):
    """Message stats view."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # TODO: Implement message stats view
        return Response({"message": "Message stats received"})


# Web Views for message sending and scheduling
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from apps.scheduling.models import MessageTemplate, ScheduledMessage
from django import forms
import json


class SendMessageForm(forms.Form):
    """Formulário para envio de mensagens."""

    MESSAGE_TYPES = [
        ("text", "Texto"),
        ("image", "Imagem"),
        ("video", "Vídeo"),
        ("audio", "Áudio"),
        ("document", "Documento"),
    ]

    RECIPIENT_TYPES = [
        ("groups", "Grupos"),
        ("contacts", "Contatos"),
        ("numbers", "Números"),
    ]

    whatsapp_instance = forms.ModelChoiceField(
        queryset=None,
        empty_label="Selecione uma instância",
        label="Instância WhatsApp",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPES,
        label="Tipo de mensagem",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_TYPES,
        label="Tipo de destinatário",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    message_content = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Digite sua mensagem aqui...",
            }
        ),
        label="Mensagem",
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Grupos",
    )

    contacts = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Contatos",
    )

    phone_numbers = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Digite os números separados por linha\nEx: 5511999999999",
            }
        ),
        label="Números de telefone",
    )

    media_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
        label="Arquivo de mídia",
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["whatsapp_instance"].queryset = WhatsAppInstance.objects.filter(
            user=user
        )
        self.fields["groups"].queryset = WhatsAppGroup.objects.filter(
            whatsapp_instance__user=user
        )
        self.fields["contacts"].queryset = WhatsAppContact.objects.filter(
            whatsapp_instance__user=user
        )


class ScheduleMessageForm(forms.ModelForm):
    """Formulário para agendamento de mensagens."""

    class Meta:
        model = ScheduledMessage
        fields = [
            "name",
            "description",
            "whatsapp_instance",
            "message_content",
            "recipient_type",
            "groups",
            "contacts",
            "schedule_date",
            "schedule_time",
            "delay_min",
            "delay_max",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "whatsapp_instance": forms.Select(attrs={"class": "form-select"}),
            "message_content": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "recipient_type": forms.Select(attrs={"class": "form-select"}),
            "groups": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "contacts": forms.CheckboxSelectMultiple(
                attrs={"class": "form-check-input"}
            ),
            "schedule_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "schedule_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "delay_min": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "delay_max": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    phone_numbers = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Digite os números separados por linha\nEx: 5511999999999",
            }
        ),
        label="Números de telefone",
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["whatsapp_instance"].queryset = WhatsAppInstance.objects.filter(
            user=user
        )
        self.fields["groups"].queryset = WhatsAppGroup.objects.filter(
            whatsapp_instance__user=user
        )
        self.fields["contacts"].queryset = WhatsAppContact.objects.filter(
            whatsapp_instance__user=user
        )


@login_required
def send_message_view(request):
    """View para página de envio de mensagens."""

    if request.method == "POST":
        form = SendMessageForm(request.user, request.POST, request.FILES)

        if form.is_valid():
            try:
                instance = form.cleaned_data["whatsapp_instance"]
                message_type = form.cleaned_data["message_type"]
                recipient_type = form.cleaned_data["recipient_type"]
                message_content = form.cleaned_data["message_content"]

                # Verificar se a instância está conectada
                if not instance.is_connected:
                    messages.error(request, "A instância WhatsApp não está conectada.")
                    return render(request, "whatsapp/send_message.html", {"form": form})

                recipients = []

                # Coletar destinatários baseado no tipo
                if recipient_type == "groups":
                    groups = form.cleaned_data["groups"]
                    for group in groups:
                        recipients.append(group.group_id)

                elif recipient_type == "contacts":
                    contacts = form.cleaned_data["contacts"]
                    for contact in contacts:
                        recipients.append(contact.phone_number)

                elif recipient_type == "numbers":
                    phone_numbers = form.cleaned_data["phone_numbers"]
                    if phone_numbers:
                        numbers = [
                            num.strip()
                            for num in phone_numbers.split("\n")
                            if num.strip()
                        ]
                        recipients.extend(numbers)

                if not recipients:
                    messages.error(request, "Selecione pelo menos um destinatário.")
                    return render(request, "whatsapp/send_message.html", {"form": form})

                # Enviar mensagens
                success_count = 0
                error_count = 0

                for recipient in recipients:
                    try:
                        if message_type == "text":
                            success, result = WhatsAppAPIService.send_text_message(
                                instance=instance,
                                number=recipient,
                                message=message_content,
                            )
                        else:
                            # Para mídia, implementar upload e envio
                            media_file = form.cleaned_data.get("media_file")
                            if media_file:
                                # TODO: Implementar upload de mídia
                                success = False
                                result = {
                                    "error": "Upload de mídia não implementado ainda"
                                }
                            else:
                                success = False
                                result = {"error": "Arquivo de mídia obrigatório"}

                        if success:
                            success_count += 1
                        else:
                            error_count += 1

                    except Exception as e:
                        error_count += 1

                if success_count > 0:
                    messages.success(
                        request, f"{success_count} mensagem(ns) enviada(s) com sucesso!"
                    )

                if error_count > 0:
                    messages.warning(
                        request, f"{error_count} mensagem(ns) falharam no envio."
                    )

                return redirect("whatsapp:send_message")

            except Exception as e:
                messages.error(request, f"Erro ao enviar mensagem: {str(e)}")

    else:
        form = SendMessageForm(request.user)

    context = {
        "form": form,
        "page_title": "Enviar Mensagem",
    }

    return render(request, "whatsapp/send_message.html", context)


@login_required
def schedule_message_view(request):
    """View para página de agendamento de mensagens."""

    if request.method == "POST":
        form = ScheduleMessageForm(request.user, request.POST)

        if form.is_valid():
            try:
                scheduled_message = form.save(commit=False)
                scheduled_message.user = request.user

                # Verificar se a instância está conectada
                if not scheduled_message.whatsapp_instance.is_connected:
                    messages.error(request, "A instância WhatsApp não está conectada.")
                    return render(
                        request, "whatsapp/schedule_message.html", {"form": form}
                    )

                scheduled_message.save()

                # Adicionar destinatários
                recipient_type = form.cleaned_data["recipient_type"]
                total_recipients = 0

                if recipient_type == "groups":
                    groups = form.cleaned_data["groups"]
                    scheduled_message.groups.set(groups)
                    total_recipients = sum(group.participant_count for group in groups)

                elif recipient_type == "contacts":
                    contacts = form.cleaned_data["contacts"]
                    scheduled_message.contacts.set(contacts)
                    total_recipients = contacts.count()

                elif recipient_type == "mixed":
                    groups = form.cleaned_data["groups"]
                    contacts = form.cleaned_data["contacts"]
                    scheduled_message.groups.set(groups)
                    scheduled_message.contacts.set(contacts)
                    total_recipients = (
                        sum(group.participant_count for group in groups)
                        + contacts.count()
                    )

                # Adicionar números avulsos se fornecidos
                phone_numbers = form.cleaned_data.get("phone_numbers")
                if phone_numbers:
                    numbers = [
                        num.strip() for num in phone_numbers.split("\n") if num.strip()
                    ]
                    total_recipients += len(numbers)
                    # TODO: Criar contatos temporários ou armazenar números separadamente

                scheduled_message.total_recipients = total_recipients
                scheduled_message.status = "scheduled"
                scheduled_message.save()

                messages.success(
                    request,
                    f"Mensagem agendada com sucesso para {total_recipients} destinatário(s)!",
                )
                return redirect("whatsapp:schedule_message")

            except Exception as e:
                messages.error(request, f"Erro ao agendar mensagem: {str(e)}")

    else:
        form = ScheduleMessageForm(request.user)

    # Buscar mensagens agendadas do usuário
    scheduled_messages = ScheduledMessage.objects.filter(user=request.user).order_by(
        "-created_at"
    )[:10]

    context = {
        "form": form,
        "scheduled_messages": scheduled_messages,
        "page_title": "Agendar Mensagem",
    }

    return render(request, "whatsapp/schedule_message.html", context)


@login_required
def scheduled_messages_list_view(request):
    """View para listar mensagens agendadas."""

    scheduled_messages = (
        ScheduledMessage.objects.filter(user=request.user)
        .select_related("whatsapp_instance")
        .order_by("-created_at")
    )

    context = {
        "scheduled_messages": scheduled_messages,
        "page_title": "Mensagens Agendadas",
    }

    return render(request, "whatsapp/scheduled_messages_list.html", context)


@login_required
@require_http_methods(["POST"])
def cancel_scheduled_message(request, message_id):
    """Cancelar mensagem agendada."""

    try:
        scheduled_message = ScheduledMessage.objects.get(
            id=message_id, user=request.user
        )

        if scheduled_message.can_be_cancelled:
            scheduled_message.status = "cancelled"
            scheduled_message.save()

            messages.success(request, "Mensagem agendada cancelada com sucesso!")
        else:
            messages.error(request, "Esta mensagem não pode ser cancelada.")

    except ScheduledMessage.DoesNotExist:
        messages.error(request, "Mensagem agendada não encontrada.")
    except Exception as e:
        messages.error(request, f"Erro ao cancelar mensagem: {str(e)}")

    return redirect("whatsapp:scheduled_messages_list")


@login_required
def get_recipients_ajax(request):
    """AJAX endpoint para buscar destinatários baseado na instância."""

    instance_id = request.GET.get("instance_id")
    recipient_type = request.GET.get("type")

    if not instance_id:
        return JsonResponse({"error": "Instance ID obrigatório"}, status=400)

    try:
        instance = WhatsAppInstance.objects.get(id=instance_id, user=request.user)

        if recipient_type == "groups":
            groups = list(
                instance.groups.filter(is_active=True).values(
                    "id", "name", "participant_count"
                )
            )
            return JsonResponse({"groups": groups})

        elif recipient_type == "contacts":
            contacts = list(
                instance.contacts.filter(is_active=True).values(
                    "id", "name", "phone_number"
                )
            )
            return JsonResponse({"contacts": contacts})

        else:
            return JsonResponse({"error": "Tipo de destinatário inválido"}, status=400)

    except WhatsAppInstance.DoesNotExist:
        return JsonResponse({"error": "Instância não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# WhatsApp Connection Management Views
class WhatsAppInstanceForm(forms.ModelForm):
    """Formulário para criar/editar instâncias WhatsApp."""

    class Meta:
        model = WhatsAppInstance
        fields = ["name", "whatsapp_number", "connection_method"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Meu WhatsApp Business",
                }
            ),
            "whatsapp_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: 5511999999999"}
            ),
            "connection_method": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "name": "Nome da Instância",
            "whatsapp_number": "Número do WhatsApp",
            "connection_method": "Método de Conexão",
        }
        help_texts = {
            "name": "Nome para identificar sua instância WhatsApp",
            "whatsapp_number": "Número do WhatsApp que será conectado (com código do país)",
            "connection_method": "Escolha como deseja conectar: QR Code ou Código no WhatsApp",
        }


@login_required
def whatsapp_connect_view(request):
    """View principal para conectar WhatsApp."""

    # Buscar instâncias existentes do usuário
    instances = WhatsAppInstance.objects.filter(user=request.user)
    current_instances_count = instances.count()
    
    # Verificar limites do plano do usuário
    max_instances = 1  # Default para usuários sem plano
    subscription = request.user.current_subscription
    
    if subscription and subscription.is_active:
        max_instances = subscription.plan.max_whatsapp_instances
    
    can_create_more = current_instances_count < max_instances
    
    new_instance = request.GET.get("instance") == "new"
    instance = instances.first() if instances.exists() and not new_instance else None
    instance_exists = instance is not None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_instance":
            # Verificar se o usuário pode criar mais instâncias
            if not can_create_more and not instance_exists:
                messages.error(
                    request, 
                    f"Você atingiu o limite de {max_instances} instância(s) do seu plano. "
                    f"Faça upgrade do seu plano para criar mais instâncias."
                )
                return redirect("whatsapp:connect")
            
            form = WhatsAppInstanceForm(request.POST, instance=instance)

            if form.is_valid():
                try:
                    if instance_exists:
                        # Atualizar instância existente
                        for field in form.cleaned_data:
                            setattr(instance, field, form.cleaned_data[field])
                        instance.save()
                        messages.success(
                            request, "Instância WhatsApp atualizada com sucesso!"
                        )
                    else:
                        # Criar nova instância
                        instance = form.save(commit=False)
                        instance.user = request.user
                        instance.save()
                        messages.success(
                            request, "Instância WhatsApp criada com sucesso!"
                        )

                    # Tentar criar a instância na API
                    success, result = WhatsAppAPIService.create_instance(instance)
                    if not success:
                        messages.warning(
                            request,
                            f'Instância salva localmente, mas houve erro na API: {result.get("error", "Erro desconhecido")}',
                        )
                    if success:
                        instance.api_key = result.get("token", "")
                        instance.save()

                    return redirect("whatsapp:connect")

                except Exception as e:
                    messages.error(request, f"Erro ao salvar instância: {str(e)}")

        elif action == "connect" and instance:
            try:
                print("CONNECTING INSTANCE", instance)
                success, result = WhatsAppAPIService.connect_instance(instance)

                if success:
                    instance.status = "connecting"
                    instance_data =  result.get("instance", {})
                    if instance_data and instance_data.get('status') == 'connecting' and instance_data.get("paircode"):
                        instance.pairing_code = instance_data.get("paircode")
                        instance.status = "pairing_code"
                    instance.save()
                    messages.success(
                        request, "Processo de conexão iniciado! Escaneie o QR Code."
                    )
                else:
                    messages.error(
                        request,
                        f'Erro ao conectar: {result.get("error", "Erro desconhecido")}',
                    )

            except Exception as e:
                messages.error(request, f"Erro ao conectar: {str(e)}")

        elif action == "disconnect" and instance:
            try:
                success, result = WhatsAppInstanceManager.disconnect_instance(instance)

                if success:
                    instance.status = "disconnected"
                    instance.phone_number = ""
                    instance.qr_code = ""
                    instance.last_disconnected_at = timezone.now()
                    instance.save()
                    messages.success(request, "WhatsApp desconectado com sucesso!")
                else:
                    messages.error(
                        request,
                        f'Erro ao desconectar: {result.get("error", "Erro desconhecido")}',
                    )

            except Exception as e:
                messages.error(request, f"Erro ao desconectar: {str(e)}")

        elif action == "delete" and instance:
            try:
                # Tentar deletar da API primeiro
                result = WhatsAppAPIService.delete_instance(instance)

                # Deletar localmente independente do resultado da API
                instance.delete()
                messages.success(request, "Instância WhatsApp removida com sucesso!")

                return redirect("whatsapp:connect")

            except Exception as e:
                messages.error(request, f"Erro ao remover instância: {str(e)}")

    # Atualizar status se instância existe
    if instance:
        try:
            WhatsAppInstanceManager.sync_instance_status(instance)
        except:
            pass  # Ignorar erros de sincronização

    # Preparar formulário
    if instance_exists:
        form = WhatsAppInstanceForm(instance=instance)
    else:
        form = WhatsAppInstanceForm()

    # Buscar estatísticas
    stats = {}
    if instance and instance.is_connected:
        try:
            stats = {
                "groups_count": instance.groups.filter(is_active=True).count(),
                "contacts_count": instance.contacts.filter(is_active=True).count(),
                "messages_sent": instance.messages_sent,
                "messages_received": instance.messages_received,
            }
        except:
            stats = {
                "groups_count": 0,
                "contacts_count": 0,
                "messages_sent": 0,
                "messages_received": 0,
            }

    context = {
        "instance": instance,
        "instance_exists": instance_exists,
        "instances": instances,
        "current_instances_count": current_instances_count,
        "max_instances": max_instances,
        "can_create_more": can_create_more,
        "form": form,
        "stats": stats,
        "subscription": subscription,
        "page_title": "Conectar WhatsApp",
    }

    return render(request, "whatsapp/connect.html", context)


@login_required
def get_qr_code_ajax(request):
    """AJAX endpoint para buscar dados de conexão (QR Code ou Pairing Code)."""

    try:
        # Pegar a primeira instância do usuário (para compatibilidade)
        instance = WhatsAppInstance.objects.filter(user=request.user).first()
        if not instance:
            return JsonResponse({"error": "Nenhuma instância encontrada"}, status=404)

        if instance.status in ["qr_code", "pairing_code", "connecting"]:
            # Atualizar status da instância
            success, instance = WhatsAppInstanceManager.sync_instance_status(instance)

            response_data = {
                "status": instance.status,
                "phone_number": instance.phone_number or instance.whatsapp_number,
                "connection_method": instance.connection_method,
            }

            if instance.status == "qr_code" and instance.qr_code and instance.connection_method == 'qr_code':
                response_data.update(
                    {
                        "qr_code": instance.qr_code,
                        "expires_at": instance.qr_code_expires_at.isoformat()
                        if instance.qr_code_expires_at
                        else None,
                    }
                )
            elif instance.status == "qr_code" and instance.qr_code and instance.connection_method == 'pairing_code':
                response_data.update(
                    {
                        "qr_code": instance.qr_code,
                        "expires_at": instance.qr_code_expires_at.isoformat()
                        if instance.qr_code_expires_at
                        else None,
                    }
                )
            elif instance.status == "pairing_code" and instance.pairing_code:
                response_data.update(
                    {
                        "pairing_code": instance.pairing_code,
                    }
                )

            return JsonResponse(response_data)
        else:
            return JsonResponse(
                {
                    "status": instance.status,
                    "phone_number": instance.phone_number,
                    "connection_method": instance.connection_method,
                }
            )

    except WhatsAppInstance.DoesNotExist:
        return JsonResponse({"error": "Instância não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def sync_whatsapp_data_ajax(request, pk):
    """AJAX endpoint para sincronizar dados do WhatsApp."""

    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    try:
        instance = WhatsAppInstance.objects.get(user=request.user, id=pk)

        if not instance.is_connected:
            return JsonResponse({"error": "WhatsApp não está conectado"}, status=400)

        sync_type = request.POST.get("type", "all")
        results = {}

        if sync_type in ["all", "groups"]:
            try:
                groups_synced = WhatsAppInstanceManager.sync_groups(instance)
                results["groups"] = {"synced": groups_synced, "success": True}
            except Exception as e:
                results["groups"] = {"error": str(e), "success": False}

        if sync_type in ["all", "contacts"]:
            try:
                contacts_synced = WhatsAppInstanceManager.sync_contacts(instance)
                results["contacts"] = {"synced": contacts_synced, "success": True}
            except Exception as e:
                results["contacts"] = {"error": str(e), "success": False}

        if sync_type in ["all", "status"]:
            try:
                status_synced = WhatsAppInstanceManager.sync_instance_status(instance)
                results["status"] = {"synced": status_synced, "success": True}
            except Exception as e:
                results["status"] = {"error": str(e), "success": False}

        return JsonResponse({"message": "Sincronização concluída", "results": results})

    except WhatsAppInstance.DoesNotExist:
        return JsonResponse({"error": "Instância não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def whatsapp_instances_list_view(request):
    """View para listar todas as instâncias WhatsApp (para usuários com múltiplas instâncias)."""

    instances = WhatsAppInstance.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    # Atualizar status de todas as instâncias
    for instance in instances:
        try:
            WhatsAppInstanceManager.sync_instance_status(instance)
        except:
            pass

    context = {
        "instances": instances,
        "page_title": "Minhas Instâncias WhatsApp",
    }

    return render(request, "whatsapp/instances_list.html", context)


@login_required
def groups_list_view(request):
    """View para listar todos os grupos WhatsApp (para usuários com múltiplos grupos)."""

    groups = WhatsAppGroup.objects.filter(
        whatsapp_instance__user=request.user
    ).order_by("-created_at")

    context = {
        "groups": groups,
        "page_title": "Meus Grupos WhatsApp",
    }
    return render(request, "whatsapp/groups_list.html", context)



# endpoint pra conectar o número do whatsapp - REAPROVEITAR O DO PROJETO
# endpoint para mandar mensagem - REAPROVEITAR O DO PROJETO
# X Instancias conectadas - REAPROVEITAR O DO PROJETO

# X criações e gerencia de grupos
# class SettingsWhatsappGroupsViews(APIView):
#     """
#     Controla as permissoes e configuracoes dos grupos de cada instancia
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         """
#         Atualiza permissões de envio de mensagens em um grupo do WhatsApp.
#         """
#         groupjid = request.data.get("groupjid")
#         announce = request.data.get("announce")

#         #Verifica se existe ou não os campos
#         if groupjid is None or announce is None:
#             return Response({"error": "Campos 'groupjid' e 'announce' são obrigatórios."}, status=400)

#         # 🔹 Recupera a instância do WhatsApp do usuário autenticado
#         try:
#             instance = WhatsAppInstance.objects.get(user=request.user)
#         except WhatsAppInstance.DoesNotExist:
#             return Response({"error": "Instância de WhatsApp não encontrada para este usuário."}, status=404)

#         # 🔹 Chama o service que faz a requisição à UAZAPI
#         success, data = WhatsAppAPIService.post_permissions_messages_groups(instance, groupjid, announce)

#         if success:
#             return Response({"success": True, "data": data}, status=200)
#         else:
#             return Response({"success": False, "data": data}, status=400)



# # Mencao de participantes em grupos
# class MentionParticipantsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         """
#         Envia uma mensagem mencionando participantes de um grupo.
#         """
#         group_id = request.data.get("group_id")
#         message = request.data.get("message")

#         if not group_id or not message:
#             return Response({"error": "Campos 'group_id' e 'message' são obrigatórios."}, status=400)

#         # 🔹 Recupera instância do WhatsApp do usuário
#         try:
#             instance = WhatsAppInstance.objects.get(user=request.user)
#         except WhatsAppInstance.DoesNotExist:
#             return Response({"error": "Instância de WhatsApp não encontrada."}, status=404)

#         # 🔹 Recupera o grupo e os participantes ativos
#         try:
#             group = WhatsAppGroup.objects.get(group_id=group_id, whatsapp_instance=instance)
#         except WhatsAppGroup.DoesNotExist:
#             return Response({"error": "Grupo não encontrado."}, status=404)

#         participants = list(
#             group.participants.filter(is_active=True).values_list("jid", flat=True)
#         )

#         if not participants:
#             return Response({"error": "Nenhum participante ativo encontrado."}, status=400)

#         # 🔹 Chama o serviço da API
#         success, data = WhatsAppAPIService.post_group_mentions(instance, group_id, message, participants)

#         if success:
#             return Response({"success": True, "data": data}, status=200)
#         else:
#             return Response({"success": False, "data": data}, status=400)


# ENDPOINT do summario do meu site
@api_view(["GET"])
def dashboard_summary(request):
    instances_activates = WhatsAppInstance.objects.filter(is_active=True, status="connected").count()
    total_instances = WhatsAppInstance.objects.count()
    total_groups = WhatsAppGroup.objects.count()
    total_members_groups = WhatsAppGroupParticipant.objects.count()
    #falta instancia ativa
    total_contacts = WhatsAppContact.objects.filter(
        whatsapp_instance__is_active=True
    ).count()

    data = {
        "summary" : {
            "instances_actives": instances_activates,
            "total_instances" : total_instances,
            "total_groups" : total_groups,
            "total_members" : total_members_groups,
            "total_contacts" : total_contacts
        }
    }
    
    return Response(data)


@api_view(["GET"])
def get_instances_details(request):
    instances = []
    for instance in WhatsAppInstance.objects.all():
        contact_count = WhatsAppContact.objects.filter(whatsapp_instance=instance).count()
        instances.append({
            "name": instance.name,
            "status": "connected" if instance.is_connected else "disconnected",
            "contacts": contact_count
        })

    data = {
        "instances" : instances
    }

    return Response(data)



@api_view(["GET", "POST"])
def campaings_details(request):
    if request.method == "GET":
        campaigns = WhatsAppCampaign.objects.order_by('-created_at')[:5]

        activities = []
        for campaign in campaigns:
                # Determina o status
            if campaign.is_active and campaign.scheduled_at and campaign.scheduled_at > now():
                status_label = "Agendado"
                status_color = "blue"
            elif campaign.is_active:
                status_label = "Ativo"
                status_color = "green"
            else:
                status_label = "Concluído"
                status_color = "gray"

            activities.append({
                "title": campaign.name,
                "date": campaign.scheduled_at.strftime("%Y-%m-%d") if campaign.scheduled_at else campaign.created_at.strftime("%Y-%m-%d"),
                "status": status_label,
                "status_color": status_color
            })

        return Response({"recent_activities": activities}, status=status.HTTP_200_OK)
    elif request.method == "POST":
        serializer = WhatsappCampaignSerializer(
            data=request.data,
            context={"request": request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
        




# Endpoint que exibe todas as instancias(números cadastrados) no dashboard
class AllWhatsappInstanceActivateView(viewsets.ModelViewSet):
    """
    Exibe todas as instâncias do usuário independente de estarem ativas ou não
    """
    queryset = WhatsAppInstance.objects.all()
    serializer_class = WhatsAppInstanceSerializer



# Criar endpoint com APIView que vai mostrar as instâncias ativas
class WhatsappInstanceActivateView(APIView):
    """
    Retorna todas os números conectados(instâncias ativas) do usuário
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instance_active = WhatsAppInstance.objects.filter(
            user=request.user, is_active=True, status="connected"
        )
        serializer = WhatsAppInstanceSerializer(instance_active, many=True)
        return Response(serializer.data)



# Mostra todos os grupos ativos da instância conectada
class ActiveGroupsView(APIView):
    """
    Retorna todos os grupos sincronizados pertencentes às instâncias ativas do usuário
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtra instâncias do usuário que estão ativas e conectadas
        active_instances = WhatsAppInstance.objects.filter(
            user=request.user, is_active=True, status="connected"
        )

        if not active_instances.exists():
            return Response({"detail": "Nenhuma instância ativa encontrada."}, status=404)
        
        total_groups_synced = 0

        for instance in active_instances:
            try:
                synced = WhatsAppInstanceManager.sync_groups(instance)
                total_synced += synced
            except Exception as e:
                print(f"Erro ao sincronizar grupos da instância {instance.id}: {e}")
        
        # Filtra grupos pertencentes a essas instâncias e ativos
        groups = WhatsAppGroup.objects.filter(  
            whatsapp_instance__in=active_instances,
            is_active=True  
        ).order_by("name")

        serializer = WhatsAppGroupSerializer(groups, many=True)
        
        # 4️⃣ Retornar resposta completa
        return Response({
            "message": f"Sincronizacao concluída com sucesso. Total de grupos sincronizados: {total_groups_synced}.",
            "groups_count": groups.count(),
            "groups": serializer.data
        })


 
class ActivateContatsInstancesView(APIView):
    """
    Retorna todos os contatos dentro dos grupos sincronizados das instâncias conectadas e ativas do usuário
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Busca as instâncias do usuário logado
        active_instances = WhatsAppInstance.objects.filter(
            user=request.user, is_active=True, status="connected"
        )
        
        if not active_instances.exists():
            return Response({"detail":"Nenhuma instância ativa encontrada"}, status=404 )
        
        total_contacts_synced = 0

        for instance in active_instances:
            try:
                synced = WhatsAppInstanceManager.sync_contacts(instance)
                total_synced += synced
            except Exception as e:
                print(f"Erro ao sincronizar grupos da instância {instance.id}: {e}")

        # Filtra os contatos das instâncias ativas do usuário   
        contacts = WhatsAppContact.objects.filter(
            whatsapp_instance__in=active_instances,
            is_active=True      
        ).order_by("name")

        serializer = WhatsAppContactSerializer(contacts, many=True)

        # 4️⃣ Retornar resposta completa
        return Response({
            "message": f"Sincronizacao concluída com sucesso. Total de contatos sincronizados: {total_contacts_synced}.",
            "contacts_count": contacts.count(),
            "contacts": serializer.data
        }) 



