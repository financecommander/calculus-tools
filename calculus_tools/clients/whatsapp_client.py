"""Calculus-Tools WhatsApp Client — WhatsApp Business API adapter."""
import logging, os
from typing import Dict, Any, Optional, List
logger = logging.getLogger(__name__)
_HAS_REQUESTS = False
try:
    import requests
    _HAS_REQUESTS = True
except ImportError: pass

class WhatsAppClient:
    """Client for WhatsApp Business API."""
    def __init__(self, api_key: str = None, phone_number_id: str = None):
        self.api_key = api_key or os.environ.get("WHATSAPP_API_KEY", "")
        self.phone_number_id = phone_number_id or os.environ.get("WHATSAPP_PHONE_ID", "")
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
    def _request(self, method, endpoint, **kwargs):
        if not _HAS_REQUESTS: return {"success": False, "error": "requests not installed"}
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            return {"success": resp.status_code < 400, "status": resp.status_code, "data": resp.json()}
        except Exception as e: return {"success": False, "error": str(e)}
    def send_text(self, to: str, message: str) -> dict:
        return self._request("POST", "messages", json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": message}})
    def send_template(self, to: str, template_name: str, variables: dict = None) -> dict:
        return self._request("POST", "messages", json={"messaging_product": "whatsapp", "to": to, "type": "template", "template": {"name": template_name, "language": {"code": "en_US"}}})
    def send_media(self, to: str, media_url: str, media_type: str = "image", caption: str = None) -> dict:
        return self._request("POST", "messages", json={"messaging_product": "whatsapp", "to": to, "type": media_type, media_type: {"link": media_url}})
    def send_interactive(self, to: str, body: str, buttons: list = None) -> dict:
        return self._request("POST", "messages", json={"messaging_product": "whatsapp", "to": to, "type": "interactive"})
    def get_status(self, message_id: str) -> dict:
        return self._request("GET", f"messages/{message_id}")
