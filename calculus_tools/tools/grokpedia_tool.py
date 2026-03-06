from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


class GrokpediaInput(BaseModel):
    query: str = Field(..., description="Factual or current-event question")


class GrokpediaTool(BaseTool):
    name: str = "grokpedia"
    description: str = (
        "Access Grok's real-time knowledge base (Grokpedia) for current events, "
        "facts, trends, or breaking news. Optimized for factual accuracy."
    )
    args_schema: type = GrokpediaInput

    def _run(self, query: str) -> str:
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            return "Grokpedia error: XAI_API_KEY not set"
        try:
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "grok-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are Grokpedia — instant access to real-time knowledge. "
                                "Answer factually and concisely, citing sources when possible. "
                                "Include dates and specifics."
                            ),
                        },
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.3,
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            return f"Grokpedia error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Grokpedia error: {e}"
