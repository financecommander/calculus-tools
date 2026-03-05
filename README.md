# calculus-tools

Shared AI tools and providers for the Calculus Holdings ecosystem.

Used by [AI-PORTAL](https://github.com/financecommander/AI-PORTAL), [super-duper-spork](https://github.com/financecommander/super-duper-spork), and other projects.

## Structure

```
calculus_tools/
├── __init__.py
├── tools/              # CrewAI BaseTool implementations
│   ├── __init__.py
│   ├── copilot_tool.py
│   ├── code_review_copilot.py
│   └── scout_tool.py
└── providers/          # AI provider implementations
    ├── __init__.py
    └── tavily_grok_provider.py
```

## Tools

| Tool | Class | Description |
|------|-------|-------------|
| **Copilot** | `CopilotTool` | Coding & research assistant — Tavily web search + Grok-4 code generation |
| **Code Review** | `CodeReviewCopilotTool` | Automated code review — bug detection, security scanning, performance analysis |
| **Scout** | `ScoutTool` | Real-time intelligence — X (Twitter) + web search for news, trends, sentiment |

## Providers

| Provider | Class | Description |
|----------|-------|-------------|
| **TavilyGrokProvider** | `TavilyGrokProvider` | Async provider that enriches prompts with Tavily web research before routing to Grok |

## Installation

```bash
pip install -e git+https://github.com/financecommander/calculus-tools.git#egg=calculus-tools
```

Or add to `requirements.txt`:

```
git+https://github.com/financecommander/calculus-tools.git
```

## Usage

### CrewAI Tools

```python
from calculus_tools.tools import CopilotTool, CodeReviewCopilotTool, ScoutTool

copilot = CopilotTool()
result = copilot._run(query="Build a FastAPI rate limiter", language="python")
```

### TavilyGrokProvider (async)

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

## Environment Variables

| Variable | Required | Used By |
|----------|----------|---------|
| `TAVILY_API_KEY` | Yes | All tools + TavilyGrokProvider |
| `XAI_API_KEY` | Yes | All tools + TavilyGrokProvider |

## License

Proprietary — Calculus Holdings LLC © 2026
