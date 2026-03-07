"""SendGrid Automation Tool — CrewAI BaseTool wrapper.

Delegates to ``calculus_tools.sendgrid`` for the actual sending logic.
Requires: pip install sendgrid, crewai
"""

from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from calculus_tools.sendgrid import send_email, send_batch


class SendEmailInput(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    name: str = Field("there", description="Recipient first name for greeting")
    company: str = Field("", description="Recipient company name (optional)")
    subject: str = Field("", description="Email subject. Auto-generated from company if blank.")
    html_content: str = Field("", description="Custom HTML body. Auto-generated if blank.")


class BatchEmailInput(BaseModel):
    leads_json: str = Field(
        ...,
        description="JSON array of lead objects. Each must have 'email'; optional: 'name', 'company'.",
    )
    dry_run: bool = Field(True, description="If true, log only — do not send.")
    limit: int = Field(30, ge=1, le=500, description="Max emails to send.")


class SendGridTool(BaseTool):
    """Send a single email via SendGrid."""

    name: str = "sendgrid_send"
    description: str = (
        "Send a single email through SendGrid. "
        "Generates a default AI-outreach body if html_content is omitted. "
        "Requires SENDGRID_API_KEY env var."
    )
    args_schema: type = SendEmailInput

    def _run(self, to_email: str, name: str = "there", company: str = "", subject: str = "", html_content: str = "") -> str:
        ok, msg = send_email(to_email, name, company, subject, html_content)
        return msg


class SendGridBatchTool(BaseTool):
    """Run a batch email campaign via SendGrid with dedup tracking."""

    name: str = "sendgrid_batch"
    description: str = (
        "Run an email campaign for a JSON list of leads. "
        "Deduplicates against previously-sent addresses. "
        "Set dry_run=false to send live. Requires SENDGRID_API_KEY env var."
    )
    args_schema: type = BatchEmailInput

    def _run(self, leads_json: str, dry_run: bool = True, limit: int = 30) -> str:
        try:
            leads: list[dict] = json.loads(leads_json)
        except (json.JSONDecodeError, TypeError) as exc:
            return f"Invalid leads_json: {exc}"

        result = send_batch(leads, dry_run=dry_run, limit=limit)
        header = f"{'DRY RUN' if dry_run else 'LIVE'} campaign: {result['sent']}/{limit} processed"
        return header + "\n" + "\n".join(result["details"])
