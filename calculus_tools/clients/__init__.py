"""
HTTP clients and service adapters for the Calculus ecosystem.

HTTP clients: PipelineClient, UnifiedClient
Service adapters (full): SendGrid, GHL (GoHighLevel)
Service adapters (stubs): LinkedIn, X, Meta, CMS, Enrichment, Analytics,
    Slack, Twilio SMS, Twilio Voice, Stripe, Calendar, ImageGen, VideoGen,
    Translation, OCR, PDF, Survey, Transcription
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
]
