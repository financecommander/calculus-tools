"""Finnhub Tool — Stock, forex, crypto quotes, news, and company profiles.

Free tier: 60 req/min. Requires free API key.
Get key: https://finnhub.io/register
Docs: https://finnhub.io/docs/api
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


_FH_BASE = "https://finnhub.io/api/v1"


class FinnhubInput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol (e.g. 'AAPL', 'BINANCE:BTCUSDT')")
    function: str = Field(
        "quote",
        description=(
            "API function: 'quote' (price), 'profile2' (company info), "
            "'company-news' (recent news), 'recommendation' (analyst ratings), "
            "'basic-financials' (metrics)"
        ),
    )


class FinnhubTool(BaseTool):
    name: str = "finnhub"
    description: str = (
        "Real-time stock quotes, company profiles, analyst recommendations, "
        "news, and financial metrics from Finnhub. 60 req/min free tier. "
        "Requires FINNHUB_API_KEY env var."
    )
    args_schema: type = FinnhubInput

    def _run(self, symbol: str, function: str = "quote") -> str:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            return "Finnhub error: FINNHUB_API_KEY not set"

        try:
            if function == "quote":
                return self._quote(symbol, api_key)
            elif function == "profile2":
                return self._profile(symbol, api_key)
            elif function == "company-news":
                return self._news(symbol, api_key)
            elif function == "recommendation":
                return self._recommendations(symbol, api_key)
            elif function == "basic-financials":
                return self._financials(symbol, api_key)
            else:
                return f"Unknown Finnhub function: {function}"
        except requests.exceptions.HTTPError as e:
            return f"Finnhub error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Finnhub error: {e}"

    def _get(self, path: str, api_key: str, params: dict | None = None) -> dict:
        p: dict = {"token": api_key}
        if params:
            p.update(params)
        resp = requests.get(f"{_FH_BASE}/{path}", params=p, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _quote(self, symbol: str, api_key: str) -> str:
        q = self._get("quote", api_key, {"symbol": symbol})
        return (
            f"{symbol}: ${q.get('c', '?')} | "
            f"Open: ${q.get('o', '?')} | High: ${q.get('h', '?')} | Low: ${q.get('l', '?')} | "
            f"Prev Close: ${q.get('pc', '?')} | Change: {q.get('dp', '?')}%"
        )

    def _profile(self, symbol: str, api_key: str) -> str:
        p = self._get("stock/profile2", api_key, {"symbol": symbol})
        if not p:
            return f"No profile found for {symbol}."
        return (
            f"{p.get('name', symbol)} ({p.get('ticker', '?')}) | "
            f"{p.get('exchange', '?')}\n"
            f"  Industry: {p.get('finnhubIndustry', '?')} | "
            f"Country: {p.get('country', '?')} | IPO: {p.get('ipo', '?')}\n"
            f"  Market Cap: ${p.get('marketCapitalization', '?')}M | "
            f"Shares: {p.get('shareOutstanding', '?')}M\n"
            f"  Web: {p.get('weburl', '?')}"
        )

    def _news(self, symbol: str, api_key: str) -> str:
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        items = self._get(
            "company-news", api_key,
            {"symbol": symbol, "from": week_ago, "to": today},
        )
        if not items:
            return f"No recent news for {symbol}."
        lines = [f"Finnhub news for {symbol} (last 7 days):"]
        for item in items[:5]:
            lines.append(
                f"  • {item.get('headline', '?')[:120]} | "
                f"{item.get('source', '?')} | "
                f"{item.get('url', '')}"
            )
        return "\n".join(lines)

    def _recommendations(self, symbol: str, api_key: str) -> str:
        recs = self._get("stock/recommendation", api_key, {"symbol": symbol})
        if not recs:
            return f"No analyst recommendations for {symbol}."
        r = recs[0]  # most recent month
        return (
            f"{symbol} analyst consensus ({r.get('period', '?')}):\n"
            f"  Strong Buy: {r.get('strongBuy', 0)} | Buy: {r.get('buy', 0)} | "
            f"Hold: {r.get('hold', 0)} | Sell: {r.get('sell', 0)} | "
            f"Strong Sell: {r.get('strongSell', 0)}"
        )

    def _financials(self, symbol: str, api_key: str) -> str:
        data = self._get(
            "stock/metric", api_key, {"symbol": symbol, "metric": "all"}
        )
        m = data.get("metric", {})
        if not m:
            return f"No financial metrics for {symbol}."
        return (
            f"{symbol} financial metrics:\n"
            f"  P/E (TTM): {m.get('peTTM', '?')} | "
            f"P/B: {m.get('pbAnnual', '?')} | "
            f"EPS (TTM): {m.get('epsNormalizedAnnual', '?')}\n"
            f"  ROE: {m.get('roeRfy', '?')} | "
            f"Debt/Equity: {m.get('totalDebt/totalEquityAnnual', '?')}\n"
            f"  52wk High: ${m.get('52WeekHigh', '?')} | "
            f"52wk Low: ${m.get('52WeekLow', '?')} | "
            f"Beta: {m.get('beta', '?')}"
        )
