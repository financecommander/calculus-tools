"""Unit tests for all 14 CrewAI tools — mocked HTTP, no live API calls."""

import json
import os
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(status=200, json_data=None, text=""):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status
    resp.text = text or json.dumps(json_data or {})
    resp.json.return_value = json_data or {}
    resp.raise_for_status.side_effect = None
    return resp


def _mock_response_error(status=500):
    """Build a mock requests.Response that raises on raise_for_status."""
    import requests as _req
    resp = MagicMock()
    resp.status_code = status
    http_err = _req.exceptions.HTTPError(response=resp)
    resp.raise_for_status.side_effect = http_err
    return resp


# ===================================================================
# 1. CopilotTool
# ===================================================================

class TestCopilotTool:
    def test_run_success(self):
        from calculus_tools.tools.copilot_tool import CopilotTool
        grok_resp = _mock_response(json_data={
            "choices": [{"message": {"content": "Here is your code..."}}]
        })
        tavily_resp = _mock_response(json_data={"answer": "Best practice info"})
        with patch.dict(os.environ, {"XAI_API_KEY": "test", "TAVILY_API_KEY": "test"}):
            with patch("calculus_tools.tools.copilot_tool.requests.post", side_effect=[tavily_resp, grok_resp]):
                result = CopilotTool()._run(query="hello world", language="python")
        assert "Here is your code" in result

    def test_run_no_keys(self):
        from calculus_tools.tools.copilot_tool import CopilotTool
        with patch.dict(os.environ, {}, clear=True):
            result = CopilotTool()._run(query="test")
        assert "not set" in result.lower()


# ===================================================================
# 2. CodeReviewCopilotTool
# ===================================================================

class TestCodeReviewCopilotTool:
    def test_run_success(self):
        from calculus_tools.tools.code_review_copilot import CodeReviewCopilotTool
        grok_resp = _mock_response(json_data={
            "choices": [{"message": {"content": "Score: 8/10\nNo critical issues"}}]
        })
        tavily_resp = _mock_response(json_data={"answer": "Review tips"})
        with patch.dict(os.environ, {"XAI_API_KEY": "test", "TAVILY_API_KEY": "test"}):
            with patch("calculus_tools.tools.code_review_copilot.requests.post", side_effect=[tavily_resp, grok_resp]):
                result = CodeReviewCopilotTool()._run(code="print('hi')")
        assert "8/10" in result

    def test_run_error(self):
        from calculus_tools.tools.code_review_copilot import CodeReviewCopilotTool
        with patch.dict(os.environ, {}, clear=True):
            result = CodeReviewCopilotTool()._run(code="x")
        assert "not set" in result.lower()


# ===================================================================
# 3. ScoutTool
# ===================================================================

class TestScoutTool:
    def test_run_success(self):
        from calculus_tools.tools.scout_tool import ScoutTool
        tavily_resp = _mock_response(json_data={"answer": "Web context here"})
        grok_resp = _mock_response(json_data={
            "choices": [{"message": {"content": "X sentiment: positive"}}]
        })
        with patch.dict(os.environ, {"XAI_API_KEY": "test", "TAVILY_API_KEY": "test"}):
            with patch("calculus_tools.tools.scout_tool.requests.post", side_effect=[tavily_resp, grok_resp]):
                result = ScoutTool()._run(query="bitcoin")
        assert "Web" in result or "sentiment" in result.lower()

    def test_run_error(self):
        from calculus_tools.tools.scout_tool import ScoutTool
        with patch.dict(os.environ, {}, clear=True):
            result = ScoutTool()._run(query="test")
        assert "not set" in result.lower()


# ===================================================================
# 4. GrokpediaTool
# ===================================================================

class TestGrokpediaTool:
    def test_run_success(self):
        from calculus_tools.tools.grokpedia_tool import GrokpediaTool
        resp = _mock_response(json_data={
            "choices": [{"message": {"content": "Gravity is a fundamental force..."}}]
        })
        with patch.dict(os.environ, {"XAI_API_KEY": "test"}):
            with patch("calculus_tools.tools.grokpedia_tool.requests.post", return_value=resp):
                result = GrokpediaTool()._run(query="What is gravity?")
        assert "Gravity" in result

    def test_run_no_key(self):
        from calculus_tools.tools.grokpedia_tool import GrokpediaTool
        with patch.dict(os.environ, {}, clear=True):
            result = GrokpediaTool()._run(query="test")
        assert "XAI_API_KEY" in result

    def test_run_http_error(self):
        from calculus_tools.tools.grokpedia_tool import GrokpediaTool
        resp = _mock_response_error(429)
        with patch.dict(os.environ, {"XAI_API_KEY": "test"}):
            with patch("calculus_tools.tools.grokpedia_tool.requests.post", return_value=resp):
                result = GrokpediaTool()._run(query="test")
        assert "error" in result.lower()


