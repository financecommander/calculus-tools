from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


class CopilotInput(BaseModel):
    query: str = Field(..., description="The coding task or research question")
    language: str = Field("python", description="Target language (default: python)")


class CopilotTool(BaseTool):
    name: str = "copilot"
    description: str = (
        "Advanced Coding & Research Copilot. Searches the web in real-time "
        "for best practices and generates clean, working code with explanations."
    )

    def _run(self, query: str, language: str = "python") -> str:
        try:
            tavily_key = os.getenv("TAVILY_API_KEY")
            context = ""
            if tavily_key:
                research = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": f"{query} {language} best practices example 2026",
                        "search_depth": "advanced",
                        "include_answer": True,
                    },
                ).json()
                context = research.get("answer", "")[:800]

            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('XAI_API_KEY')}"},
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""You are a senior full-stack engineer with real-time research.

Research context: {context}

Task: {query}
Language: {language}

Return:
- Clean, production-ready code
- Explanation of key decisions
- Usage example
- Warnings or improvements""",
                        }
                    ],
                },
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Copilot error: {str(e)}"
