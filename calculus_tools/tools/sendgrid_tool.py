"""SendGrid Automation Tool — Email campaign sending via SendGrid API.

Provides single-email and batch-campaign capabilities for the Calculus
Holdings outreach pipeline. Matches the ``sendgrid_automation`` module
declared in ``calculus_swarm_unified.orc`` (Division 2).

Requires:
    pip install sendgrid
    Environment variable: SENDGRID_API_KEY
    Optional: EMAIL_FROM (defaults to sean@calculusoutreach.com)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    SendGridAPIClient = None  # type: ignore[misc]
    Mail = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Pydantic input schemas
# ---------------------------------------------------------------------------

class SendEmailInput(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    name: str = Field("there", description="Recipient first name for greeting")
    company: str = Field("", description="Recipient company name (optional)")
    subject: str = Field(
        "",
        description="Email subject. Auto-generated from company if blank.",
    )
    html_content: str = Field(
        "",
        description="Custom HTML body. Auto-generated if blank.",
    )


class BatchEmailInput(BaseModel):
    leads_json: str = Field(
        ...,
        description=(
            "JSON array of lead objects. Each must have 'email'; "
            "optional keys: 'name', 'company'."
        ),
    )
    dry_run: bool = Field(True, description="If true, log only — do not send.")
    limit: int = Field(30, ge=1, le=500, description="Max emails to send.")


# ---------------------------------------------------------------------------
# Helper: tracker for dedup
# ---------------------------------------------------------------------------

_SENT_TRACKER = Path("data/sent/sent_tracker.json")


def _load_sent() -> set[str]:
    try:
        return set(json.loads(_SENT_TRACKER.read_text()))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_sent(sent: set[str]) -> None:
    _SENT_TRACKER.parent.mkdir(parents=True, exist_ok=True)
    _SENT_TRACKER.write_text(json.dumps(sorted(sent)))


# ---------------------------------------------------------------------------
# Core send logic (shared by both tools)
# ---------------------------------------------------------------------------

def _send_one(
    to_email: str,
    name: str,
    company: str,
    subject: str,
    html_content: str,
) -> tuple[bool, str]:
    """Send a single email via SendGrid. Returns (success, message)."""
    if SendGridAPIClient is None:
        return False, "sendgrid package not installed (pip install sendgrid)"

    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        return False, "SENDGRID_API_KEY env var not set"

    from_email = os.getenv("EMAIL_FROM", "sean@calculusoutreach.com")

    if not subject:
        subject = (
            f"AI-Powered Solutions for {company}"
            if company
            else "AI-Powered Solutions for Your Business"
        )

    if not html_content:
        html_content = (
            f"<p>Hi {name},</p>"
            f"<p>I'm reaching out because we've built an AI orchestration platform "
            f"that helps companies like {company or 'yours'} automate complex "
            f"workflows — from code generation to financial analysis — at a "
            f"fraction of the cost of single-model approaches.</p>"
            f"<p>Would you be open to a 15-minute call this week?</p>"
            f"<p>Best,<br>Sean<br>Calculus Holdings</p>"
        )

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        if response.status_code == 202:
            return True, f"Sent to {to_email} (202)"
        return False, f"Unexpected status {response.status_code}"
    except Exception as exc:
        return False, f"SendGrid error: {exc}"


# ---------------------------------------------------------------------------
# CrewAI tools
# ---------------------------------------------------------------------------

class SendGridTool(BaseTool):
    """Send a single email via SendGrid."""

    name: str = "sendgrid_send"
    description: str = (
        "Send a single email through SendGrid. "
        "Generates a default AI-outreach body if html_content is omitted. "
        "Requires SENDGRID_API_KEY env var."
    )
    args_schema: type = SendEmailInput

    def _run(
        self,
        to_email: str,
        name: str = "there",
        company: str = "",
        subject: str = "",
        html_content: str = "",
    ) -> str:
        ok, msg = _send_one(to_email, name, company, subject, html_content)
        return msg


class SendGridBatchTool(BaseTool):
    """Run a batch email campaign via SendGrid with dedup tracking."""

    name: str = "sendgrid_batch"
    description: str = (
        "Run an email campaign for a JSON list of leads. "
        "Automatically deduplicates against previously-sent addresses. "
        "Set dry_run=false to send live. Requires SENDGRID_API_KEY env var."
    )
    args_schema: type = BatchEmailInput

    def _run(
        self,
        leads_json: str,
        dry_run: bool = True,
        limit: int = 30,
    ) -> str:
        try:
            leads: list[dict] = json.loads(leads_json)
        except (json.JSONDecodeError, TypeError) as exc:
            return f"Invalid leads_json: {exc}"

        sent_set = _load_sent()
        results: list[str] = []
        sent_count = 0

        for lead in leads[:limit]:
            email = lead.get("email", "")
            if not email or email in sent_set:
                continue

            name = lead.get("name", "there")
            company = lead.get("company", "")

            if dry_run:
                results.append(f"DRY RUN — would send to {email} ({name})")
                sent_count += 1
            else:
                ok, msg = _send_one(email, name, company, "", "")
                results.append(msg)
                if ok:
                    sent_count += 1
                    sent_set.add(email)

        if not dry_run:
            _save_sent(sent_set)

        header = f"{'DRY RUN' if dry_run else 'LIVE'} campaign: {sent_count}/{len(leads[:limit])} processed"
        return header + "\n" + "\n".join(results)
