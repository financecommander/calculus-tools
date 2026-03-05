from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


class ScoutInput(BaseModel):
    query: str = Field(..., description="Search query or topic")


class ScoutTool(BaseTool):
    name: str = "scout"
    description: str = (
        "Real-time intelligence scout. Searches X (Twitter) and the web "
        "for latest news, trends, sentiment, or events."
    )

    def _run(self, query: str) -> str:
        try:
            tavily_key = os.getenv("TAVILY_API_KEY")
            web_context = ""
            if tavily_key:
                web = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "advanced",
                        "include_answer": True,
                    },
                ).json()
                web_context = web.get("answer", "")[:600]

            x_response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('XAI_API_KEY')}"},
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Search X for latest info on: {query}",
                        }
                    ],
                },
            ).json()
            x_content = x_response["choices"][0]["message"]["content"]

            return (
                f"Web/News Summary:\n{web_context}\n\n"
                f"Latest X Sentiment:\n{x_content}"
            )
        except Exception as e:
            return f"Scout error: {str(e)}"
