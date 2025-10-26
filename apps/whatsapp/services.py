"""
WhatsApp API integration services for Tsuru Groups.
Adapted from the UazapiApi class provided.
"""
import requests
from typing import Dict, Tuple, List, Any, Optional
from django.conf import settings
from .models import WhatsAppInstance, WhatsAppGroup, WhatsAppGroupParticipant
from rest_framework.response import Response


class WhatsAppAPIService:
    """Service class for WhatsApp API integration."""
    
    @classmethod 
    def _get_headers(cls, instance: WhatsAppInstance) -> Dict[str, str]:
        """Get API headers for requests."""
        api_key = instance.api_key if instance else settings.DEFAULT_UAZAPI_API_KEY
        return {
            "Content-Type": "application/json",
            "admintoken": settings.DEFAULT_UAZAPI_API_KEY,
            "token": api_key,
        }
    
    @classmethod
    def create_instance(cls, instance: WhatsAppInstance) -> Tuple[bool, Dict]:
        """Create a new WhatsApp instance."""
        url = f"{instance.gateway_url}/instance/init"
        headers = cls._get_headers(instance)
        payload = {
            "name": instance.name,
            "systemname": instance.system_name,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"{response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def connect_instance(cls, instance: WhatsAppInstance) -> Tuple[bool, Dict]:
        """Connect WhatsApp instance."""
        url = f"{instance.gateway_url}/instance/connect"
        headers = cls._get_headers(instance)
        payload = {"phone": instance.whatsapp_number} if instance.whatsapp_number and instance.connection_method == 'pairing_code' else {}
        print("PAYLOAD", payload)
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print("RESPONSE", response.status_code)
            print("RESPONSE", response.text)
            if response.status_code in [200, 409]:
                data = response.json()
                print("DATA", data)
                return True, data
            else:
                return False, {"error": f"Error {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def delete_instance(cls, instance: WhatsAppInstance) -> Dict:
        """Delete WhatsApp instance."""
        url = f"{instance.gateway_url}/instance"
        headers = cls._get_headers(instance)    
        
        try:
            response = requests.delete(url, headers=headers, json={}, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json() if response.content else {}
                return {"error": f"Error {response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def send_text_message(
        cls, 
        instance: WhatsAppInstance, 
        number: str, 
        message: str, 
        quote_id: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """Send a text message."""
        url = f"{instance.gateway_url}/send/text"
        headers = cls._get_headers(instance)
        payload = {
            "number": number,
            "text": message,
            "linkPreview": False,
            "replyid": quote_id,
            "mentions": "",
            "readchat": True,
            "delay": 1200,
            "convert": "true",
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"{response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def send_menu_message(
        cls, 
        instance: WhatsAppInstance, 
        number: str, 
        message: str, 
        options: List[str], 
        menu_type: str = "list"
    ) -> Tuple[bool, Dict]:
        """Send a menu message (poll, list, or button)."""
        url = f"{instance.gateway_url}/send/menu"
        headers = cls._get_headers(instance)
        payload = {
            "number": number,
            "type": menu_type,  # poll, list, button
            "text": message,
            "footerText": "Escolha uma opção",
            "buttonText": "Selecione",
            "listButton": "Selecione",
            "selectableCount": 1,
            "choices": options,
            "replyid": "",
            "mentions": "",
            "readchat": True,
            "delay": 1200,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"{response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def send_media_message(
        cls,
        instance: WhatsAppInstance,
        number: str,
        message: str,
        media_url: str,
        media_type: str,
        quote_id: Optional[str] = None,
    ) -> Tuple[bool, Dict]:
        """Send a media message (image, video, audio, document, etc)."""
        url = f"{instance.gateway_url}/send/media"
        headers = cls._get_headers(instance)
        payload = {
            "number": number,
            "text": message,
            "type": media_type,  # document, video, image, audio, ptt, sticker
            "file": media_url,
            "docName": "",  # optional, only for documents
            "replyid": quote_id,
            "readchat": True,
            "delay": 1200,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"{response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def send_location_message(
        cls,
        instance: WhatsAppInstance,
        number: str,
        name: str,
        address: str,
        latitude: float,
        longitude: float,
    ) -> Dict:
        """Send a location message."""
        url = f"{instance.gateway_url}/send/location"
        headers = cls._get_headers(instance)
        payload = {
            "number": number,
            "name": name,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "replyid": "",
            "mentions": "",
            "readchat": True,
            "delay": 1200,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json() if response.content else {}
                return {"error": f"{response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def send_contact_message(
        cls, 
        instance: WhatsAppInstance, 
        number: str, 
        contact_name: str, 
        contact_number: str
    ) -> Dict:
        """Send a contact message."""
        url = f"{instance.gateway_url}/send/contact"
        headers = cls._get_headers(instance)
        payload = {
            "number": number,
            "fullName": contact_name,
            "phoneNumber": contact_number,
            "organization": "",
            "email": "",
            "url": "",
            "replyid": "",
            "mentions": "",
            "readchat": True,
            "delay": 1200,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"{response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def get_groups(cls, instance: WhatsAppInstance) -> Dict:
        """Get list of groups."""
        url = f"{instance.gateway_url}/group/list"
        headers = cls._get_headers(instance)
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json().get('groups', [])
            else:
                data = response.json() if response.content else {}
                return {"error": f"{response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def get_group_info(cls, instance: WhatsAppInstance, group_id: str) -> Dict:
        """Get detailed group information."""
        url = f"{instance.gateway_url}/group/info"
        headers = cls._get_headers(instance)
        payload = {
            "GroupJID": group_id,
            "getInviteLink": True,
            "force": True,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json() if response.content else {}
                return {"error": f"{response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def get_contacts(cls, instance: WhatsAppInstance) -> Dict:
        """Get list of contacts."""
        url = f"{instance.gateway_url}/contacts"
        headers = cls._get_headers(instance)
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json() if response.content else {}
                return {"error": f"{response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def get_contact_info(cls, instance: WhatsAppInstance, number: str) -> Tuple[bool, Dict]:
        """Get contact information."""
        url = f"{instance.gateway_url}/chat/GetNameAndImageURL"
        headers = cls._get_headers(instance)
        payload = {"number": number}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"{response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def validate_whatsapp_number(cls, instance: WhatsAppInstance, numbers: List[str]) -> Dict:
        """Validate WhatsApp numbers."""
        url = f"{instance.gateway_url}/chat/check"
        headers = cls._get_headers(instance)
        payload = {"numbers": numbers}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def setup_webhook(cls, instance: WhatsAppInstance, webhook_url: str) -> Dict:
        """Setup webhook for receiving messages and events."""
        url = f"{instance.gateway_url}/webhook"
        headers = cls._get_headers(instance)
        payload = {
            "enabled": True,
            "url": webhook_url,
            "events": [
                "connection",
                "messages",
                "messages_update", 
                "groups",
                "contacts",
                "chats",
            ],
            "excludeMessages": [],
            "addUrlEvents": True,
            "addUrlTypesMessages": True,
            "action": "add",
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                return {"success": "Webhook configurado com sucesso"}
            else:
                data = response.json() if response.content else {}
                return {"error": f"{response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    @classmethod
    def send_bulk_message(
        cls, 
        instance: WhatsAppInstance, 
        recipients: List[str],
        message: str,
        campaign_name: str = "Tsuru Groups Campaign",
        delay_min: int = 3,
        delay_max: int = 6
    ) -> Dict:
        """Send bulk messages to multiple recipients."""
        url = f"{instance.gateway_url}/sender/simple"
        headers = cls._get_headers(instance)
        payload = {
            "numbers": recipients,
            "type": "text",
            "folder": "Tsuru Groups",
            "delayMin": delay_min,
            "delayMax": delay_max,
            "info": campaign_name,
            "delay": 1000,
            "mentions": "",
            "text": message,
            "linkPreview": True,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json() if response.content else {}
                return {"error": f"{response.status_code}: {response.text}\n{data}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}


class WhatsAppInstanceManager:
    """Manager class for WhatsApp instance operations."""
    
    @staticmethod
    def sync_instance_status(instance: WhatsAppInstance) -> bool:
        """Sync instance status with API."""
        success, data = WhatsAppInstanceManager.get_instance_status(instance)
        
        if success and 'instance' in data:
            instance_data = data['instance']
            # Update status
            if instance_data.get('status') == 'connected' and instance.status == 'connected':
                return True, instance
            
            if instance_data.get('status') == 'open':
                instance.status = 'connected'
                instance.phone_number = instance_data.get('profilePictureUrl', '')
                instance.whatsapp_number = instance_data.get('owner')
            elif instance_data.get('status') == 'connecting':
                instance.status = 'connecting'
            elif instance_data.get('status') == 'connected':
                print("STATUS CONNECTED")
                instance.status = 'connected'
                instance.phone_number = instance_data.get('owner')
                instance.whatsapp_number = instance_data.get('owner')
            else:
                instance.status = 'disconnected'
            
            # Update QR code if available
            if 'qrcode' in instance_data and instance.status != 'connected':
                instance.qr_code = instance_data['qrcode']
                instance.status = 'qr_code'
            
            instance.save()
            return True, instance
        
        return False, instance
    
    @staticmethod
    def sync_groups(instance: WhatsAppInstance) -> int:
        """Sync groups with API."""
        from .models import WhatsAppGroup, WhatsAppGroupParticipant
        from django.utils import timezone
        from datetime import datetime
        
        data = WhatsAppAPIService.get_groups(instance)
        
        if isinstance(data, list):
            synced_count = 0
            
            for group_data in data:
                # Verificar se o usuário é admin do grupo
                is_admin = group_data.get('OwnerIsAdmin', False)
                
                # Se não for owner admin, verificar nos participantes
                if not is_admin:
                    participants = group_data.get('Participants', [])
                    owner_jid = group_data.get('OwnerJID', '')
                    
                    for participant in participants:
                        if (participant.get('JID') == owner_jid and 
                            (participant.get('IsAdmin') or participant.get('IsSuperAdmin'))):
                            is_admin = True
                            break
                # Converter data de criação do grupo
                group_created = None
                if group_data.get('GroupCreated'):
                    try:
                        group_created = datetime.fromisoformat(
                            group_data['GroupCreated'].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass
                
                # Extrair número do telefone do owner JID
                owner_phone = ""
                owner_jid = group_data.get('OwnerJID', '')
                if owner_jid and '@s.whatsapp.net' in owner_jid:
                    owner_phone = owner_jid.replace('@s.whatsapp.net', '')
                
                group, created = WhatsAppGroup.objects.update_or_create(
                    whatsapp_instance=instance,
                    group_id=group_data.get('JID', ''),
                    defaults={
                        'name': group_data.get('Name', ''),
                        'description': group_data.get('Topic', ''),
                        'participant_count': len(group_data.get('Participants', [])),
                        'is_admin': is_admin,
                        'owner_jid': owner_jid,
                        'owner_phone_number': owner_phone,
                        'is_locked': group_data.get('IsLocked', False),
                        'is_announce': group_data.get('IsAnnounce', False),
                        'is_ephemeral': group_data.get('IsEphemeral', False),
                        'disappearing_timer': group_data.get('DisappearingTimer', 0),
                        'is_join_approval_required': group_data.get('IsJoinApprovalRequired', False),
                        'group_created': group_created,
                        'creator_country_code': group_data.get('CreatorCountryCode', ''),
                        'announce_version_id': group_data.get('AnnounceVersionID', ''),
                        'participant_version_id': group_data.get('ParticipantVersionID', ''),
                        'member_add_mode': group_data.get('MemberAddMode', 'all_member_add'),
                        'last_synced_at': timezone.now(),
                    }
                )
                print("GROUP", group)
                
                # Sincronizar participantes do grupo
                participants_data = group_data.get('Participants', [])
                current_participant_jids = set()
                
                for participant_data in participants_data:
                    participant_jid = participant_data.get('JID', '')
                    if not participant_jid:
                        continue
                    
                    current_participant_jids.add(participant_jid)
                    
                    # Extrair número do telefone do JID
                    phone_number = ""
                    if '@s.whatsapp.net' in participant_jid:
                        phone_number = participant_jid.replace('@s.whatsapp.net', '')
                    elif participant_data.get('PhoneNumber'):
                        phone_number = participant_data['PhoneNumber'].replace('@s.whatsapp.net', '')
                    
                    WhatsAppGroupParticipant.objects.update_or_create(
                        group=group,
                        jid=participant_jid,
                        defaults={
                            'phone_number': phone_number,
                            'lid': participant_data.get('LID', ''),
                            'display_name': participant_data.get('DisplayName', ''),
                            'is_admin': participant_data.get('IsAdmin', False),
                            'is_super_admin': participant_data.get('IsSuperAdmin', False),
                            'error_code': participant_data.get('Error', 0),
                            'is_active': True,
                        }
                    )
                print("TOTAL PARTICIPANTS", len(participants_data))
                
                # Remover participantes que não estão mais no grupo
                # group.participants.exclude(jid__in=current_participant_jids).update(is_active=False)
                
                synced_count += 1
            
            return synced_count
        
        return 0
    
    @staticmethod
    def sync_contacts(instance: WhatsAppInstance) -> int:
        """Sync contacts with API."""
        from .models import WhatsAppContact
        
        data = WhatsAppAPIService.get_contacts(instance)
        
        if 'error' not in data and isinstance(data, list):
            synced_count = 0
            
            for contact_data in data:
                contact, created = WhatsAppContact.objects.update_or_create(
                    instance=instance,
                    phone_number=contact_data.get('id', '').replace('@c.us', ''),
                    defaults={
                        'name': contact_data.get('name', ''),
                        'is_business': contact_data.get('isBusiness', False),
                        'profile_picture_url': contact_data.get('profilePictureUrl', ''),
                    }
                )
                synced_count += 1
            
            return synced_count
        
        return 0
    
    @classmethod
    def get_instance_status(cls, instance: WhatsAppInstance) -> Tuple[bool, Dict]:
        """Get instance connection status."""
        url = f"{instance.gateway_url}/instance/status"
        headers = WhatsAppAPIService._get_headers(instance)
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"Error {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
    
    
    @classmethod
    def permissions_messages_groups(cls, instance: WhatsAppGroup)-> Tuple[bool, Dict]:
        url = f"{instance.gateway_url}/group/updateAnnounce"
        headers = WhatsAppAPIService._get_headers(instance)
        payload = {"groupjid": instance.group_id, "announce": instance.is_announce}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"Error {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
        
    
    @classmethod
    def post_group_mentions(cls, instance, groupjid: str, message: str, mentions: list) -> Tuple[bool, Dict]:
        """
        Envia uma mensagem mencionando participantes em um grupo do WhatsApp.
        """
        url = f"{instance.gateway_url}/message/sendText"
        headers = cls._get_headers(instance)
        payload = {
            "phone": groupjid,
            "message": message,
            "mentions": mentions
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"error": f"Error {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
            


    @classmethod
    def disconnect_instance(cls, instance: WhatsAppInstance) -> Tuple[bool, Dict]:
        """Disconnect WhatsApp instance."""
        url = f"{instance.gateway_url}/instance/disconnect"
        headers = WhatsAppAPIService._get_headers(instance)
        
        try:
            response = requests.post(url, headers=headers, json={}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {"error": f"Error {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}
