"""
HTTP clients and service adapters for the Calculus ecosystem.

HTTP clients: PipelineClient, UnifiedClient
Service adapters (full): SendGrid, GHL (GoHighLevel)
Service adapters (stubs): LinkedIn, X, Meta, CMS, Enrichment, Analytics
"""

try:
    from calculus_tools.clients.pipeline_client import PipelineClient
    from calculus_tools.clients.unified_client import UnifiedClient
except ImportError:
    PipelineClient = None
    UnifiedClient = None

from calculus_tools.clients.sendgrid_client import SendGridClient
from calculus_tools.clients.ghl_client import GHLClient

__all__ = [
    "PipelineClient",
    "UnifiedClient",
    "SendGridClient",
    "GHLClient",
]
