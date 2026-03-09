"""
calculus-tools — shared AI tools, providers, API clients, and registry
for the Calculus Holdings ecosystem.

Modules:
    tools       — CrewAI BaseTool implementations (14 tools)
    providers   — AI provider backends (TavilyGrokProvider)
    clients     — HTTP clients (UnifiedClient, PipelineClient) + service adapters
                  Full: SendGrid, GHL
                  Stubs: Slack, Twilio SMS/Voice, Stripe, Calendar, ImageGen,
                         VideoGen, Translation, OCR, PDF, Survey, Transcription,
                         LinkedIn, X, Meta, CMS, Enrichment, Analytics
    registry    — API catalog with PostgreSQL / in-memory store
    utils       — Deduplication, normalization, validation, rate limiting, scoring
"""

__version__ = "2.5.0"
