from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


class CodeReviewInput(BaseModel):
    code: str = Field(..., description="The code to review")
    language: str = Field("python", description="Language")
    focus: str = Field(
        "all",
        description="Focus: security, performance, bugs, best practices, or all",
    )


class CodeReviewCopilotTool(BaseTool):
    name: str = "code_review_copilot"
    description: str = (
        "Expert code reviewer. Analyzes for bugs, security, performance, "
        "and suggests improvements with real-time research."
    )

    def _run(self, code: str, language: str = "python", focus: str = "all") -> str:
        try:
            tavily_key = os.getenv("TAVILY_API_KEY")
            context = ""
            if tavily_key:
                research = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": f"{language} code review best practices {focus} 2026",
                        "search_depth": "advanced",
                    },
                ).json()
                context = research.get("answer", "")[:600]

            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('XAI_API_KEY')}"},
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""You are a strict senior code reviewer.

Code:
{code}

Focus: {focus}
Best practices: {context}

Return:
- List of issues (bugs, security, performance)
- Specific fixes with improved code
- Overall score (1-10)
- Final optimized version""",
                        }
                    ],
                },
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Review error: {str(e)}"