# ===================================================================
# 5. SecEdgarTool
# ===================================================================

class TestSecEdgarTool:
    def test_run_success(self):
        from calculus_tools.tools.sec_edgar_tool import SecEdgarTool
        resp = _mock_response(json_data={
            "hits": {"hits": [
                {"_source": {
                    "form": "10-K",
                    "display_names": ["Apple Inc (AAPL) (CIK 0000320193)"],
                    "ciks": ["0000320193"],
                    "adsh": "0000320193-24-000123",
                    "file_date": "2024-11-01",
                }}
            ]}
        })
        with patch("calculus_tools.tools.sec_edgar_tool.requests.get", return_value=resp):
            result = SecEdgarTool()._run(query="Apple Inc", filing_type="10-K", max_results=3)
        assert "10-K" in result
        assert "Apple" in result
        assert "sec.gov" in result

    def test_run_no_hits_fallback(self):
        from calculus_tools.tools.sec_edgar_tool import SecEdgarTool
        empty = _mock_response(json_data={"hits": {"hits": []}})
        fallback = _mock_response(json_data={
            "hits": {"hits": [
                {"_source": {"form": "10-Q", "display_names": ["Tesla"], "file_date": "2024-06-01"}}
            ]}
        })
        with patch("calculus_tools.tools.sec_edgar_tool.requests.get", side_effect=[empty, fallback]):
            result = SecEdgarTool()._run(query="Tesla")
        assert "Tesla" in result

    def test_run_http_error(self):
        from calculus_tools.tools.sec_edgar_tool import SecEdgarTool
        resp = _mock_response_error(500)
        with patch("calculus_tools.tools.sec_edgar_tool.requests.get", return_value=resp):
            result = SecEdgarTool()._run(query="test")
        assert "error" in result.lower()


# ===================================================================
# 6. CourtListenerTool
# ===================================================================

class TestCourtListenerTool:
    def test_run_opinions(self):
        from calculus_tools.tools.courtlistener_tool import CourtListenerTool
        resp = _mock_response(json_data={
            "results": [
                {
                    "case_name": "Smith v. Jones",
                    "court": "Supreme Court",
                    "date_filed": "2024-01-15",
                    "absolute_url": "/opinion/12345/smith-v-jones/",
                }
            ]
        })
        with patch("calculus_tools.tools.courtlistener_tool.requests.get", return_value=resp):
            result = CourtListenerTool()._run(query="contract dispute", search_type="opinions")
        assert "smith-v-jones" in result or "Smith" in result

    def test_run_no_results(self):
        from calculus_tools.tools.courtlistener_tool import CourtListenerTool
        resp = _mock_response(json_data={"results": []})
        with patch("calculus_tools.tools.courtlistener_tool.requests.get", return_value=resp):
            result = CourtListenerTool()._run(query="xyzzzz")
        assert "No" in result or "no" in result


# ===================================================================
# 7. OpenCorporatesTool
# ===================================================================

class TestOpenCorporatesTool:
    def test_run_no_key(self):
        from calculus_tools.tools.opencorporates_tool import OpenCorporatesTool
        with patch.dict(os.environ, {}, clear=True):
            result = OpenCorporatesTool()._run(query="Google")
        assert "not set" in result.lower()

    def test_run_companies(self):
        from calculus_tools.tools.opencorporates_tool import OpenCorporatesTool
        resp = _mock_response(json_data={
            "results": {"companies": [
                {"company": {
                    "name": "Google LLC",
                    "jurisdiction_code": "us_ca",
                    "company_number": "123456",
                    "incorporation_date": "1998-09-04",
                    "current_status": "Active",
                    "opencorporates_url": "https://opencorporates.com/companies/us_ca/123456",
                }}
            ]}
        })
        with patch.dict(os.environ, {"OPENCORPORATES_API_KEY": "test"}):
            with patch("calculus_tools.tools.opencorporates_tool.requests.get", return_value=resp):
                result = OpenCorporatesTool()._run(query="Google")
        assert "Google" in result


# ===================================================================
# 8. AlphaVantageTool
# ===================================================================

