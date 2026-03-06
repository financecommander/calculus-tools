# calculus-tools

> **v2.1.0** — Shared AI tools, providers, API clients, and registry for the Calculus Holdings ecosystem.

Used by [AI-PORTAL](https://github.com/financecommander/AI-PORTAL), [super-duper-spork](https://github.com/financecommander/super-duper-spork), and other projects.

---

## Structure

```
calculus_tools/
├── __init__.py
├── clients/                # HTTP / pipeline clients
│   ├── pipeline_client.py  # Multi-agent pipeline execution (REST + WebSocket)
│   └── unified_client.py   # Resilient async HTTP with retry & circuit-breaker
├── providers/              # AI provider implementations
│   └── tavily_grok_provider.py
├── registry/               # API catalog & seed data
│   ├── models.py           # Pydantic models (ApiEntry, AuthType, ApiCategory)
│   ├── store.py            # Async CRUD store (PostgreSQL / in-memory)
│   ├── import_seed.py      # CLI bulk-import script
│   ├── seed_apis.json      # 20 pre-loaded free APIs
│   └── seed_apis.csv
└── tools/                  # CrewAI BaseTool implementations
    ├── copilot_tool.py
    ├── code_review_copilot.py
    ├── scout_tool.py
    └── api_intelligence.py # Multi-API routing & synthesis
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

### CrewAI Tools

```python
from calculus_tools.tools import CopilotTool, CodeReviewCopilotTool, ScoutTool

copilot = CopilotTool()
result = copilot._run(query="Build a FastAPI rate limiter", language="python")
```

### API Intelligence

```python
from calculus_tools.tools import ApiIntelligenceTool

intel = ApiIntelligenceTool()
result = intel._run(query="What is my public IP and a random cat fact?", max_apis=5)
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
