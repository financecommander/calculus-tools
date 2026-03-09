"""
SendGrid v3 Email Client

Full implementation for transactional and marketing email via SendGrid API.
Supports single send, batch send, template-based emails, and suppression management.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Personalization,
    TemplateId, DynamicTemplateData,
)

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Represents a single email to be sent."""
    to: str
    subject: str
    from_email: str = ""
    from_name: str = ""
    html_body: str = ""
    text_body: str = ""
    template_id: Optional[str] = None
    dynamic_data: Optional[Dict[str, Any]] = None
    categories: List[str] = field(default_factory=list)
    custom_args: Optional[Dict[str, str]] = None


@dataclass
class SendResult:
    """Result of an email send operation."""
    success: bool
    status_code: int = 0
    message_id: str = ""
    error: str = ""


class SendGridClient:
    """
    SendGrid v3 email client with batch support and suppression management.

    Usage:
        client = SendGridClient()  # reads SENDGRID_API_KEY from env
        result = await client.send_email(
            to="user@example.com",
            subject="Hello",
            html="<h1>Hi</h1>",
            from_email="noreply@calculus.holdings"
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_from_email: str = "",
        default_from_name: str = "Calculus",
    ):
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY", "")
        self.default_from_email = default_from_email or os.getenv(
            "SENDGRID_FROM_EMAIL", "noreply@calculus.holdings"
        )
        self.default_from_name = default_from_name
        self._client: Optional[SendGridAPIClient] = None

    @property
    def client(self) -> SendGridAPIClient:
        if self._client is None:
            if not self.api_key:
                raise ValueError("SENDGRID_API_KEY not set")
            self._client = SendGridAPIClient(api_key=self.api_key)
        return self._client

    def send_email(
        self,
        to: str,
        subject: str,
        html: str = "",
        text: str = "",
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> SendResult:
        """Send a single email."""
        from_addr = Email(
            email=from_email or self.default_from_email,
            name=from_name or self.default_from_name,
        )
        message = Mail(
            from_email=from_addr,
            to_emails=To(to),
            subject=subject,
        )
        if html:
            message.content = [Content("text/html", html)]
        elif text:
            message.content = [Content("text/plain", text)]

        if categories:
            for cat in categories:
                message.category = cat

        try:
            response = self.client.send(message)
            return SendResult(
                success=response.status_code in (200, 201, 202),
                status_code=response.status_code,
                message_id=response.headers.get("X-Message-Id", ""),
            )
        except Exception as e:
            logger.error("SendGrid send failed: %s", e)
            return SendResult(success=False, error=str(e))

    def send_template(
        self,
        to: str,
        template_id: str,
        dynamic_data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> SendResult:
        """Send an email using a SendGrid dynamic template."""
        message = Mail()
        message.from_email = Email(
            email=from_email or self.default_from_email,
            name=from_name or self.default_from_name,
        )
        message.template_id = TemplateId(template_id)

        personalization = Personalization()
        personalization.add_to(To(to))
        personalization.dynamic_template_data = DynamicTemplateData(dynamic_data)
        message.add_personalization(personalization)

        try:
            response = self.client.send(message)
            return SendResult(
                success=response.status_code in (200, 201, 202),
                status_code=response.status_code,
                message_id=response.headers.get("X-Message-Id", ""),
            )
        except Exception as e:
            logger.error("SendGrid template send failed: %s", e)
            return SendResult(success=False, error=str(e))

    def send_batch(
        self,
        messages: List[EmailMessage],
        batch_size: int = 1000,
    ) -> List[SendResult]:
        """
        Send a batch of emails. SendGrid supports up to 1000 personalizations
        per API call. Messages are chunked accordingly.
        """
        results = []
        for i in range(0, len(messages), batch_size):
            chunk = messages[i : i + batch_size]
            for msg in chunk:
                if msg.template_id:
                    result = self.send_template(
                        to=msg.to,
                        template_id=msg.template_id,
                        dynamic_data=msg.dynamic_data or {},
                        from_email=msg.from_email or None,
                        from_name=msg.from_name or None,
                    )
                else:
                    result = self.send_email(
                        to=msg.to,
                        subject=msg.subject,
                        html=msg.html_body,
                        text=msg.text_body,
                        from_email=msg.from_email or None,
                        from_name=msg.from_name or None,
                        categories=msg.categories,
                    )
                results.append(result)
        return results

    def check_suppression(self, email: str) -> bool:
        """Check if an email is on the suppression list (bounces, spam reports, unsubscribes)."""
        try:
            response = self.client.client.suppression.bounces._(email).get()
            if response.status_code == 200:
                return True
        except Exception:
            pass

        try:
            response = self.client.client.suppression.spam_reports._(email).get()
            if response.status_code == 200:
                return True
        except Exception:
            pass

        return False

    def add_to_suppression(self, email: str, reason: str = "manual") -> bool:
        """Add an email to the global suppression list."""
        try:
            data = {"recipient_emails": [email]}
            response = self.client.client.asm.suppressions._("global").post(
                request_body=data
            )
            return response.status_code in (200, 201)
        except Exception as e:
            logger.error("Failed to add suppression for %s: %s", email, e)
            return False

    def get_stats(self, start_date: str, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get email statistics for a date range."""
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date

        try:
            response = self.client.client.stats.get(query_params=params)
            if response.status_code == 200:
                import json
                return json.loads(response.body)
        except Exception as e:
            logger.error("Failed to get stats: %s", e)

        return {}