class TestAlphaVantageTool:
    def test_run_no_key(self):
        from calculus_tools.tools.alpha_vantage_tool import AlphaVantageTool
        with patch.dict(os.environ, {}, clear=True):
            result = AlphaVantageTool()._run(symbol="AAPL")
        assert "not set" in result.lower()

    def test_run_global_quote(self):
        from calculus_tools.tools.alpha_vantage_tool import AlphaVantageTool
        resp = _mock_response(json_data={
            "Global Quote": {
                "01. symbol": "AAPL",
                "05. price": "185.50",
                "09. change": "+2.30",
                "10. change percent": "+1.25%",
                "06. volume": "54000000",
            }
        })
        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "test"}):
            with patch("calculus_tools.tools.alpha_vantage_tool.requests.get", return_value=resp):
                result = AlphaVantageTool()._run(symbol="AAPL", function="GLOBAL_QUOTE")
        assert "AAPL" in result
        assert "185.50" in result

    def test_run_rate_limit(self):
        from calculus_tools.tools.alpha_vantage_tool import AlphaVantageTool
        resp = _mock_response(json_data={"Note": "Thank you for using Alpha Vantage! API rate limit reached."})
        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "test"}):
            with patch("calculus_tools.tools.alpha_vantage_tool.requests.get", return_value=resp):
                result = AlphaVantageTool()._run(symbol="AAPL")
        assert "rate" in result.lower() or "limit" in result.lower() or "error" in result.lower()


# ===================================================================
# 9. FinnhubTool
# ===================================================================

class TestFinnhubTool:
    def test_run_no_key(self):
        from calculus_tools.tools.finnhub_tool import FinnhubTool
        with patch.dict(os.environ, {}, clear=True):
            result = FinnhubTool()._run(symbol="AAPL")
        assert "not set" in result.lower()

    def test_run_quote(self):
        from calculus_tools.tools.finnhub_tool import FinnhubTool
        resp = _mock_response(json_data={
            "c": 185.5, "h": 187.0, "l": 184.0, "o": 185.0,
            "pc": 183.2, "t": 1700000000
        })
        with patch.dict(os.environ, {"FINNHUB_API_KEY": "test"}):
            with patch("calculus_tools.tools.finnhub_tool.requests.get", return_value=resp):
                result = FinnhubTool()._run(symbol="AAPL", function="quote")
        assert "185.5" in result or "AAPL" in result


# ===================================================================
# 10. PubChemTool
# ===================================================================

class TestPubChemTool:
    def test_run_by_name(self):
        from calculus_tools.tools.pubchem_tool import PubChemTool
        cid_resp = _mock_response(json_data={"IdentifierList": {"CID": [2244]}})
        props_resp = _mock_response(json_data={
            "PropertyTable": {"Properties": [{
                "CID": 2244,
                "MolecularFormula": "C9H8O4",
                "MolecularWeight": "180.16",
                "IUPACName": "2-acetoxybenzoic acid",
                "XLogP": 1.2,
                "TPSA": 63.6,
            }]}
        })
        syn_resp = _mock_response(json_data={
            "InformationList": {"Information": [{"Synonym": ["aspirin", "acetylsalicylic acid"]}]}
        })
        desc_resp = _mock_response(json_data={
            "InformationList": {"Information": [{"Description": "Aspirin is a salicylate drug."}]}
        })
        with patch("calculus_tools.tools.pubchem_tool.requests.get", side_effect=[cid_resp, props_resp, syn_resp, desc_resp]):
            result = PubChemTool()._run(query="aspirin")
        assert "2244" in result
        assert "C9H8O4" in result

    def test_run_not_found(self):
        from calculus_tools.tools.pubchem_tool import PubChemTool
        resp = MagicMock()
        resp.status_code = 404
        resp.raise_for_status.side_effect = None
        with patch("calculus_tools.tools.pubchem_tool.requests.get", return_value=resp):
            result = PubChemTool()._run(query="xyznotacompound123")
        assert "no compound found" in result.lower() or "error" in result.lower()


# ===================================================================
# 11. FoodDataTool
# ===================================================================

