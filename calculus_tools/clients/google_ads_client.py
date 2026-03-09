"""Calculus-Tools Google_ads Client — Service adapter for google_ads API."""
import logging, os
from typing import Dict, Any, Optional, List
logger = logging.getLogger(__name__)
_HAS_REQUESTS = False
try:
    import requests
    _HAS_REQUESTS = True
except ImportError: pass

class GoogleAdsClient:
    """Client for google_ads API."""
    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key or os.environ.get("GOOGLE_ADS_API_KEY", "")
        self.base_url = kwargs.get("base_url", "https://api.google_ads.com/v1")
    def _request(self, method, endpoint, **kwargs):
        if not _HAS_REQUESTS: return {"success": False, "error": "requests not installed"}
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            try: data = resp.json()
            except: data = resp.text
            return {"success": resp.status_code < 400, "status": resp.status_code, "data": data}
        except Exception as e: return {"success": False, "error": str(e)}
