"""
calculus-tools — shared AI tools, providers, API clients, and registry
for the Calculus Holdings ecosystem.

Modules:
    tools       — CrewAI BaseTool implementations (14 tools)
    providers   — AI provider backends (TavilyGrokProvider)
    clients     — HTTP clients (UnifiedClient, PipelineClient) + service adapters (SendGrid, GHL)
    registry    — API catalog with PostgreSQL / in-memory store
    utils       — Deduplication, normalization, validation, rate limiting, scoring
"""

__version__ = "2.4.0"
