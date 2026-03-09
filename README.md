# calculus-tools

> **v2.6.0** — Shared AI tools, providers, API clients, and registry for the Calculus Holdings ecosystem.

Used by [AI-PORTAL](https://github.com/financecommander/AI-PORTAL), [super-duper-spork](https://github.com/financecommander/super-duper-spork), and other projects.

---

## Structure

```
calculus_tools/
├── __init__.py
├── clients/                    # HTTP / pipeline / service clients (23 total)
│   ├── pipeline_client.py      # Multi-agent pipeline execution (REST + WebSocket)
│   ├── unified_client.py       # Resilient async HTTP with retry & circuit-breaker
│   │
│   │  ── Full implementations ──
│   ├── sendgrid_client.py      # SendGrid v3 email (send, batch, templates, suppression)
│   ├── ghl_client.py           # GoHighLevel CRM (contacts, workflows, tags)
│   │
│   │  ── Communication ──
│   ├── slack_client.py         # Slack Bot (messages, DMs, channels, files)
│   ├── twilio_sms_client.py    # Twilio SMS + WhatsApp (send, batch, delivery status)
│   ├── twilio_voice_client.py  # Twilio Voice (calls, TTS, transcription)
│   │
│   │  ── Payments ──
│   ├── stripe_client.py        # Stripe (payment links, invoices, customers, webhooks)
│   │
│   │  ── Scheduling ──
│   ├── calendar_client.py      # Google Calendar (events, availability, meeting links)
│   │
│   │  ── Media Generation ──
│   ├── image_gen_client.py     # DALL-E 3 / Stability AI (generate, edit, variations, upscale)
│   ├── video_gen_client.py     # Runway Gen-3 / Luma Dream Machine / HeyGen avatars
│   │
│   │  ── Language & Document ──
│   ├── translation_client.py   # DeepL / Google (translate, batch, detect language)
│   ├── ocr_client.py           # Google Vision / AWS Textract / Tesseract (text, tables, receipts, PDF)
│   ├── pdf_client.py           # WeasyPrint/API HTML→PDF, merge, split, watermark, extract text
│   ├── transcription_client.py # Whisper / AssemblyAI (transcribe, speakers, notes)
│   │
│   │  ── Infrastructure ──
│   ├── vector_db_client.py     # Pinecone / ChromaDB / Qdrant / Weaviate (upsert, query, index mgmt)
│   ├── vault_client.py         # HashiCorp Vault / AWS Secrets Manager (get, put, delete, list)
│   ├── search_client.py        # Elasticsearch / OpenSearch / Meilisearch (index, search, bulk)
│   ├── bigquery_client.py      # BigQuery / Snowflake / Redshift (query, schema, insert)
│   ├── vision_client.py        # Google Vision / AWS Rekognition / OpenAI Vision (labels, text, objects)
│   │
│   │  ── Feedback ──
│   ├── survey_client.py        # Typeform (create, responses, NPS, summaries)
│   │
│   │  ── Stubs ──
│   ├── linkedin_client.py      # LinkedIn API
│   ├── x_client.py             # X/Twitter API
│   ├── meta_client.py          # Meta/Facebook API
│   ├── cms_client.py           # CMS publishing
│   ├── enrichment_client.py    # Data enrichment
│   └── analytics_client.py     # Analytics reporting
│
├── utils/                      # Business data utilities
│   ├── dedupe.py               # Email/contact deduplication
│   ├── normalizers.py          # Phone, email, name normalization
│   ├── validators.py           # Email deliverability, phone format
│   ├── rate_limiter.py         # Rate window enforcement
│   └── scoring_helpers.py      # Lead scoring utilities
│
├── providers/                  # AI provider implementations
│   └── tavily_grok_provider.py
├── registry/                   # API catalog & seed data
│   ├── models.py               # Pydantic models (ApiEntry, AuthType, ApiCategory)
│   ├── store.py                # Async CRUD store (PostgreSQL / in-memory)
│   ├── import_seed.py          # CLI bulk-import script
│   ├── seed_apis.json          # 20 pre-loaded free APIs
│   └── seed_apis.csv
└── tools/                      # CrewAI BaseTool implementations (14 tools)
    ├── copilot_tool.py
    ├── code_review_copilot.py
    ├── scout_tool.py
    ├── grokpedia_tool.py
    ├── api_intelligence.py     # Multi-API routing & synthesis
    ├── sec_edgar_tool.py       # SEC EDGAR filings
    ├── courtlistener_tool.py   # Court opinions & dockets
    ├── opencorporates_tool.py  # Global company registry
    ├── alpha_vantage_tool.py   # Stock prices & fundamentals
    ├── finnhub_tool.py         # Market data & news
    ├── pubchem_tool.py         # Chemical compound data
    ├── usda_fooddata_tool.py   # Nutritional data
    ├── newsapi_tool.py         # Global news articles
    └── wikipedia_tool.py       # General knowledge lookup
```

---

## Installation

```bash
# Core (httpx, pydantic, websockets)
pip install git+https://github.com/financecommander/calculus-tools.git

# With PostgreSQL support
pip install "calculus-tools[db] @ git+https://github.com/financecommander/calculus-tools.git"

# With CrewAI tools
pip install "calculus-tools[crewai] @ git+https://github.com/financecommander/calculus-tools.git"

# Everything
pip install "calculus-tools[all] @ git+https://github.com/financecommander/calculus-tools.git"
```

Or in `requirements.txt` (PEP 508):

```
calculus-tools[db] @ git+https://github.com/financecommander/calculus-tools.git@main
```

---

## Tools

All tools extend CrewAI `BaseTool` and expose a synchronous `_run()` method.

| Tool | Class | Description |
|------|-------|-------------|
| **Copilot** | `CopilotTool` | Coding & research assistant — Tavily web search + Grok-4 code generation |
| **Code Review** | `CodeReviewCopilotTool` | Automated code review — bug detection, security scanning, performance analysis |
| **Scout** | `ScoutTool` | Real-time intelligence — X (Twitter) + web search for news, trends, sentiment |
| **API Intelligence** | `ApiIntelligenceTool` | Multi-API routing — selects relevant APIs from the registry, calls in parallel, synthesizes results |
| **Grokpedia** | `GrokpediaTool` | Real-time knowledge base — factual answers, current events, trends via Grok-4 (low temperature) |
| **SEC EDGAR** | `SecEdgarTool` | SEC filings search — 10-K, 10-Q, 8-K, insider trades, XBRL. Free, rate-limited |
| **CourtListener** | `CourtListenerTool` | U.S. court opinions, dockets, RECAP archives. Free (100 req/day) |
| **OpenCorporates** | `OpenCorporatesTool` | Global company registry — 200M+ companies, officers, subsidiaries. Free (50 req/day) |
| **Alpha Vantage** | `AlphaVantageTool` | Stock quotes, fundamentals, forex, news sentiment. Free (500 req/day) |
| **Finnhub** | `FinnhubTool` | Real-time market data, analyst ratings, company news. Free (60 req/min) |
| **PubChem** | `PubChemTool` | Chemical compound search — molecular properties, structures, safety data. Free, no key |
| **USDA FoodData** | `FoodDataTool` | Nutritional composition — calories, macros, vitamins, minerals. Free, no key |
| **NewsAPI** | `NewsApiTool` | Global news headlines & articles from 80K+ sources. Free (100 req/day) |
| **Wikipedia** | `WikipediaTool` | General knowledge lookup — article summaries & links. Free, unlimited |

### CrewAI Tools

```python
from calculus_tools.tools import CopilotTool, CodeReviewCopilotTool, ScoutTool

copilot = CopilotTool()
result = copilot._run(query="Build a FastAPI rate limiter", language="python")
```

### Grokpedia

```python
from calculus_tools.tools import GrokpediaTool

grok = GrokpediaTool()
result = grok._run(query="What are the latest SEC enforcement actions in 2026?")
```

### API Intelligence

```python
from calculus_tools.tools import ApiIntelligenceTool

intel = ApiIntelligenceTool()
result = intel._run(query="What is my public IP and a random cat fact?", max_apis=5)
```

### Data API Tools (v2.2.0)

```python
from calculus_tools.tools import (
    SecEdgarTool, CourtListenerTool, OpenCorporatesTool,
    AlphaVantageTool, FinnhubTool, PubChemTool,
    FoodDataTool, NewsApiTool, WikipediaTool,
)

# SEC filings
sec = SecEdgarTool()
result = sec._run(query="Tesla", filing_type="10-K", max_results=3)

# Court records
court = CourtListenerTool()
result = court._run(query="securities fraud", search_type="opinions")

# Company registry
oc = OpenCorporatesTool()
result = oc._run(query="Calculus Holdings", search_type="companies")

# Stock prices
av = AlphaVantageTool()
result = av._run(symbol="AAPL", function="GLOBAL_QUOTE")

# Market data + news
fh = FinnhubTool()
result = fh._run(symbol="TSLA", function="company-news")

# Chemistry
chem = PubChemTool()
result = chem._run(query="aspirin", search_type="name")

# Nutrition
food = FoodDataTool()
result = food._run(query="chicken breast", max_results=3)

# News
news = NewsApiTool()
result = news._run(query="AI regulation", category="technology")

# Wikipedia
wiki = WikipediaTool()
result = wiki._run(query="Monte Carlo method", sentences=5)
```

The tool automatically:
1. Loads enabled APIs from the registry (seeds from bundled JSON if empty)
2. Uses Grok to select the most relevant APIs (falls back to keyword heuristic)
3. Calls selected APIs in parallel via `UnifiedClient`
4. Aggregates into a Markdown report with optional Grok narrative synthesis

---

## Clients

### UnifiedClient

Resilient async HTTP client with retry, circuit-breaker, and auth injection.

```python
from calculus_tools.clients import UnifiedClient
from calculus_tools.registry import RegistryStore

store = RegistryStore()
await store.connect()
apis = await store.list_apis(enabled_only=True)

async with UnifiedClient(max_retries=3, timeout=15.0) as client:
    # Single call
    result = await client.call(apis[0])
    print(result.status_code, result.data)

    # Parallel calls
    results = await client.call_many(apis[:5])
    for r in results:
        print(r.api_name, r.status_code, f"{r.latency_ms:.0f}ms")
```

**Features:**
- Exponential-backoff retry (configurable attempts)
- Per-API circuit breaker (opens after 5 consecutive failures, 30s recovery)
- Auto auth injection: Bearer token, API key (query param), Basic auth
- `Retry-After` header support for 429 responses
- Parallel `call_many()` via `asyncio.gather`

### PipelineClient

Async client for executing multi-agent AI pipelines on the AI Portal.

```python
from calculus_tools.clients import PipelineClient

async with PipelineClient(base_url="http://34.139.78.75:8000") as client:
    pipelines = await client.list_pipelines()
    result = await client.run_pipeline("research", query="Analyze $TSLA options flow")
    print(result.output)
```

### Service Adapters (23 clients)

All service clients are async and follow the same pattern: constructor takes auth credentials, methods return dicts.

| Client | Class | Status | Description |
|--------|-------|--------|-------------|
| **SendGrid** | `SendGridClient` | Full | Email send, batch, templates, suppression, bounce handling |
| **GoHighLevel** | `GHLClient` | Full | CRM contacts, workflows, tags, search |
| **Image Gen** | `ImageGenClient` | Full | DALL-E 3 / Stability AI — generate, edit, variations, upscale, save to disk |
| **Video Gen** | `VideoGenClient` | Full | Runway Gen-3 / Luma Dream Machine / HeyGen — text→video, image→video, avatars, poll + download |
| **OCR** | `OCRClient` | Full | Google Vision / AWS Textract / Tesseract — text, structured data, tables, receipts, PDF extraction |
| **PDF** | `PDFClient` | Full | WeasyPrint / API — HTML→PDF, report generation, merge, split, watermark, extract text with page ranges |
| **Vector DB** | `VectorDBClient` | Full | Pinecone / ChromaDB / Qdrant / Weaviate — create/delete index, upsert, query, stats |
| **Vault** | `VaultClient` | Full | HashiCorp Vault / AWS Secrets Manager — get, put, delete, list secrets, engine management |
| **Vision** | `VisionClient` | Full | Google Vision / AWS Rekognition / OpenAI Vision — labels, text, objects, classification |
| **Search** | `SearchClient` | Full | Elasticsearch / OpenSearch / Meilisearch — create index, search, bulk index, count |
| **BigQuery** | `BigQueryClient` | Full | BigQuery / Snowflake / Redshift — query, list datasets/tables, schema, insert rows |
| **Slack** | `SlackClient` | Stub | Bot messages, DMs, channels, file upload |
| **Twilio SMS** | `TwilioSMSClient` | Stub | SMS, WhatsApp, batch send, delivery status |
| **Twilio Voice** | `TwilioVoiceClient` | Stub | Calls, TTS, transcription, recordings |
| **Stripe** | `StripeClient` | Stub | Payment links, invoices, customers, webhook verify |
| **Calendar** | `CalendarClient` | Stub | Google Calendar events, availability, meeting links |
| **Translation** | `TranslationClient` | Stub | DeepL / Google translate, batch, detect language |
| **Transcription** | `TranscriptionClient` | Stub | Whisper / AssemblyAI transcribe, speakers, notes |
| **Survey** | `SurveyClient` | Stub | Typeform create, responses, NPS, summaries |
| **LinkedIn** | `LinkedInClient` | Stub | LinkedIn API |
| **X/Twitter** | `XClient` | Stub | X/Twitter API |
| **Meta** | `MetaClient` | Stub | Meta/Facebook API |
| **CMS** | `CMSClient` | Stub | CMS publishing |

```python
from calculus_tools.clients import SendGridClient, GHLClient, SlackClient, StripeClient

# SendGrid (full implementation)
sg = SendGridClient(api_key="SG.xxx")
await sg.send_email(to="user@example.com", subject="Hello", html="<p>Hi</p>")

# GHL (full implementation)
ghl = GHLClient(api_key="ghl-xxx", location_id="loc-123")
await ghl.create_contact(first_name="John", last_name="Doe", email="john@example.com")

# Stub clients — API signatures defined, raise NotImplementedError
slack = SlackClient(bot_token="xoxb-xxx")
# await slack.send_message("#general", "Hello team!")  # → NotImplementedError
```

---

## Registry

API catalog with PostgreSQL persistence or in-memory fallback (no database required).

### Models

| Model | Description |
|-------|-------------|
| `AuthType` | Enum: `none`, `api_key`, `bearer`, `basic`, `oauth2` |
| `ApiCategory` | Enum: `testing`, `api_discovery`, `fun`, `demographics`, `network`, `geolocation`, `finance`, `calendar`, `news`, `market_data`, `sec`, `social`, `other` |
| `ApiEntry` | Pydantic model: `name`, `base_url`, `auth_type`, `rate_limit`, `cost_per_call`, `category`, `notes`, `enabled` |

### Store

```python
from calculus_tools.registry import RegistryStore, ApiEntry, AuthType, ApiCategory

store = RegistryStore()          # In-memory (no DATABASE_URL)
await store.connect()

# Add an API
entry = ApiEntry(
    name="Cat Fact",
    base_url="https://catfact.ninja/fact",
    auth_type=AuthType.none,
    category=ApiCategory.fun,
    cost_per_call=0.0,
)
await store.upsert(entry)

# Query
apis = await store.list_apis(category=ApiCategory.fun)

# Bulk import from seed data
count = await store.import_json("calculus_tools/registry/seed_apis.json")
```

### Seed Data (20 APIs)

Import the bundled catalog:

```bash
python -m calculus_tools.registry.import_seed
```

Included APIs: JSONPlaceholder, Public APIs Directory, Dog CEO, Cat Fact, Bored API, Agify.io, Genderize.io, Nationalize.io, IPify, IP-API, REST Countries, Frankfurter, Open Exchange Rates, Numbers API, PokeAPI, SWAPI, Nager.Date, Sunrise-Sunset, Zippopotam, HTTPBin.

---

## Providers

| Provider | Class | Description |
|----------|-------|-------------|
| **TavilyGrokProvider** | `TavilyGrokProvider` | Async provider that enriches prompts with Tavily web research before routing to Grok |

```python
from calculus_tools.providers import TavilyGrokProvider

provider = TavilyGrokProvider(
    tavily_api_key="tvly-...",
    xai_api_key="xai-...",
)
response = await provider.send_message(
    messages=[{"role": "user", "content": "Explain CORS"}],
    model="grok-4-0709",
)
```

Supports both `send_message()` (full response) and `stream_message()` (SSE streaming).

---

## Environment Variables

| Variable | Required | Used By |
|----------|----------|---------|
| `XAI_API_KEY` | Yes (for AI features) | All tools, TavilyGrokProvider |
| `TAVILY_API_KEY` | No (skips web search if absent) | CopilotTool, CodeReviewCopilotTool, ScoutTool, TavilyGrokProvider |
| `DATABASE_URL` | No (falls back to in-memory) | RegistryStore, import_seed |
| `SEC_USER_AGENT` | No (default provided) | SecEdgarTool |
| `COURTLISTENER_API_KEY` | No (basic access without) | CourtListenerTool |
| `OPENCORPORATES_API_KEY` | No (50 req/day without) | OpenCorporatesTool |
| `ALPHA_VANTAGE_API_KEY` | Yes | AlphaVantageTool |
| `FINNHUB_API_KEY` | Yes | FinnhubTool |
| `USDA_API_KEY` | No (uses DEMO_KEY) | FoodDataTool |
| `NEWSAPI_KEY` | Yes | NewsApiTool |

---

## Optional Dependencies

| Extra | Packages | When to use |
|-------|----------|-------------|
| `[db]` | `asyncpg>=0.29` | PostgreSQL-backed registry |
| `[crewai]` | `crewai>=1.0` | CrewAI tool integrations |
| `[all]` | Both above | Full install |

> **Note:** CrewAI requires `opentelemetry-api>=1.30.0`. If your project pins an older otel version, install with `[db]` instead of `[all]` to avoid conflicts.

---

## License

Proprietary — Calculus Holdings LLC © 2026
