"""Alpha Vantage Tool — Stock prices, fundamentals, forex, crypto.

Free tier: 5 req/min, 500 req/day. Requires free API key.
Get key: https://www.alphavantage.co/support/#api-key
Docs: https://www.alphavantage.co/documentation/
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os
import requests


_AV_BASE = "https://www.alphavantage.co/query"


class AlphaVantageInput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol (e.g. 'AAPL', 'MSFT', 'EUR/USD')")
    function: str = Field(
        "GLOBAL_QUOTE",
        description=(
            "API function: 'GLOBAL_QUOTE' (price), 'OVERVIEW' (fundamentals), "
            "'TIME_SERIES_DAILY', 'INCOME_STATEMENT', 'BALANCE_SHEET', "
            "'NEWS_SENTIMENT', 'CURRENCY_EXCHANGE_RATE'"
        ),
    )


class AlphaVantageTool(BaseTool):
    name: str = "alpha_vantage"
    description: str = (
        "Retrieve real-time stock quotes, company fundamentals, income statements, "
        "balance sheets, forex rates, and news sentiment from Alpha Vantage. "
        "Requires ALPHA_VANTAGE_API_KEY env var."
    )
    args_schema: type = AlphaVantageInput

    def _run(self, symbol: str, function: str = "GLOBAL_QUOTE") -> str:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return "Alpha Vantage error: ALPHA_VANTAGE_API_KEY not set"

        params: dict = {
            "function": function,
            "apikey": api_key,
        }

        # Route symbol param based on function
        if function == "CURRENCY_EXCHANGE_RATE":
            parts = symbol.split("/")
            params["from_currency"] = parts[0] if parts else symbol
            params["to_currency"] = parts[1] if len(parts) > 1 else "USD"
        elif function == "NEWS_SENTIMENT":
            params["tickers"] = symbol
        else:
            params["symbol"] = symbol

        try:
            resp = requests.get(_AV_BASE, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if "Error Message" in data:
                return f"Alpha Vantage: {data['Error Message']}"
            if "Note" in data:
                return f"Alpha Vantage rate limit: {data['Note']}"

            return self._format(function, symbol, data)

        except requests.exceptions.HTTPError as e:
            return f"Alpha Vantage error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Alpha Vantage error: {e}"

    def _format(self, function: str, symbol: str, data: dict) -> str:
        if function == "GLOBAL_QUOTE":
            q = data.get("Global Quote", {})
            return (
                f"{symbol}: ${q.get('05. price', '?')} | "
                f"Change: {q.get('09. change', '?')} ({q.get('10. change percent', '?')}) | "
                f"Vol: {q.get('06. volume', '?')} | "
                f"Date: {q.get('07. latest trading day', '?')}"
            )
        elif function == "OVERVIEW":
            return (
                f"{data.get('Name', symbol)} ({data.get('Exchange', '?')})\n"
                f"  Sector: {data.get('Sector', '?')} | Industry: {data.get('Industry', '?')}\n"
                f"  Market Cap: ${data.get('MarketCapitalization', '?')} | "
                f"P/E: {data.get('PERatio', '?')} | EPS: {data.get('EPS', '?')}\n"
                f"  52wk High: ${data.get('52WeekHigh', '?')} | "
                f"52wk Low: ${data.get('52WeekLow', '?')}\n"
                f"  Div Yield: {data.get('DividendYield', '?')} | "
                f"Beta: {data.get('Beta', '?')}"
            )
        elif function == "CURRENCY_EXCHANGE_RATE":
            r = data.get("Realtime Currency Exchange Rate", {})
            return (
                f"{r.get('1. From_Currency Code', '?')} → "
                f"{r.get('3. To_Currency Code', '?')}: "
                f"{r.get('5. Exchange Rate', '?')} | "
                f"Updated: {r.get('6. Last Refreshed', '?')}"
            )
        elif function == "NEWS_SENTIMENT":
            feed = data.get("feed", [])[:5]
            if not feed:
                return f"No news sentiment for {symbol}."
            lines = [f"News sentiment for {symbol}:"]
            for item in feed:
                score = item.get("overall_sentiment_score", 0)
                label = item.get("overall_sentiment_label", "?")
                lines.append(
                    f"  • [{label} {score:+.3f}] {item.get('title', '?')[:100]} "
                    f"({item.get('source', '?')})"
                )
            return "\n".join(lines)
        else:
            # Generic: return first few keys
            return json.dumps(data, indent=2)[:2000]