class TestFoodDataTool:
    def test_run_success(self):
        from calculus_tools.tools.usda_fooddata_tool import FoodDataTool
        resp = _mock_response(json_data={
            "foods": [{
                "description": "Chicken breast, raw",
                "fdcId": 171077,
                "dataType": "Survey (FNDDS)",
                "foodNutrients": [
                    {"nutrientName": "Energy", "value": 120, "unitName": "KCAL"},
                    {"nutrientName": "Protein", "value": 22.5, "unitName": "G"},
                    {"nutrientName": "Total lipid (fat)", "value": 2.6, "unitName": "G"},
                ]
            }]
        })
        with patch("calculus_tools.tools.usda_fooddata_tool.requests.get", return_value=resp):
            result = FoodDataTool()._run(query="chicken breast")
        assert "Chicken" in result
        assert "Protein" in result

    def test_run_no_results(self):
        from calculus_tools.tools.usda_fooddata_tool import FoodDataTool
        resp = _mock_response(json_data={"foods": []})
        with patch("calculus_tools.tools.usda_fooddata_tool.requests.get", return_value=resp):
            result = FoodDataTool()._run(query="xyzfake")
        assert "No" in result or "no" in result


# ===================================================================
# 12. NewsApiTool
# ===================================================================

class TestNewsApiTool:
    def test_run_no_key(self):
        from calculus_tools.tools.newsapi_tool import NewsApiTool
        with patch.dict(os.environ, {}, clear=True):
            result = NewsApiTool()._run(query="test")
        assert "not set" in result.lower()

    def test_run_everything(self):
        from calculus_tools.tools.newsapi_tool import NewsApiTool
        resp = _mock_response(json_data={
            "status": "ok",
            "totalResults": 1,
            "articles": [{
                "title": "Tech Stocks Surge",
                "source": {"name": "Reuters"},
                "publishedAt": "2026-03-06T10:00:00Z",
                "url": "https://reuters.com/tech-stocks",
                "description": "Stocks hit new highs",
            }]
        })
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test"}):
            with patch("calculus_tools.tools.newsapi_tool.requests.get", return_value=resp):
                result = NewsApiTool()._run(query="technology")
        assert "Tech Stocks" in result


# ===================================================================
# 13. WikipediaTool
# ===================================================================

class TestWikipediaTool:
    def test_run_success(self):
        from calculus_tools.tools.wikipedia_tool import WikipediaTool
        resp = _mock_response(json_data={
            "type": "standard",
            "title": "Python (programming language)",
            "extract": "Python is a high-level programming language.",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Python_(programming_language)"}},
            "description": "General-purpose programming language",
        })
        resp.status_code = 200
        with patch("calculus_tools.tools.wikipedia_tool.requests.get", return_value=resp):
            result = WikipediaTool()._run(query="Python programming language")
        assert "Python" in result

    def test_run_not_found(self):
        from calculus_tools.tools.wikipedia_tool import WikipediaTool
        resp404 = MagicMock()
        resp404.status_code = 404
        search_resp = _mock_response(json_data={"query": {"search": []}})
        with patch("calculus_tools.tools.wikipedia_tool.requests.get", side_effect=[resp404, search_resp]):
            result = WikipediaTool()._run(query="xyznoarticle12345")
        assert "no" in result.lower() or "not found" in result.lower() or "error" in result.lower()


# ===================================================================
# 14. ApiIntelligenceTool
# ===================================================================

class TestApiIntelligenceTool:
    def test_run_basic(self):
        from calculus_tools.tools.api_intelligence import ApiIntelligenceTool
        result = ApiIntelligenceTool()._run(query="test query")
        assert isinstance(result, str)
        assert len(result) > 0


# ===================================================================
# Meta: ensure all 14 tools import and instantiate
# ===================================================================

class TestToolMeta:
    def test_all_14_export(self):
        from calculus_tools.tools import __all__
        assert len(__all__) == 14

    def test_all_instantiate(self):
        from calculus_tools.tools import (
            CopilotTool, CodeReviewCopilotTool, ScoutTool, ApiIntelligenceTool,
            GrokpediaTool, SecEdgarTool, CourtListenerTool, OpenCorporatesTool,
            AlphaVantageTool, FinnhubTool, PubChemTool, FoodDataTool,
            NewsApiTool, WikipediaTool,
        )
        for cls in [CopilotTool, CodeReviewCopilotTool, ScoutTool, ApiIntelligenceTool,
                     GrokpediaTool, SecEdgarTool, CourtListenerTool, OpenCorporatesTool,
                     AlphaVantageTool, FinnhubTool, PubChemTool, FoodDataTool,
                     NewsApiTool, WikipediaTool]:
            inst = cls()
            assert hasattr(inst, '_run')
            assert hasattr(inst, 'name')
            assert hasattr(inst, 'description')
            assert isinstance(inst.name, str)
            assert len(inst.name) > 0

    def test_version(self):
        from calculus_tools import __version__
        assert __version__ == "2.2.0"
