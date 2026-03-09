"""
HTTP clients and service adapters for the Calculus ecosystem.

HTTP clients: PipelineClient, UnifiedClient
Service adapters (full): SendGrid, GHL (GoHighLevel)
Service adapters (stubs): LinkedIn, X, Meta, CMS, Enrichment, Analytics,
    Slack, Twilio SMS, Twilio Voice, Stripe, Calendar, ImageGen, VideoGen,
    Translation, OCR, PDF, Survey, Transcription
Phase 2 adapters: WhatsApp, Discord, Push Notifications, Google Workspace,
    Microsoft 365, Notion, Airtable, HubSpot, Salesforce, Shopify,
    QuickBooks, GitHub, Google Ads, Meta Ads, Zapier
"""

try:
    from calculus_tools.clients.pipeline_client import PipelineClient
    from calculus_tools.clients.unified_client import UnifiedClient
except ImportError:
    PipelineClient = None
    UnifiedClient = None

try:
    from calculus_tools.clients.sendgrid_client import SendGridClient
except ImportError:
    SendGridClient = None

try:
    from calculus_tools.clients.ghl_client import GHLClient
except ImportError:
    GHLClient = None

# Communication
from calculus_tools.clients.slack_client import SlackClient
from calculus_tools.clients.twilio_sms_client import TwilioSMSClient
from calculus_tools.clients.twilio_voice_client import TwilioVoiceClient

# Payments
from calculus_tools.clients.stripe_client import StripeClient

# Scheduling
from calculus_tools.clients.calendar_client import CalendarClient

# Media generation
from calculus_tools.clients.image_gen_client import ImageGenClient
from calculus_tools.clients.video_gen_client import VideoGenClient

# Language & Document processing
from calculus_tools.clients.translation_client import TranslationClient
from calculus_tools.clients.ocr_client import OCRClient
from calculus_tools.clients.pdf_client import PDFClient
from calculus_tools.clients.transcription_client import TranscriptionClient

# Feedback
from calculus_tools.clients.survey_client import SurveyClient

# ── Phase 2: Messaging ──
try:
    from calculus_tools.clients.whatsapp_client import WhatsAppClient
except ImportError:
    WhatsAppClient = None

try:
    from calculus_tools.clients.discord_client import DiscordClient
except ImportError:
    DiscordClient = None

try:
    from calculus_tools.clients.push_notification_client import PushNotificationClient
except ImportError:
    PushNotificationClient = None

# ── Phase 2: Workspace Connectors ──
try:
    from calculus_tools.clients.google_workspace_client import GoogleWorkspaceClient
except ImportError:
    GoogleWorkspaceClient = None

try:
    from calculus_tools.clients.microsoft365_client import Microsoft365Client
except ImportError:
    Microsoft365Client = None

try:
    from calculus_tools.clients.notion_client import NotionClient
except ImportError:
    NotionClient = None

try:
    from calculus_tools.clients.airtable_client import AirtableClient
except ImportError:
    AirtableClient = None

try:
    from calculus_tools.clients.hubspot_client import HubSpotClient
except ImportError:
    HubSpotClient = None

try:
    from calculus_tools.clients.salesforce_client import SalesforceClient
except ImportError:
    SalesforceClient = None

try:
    from calculus_tools.clients.shopify_client import ShopifyClient
except ImportError:
    ShopifyClient = None

try:
    from calculus_tools.clients.quickbooks_client import QuickBooksClient
except ImportError:
    QuickBooksClient = None

try:
    from calculus_tools.clients.github_client import GitHubClient
except ImportError:
    GitHubClient = None

# ── Phase 2: Advertising ──
try:
    from calculus_tools.clients.google_ads_client import GoogleAdsClient
except ImportError:
    GoogleAdsClient = None

try:
    from calculus_tools.clients.meta_ads_client import MetaAdsClient
except ImportError:
    MetaAdsClient = None

# ── Phase 2: Integration ──
try:
    from calculus_tools.clients.zapier_client import ZapierClient
except ImportError:
    ZapierClient = None

# ── Phase 3: Voice AI ──
try:
    from calculus_tools.clients.voice_ai_client import VoiceAIClient
except ImportError:
    VoiceAIClient = None

__all__ = [
    "PipelineClient",
    "UnifiedClient",
    # Full implementations
    "SendGridClient",
    "GHLClient",
    # Communication
    "SlackClient",
    "TwilioSMSClient",
    "TwilioVoiceClient",
    # Payments
    "StripeClient",
    # Scheduling
    "CalendarClient",
    # Media generation
    "ImageGenClient",
    "VideoGenClient",
    # Language & Document processing
    "TranslationClient",
    "OCRClient",
    "PDFClient",
    "TranscriptionClient",
    # Feedback
    "SurveyClient",
    # Phase 2 — Messaging
    "WhatsAppClient",
    "DiscordClient",
    "PushNotificationClient",
    # Phase 2 — Workspace Connectors
    "GoogleWorkspaceClient",
    "Microsoft365Client",
    "NotionClient",
    "AirtableClient",
    "HubSpotClient",
    "SalesforceClient",
    "ShopifyClient",
    "QuickBooksClient",
    "GitHubClient",
    # Phase 2 — Advertising
    "GoogleAdsClient",
    "MetaAdsClient",
    # Phase 2 — Integration
    "ZapierClient",
    # Phase 3 — Voice AI
    "VoiceAIClient",
]
