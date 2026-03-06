"""USDA FoodData Central Tool — Nutritional data, food composition, and labels.

Free, no API key required (key optional for higher limits).
Docs: https://fdc.nal.usda.gov/api-guide.html
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


_FDC_BASE = "https://api.nal.usda.gov/fdc/v1"


class FoodDataInput(BaseModel):
    query: str = Field(
        ..., description="Food name or search term (e.g. 'chicken breast', 'kale')"
    )
    max_results: int = Field(3, ge=1, le=10, description="Max foods to return")


class FoodDataTool(BaseTool):
    name: str = "usda_fooddata"
    description: str = (
        "Search USDA FoodData Central for nutritional composition — calories, "
        "protein, fat, carbs, vitamins, minerals. Free, no key required."
    )
    args_schema: type = FoodDataInput

    def _run(self, query: str, max_results: int = 3) -> str:
        api_key = os.getenv("USDA_API_KEY", "DEMO_KEY")

        try:
            resp = requests.get(
                f"{_FDC_BASE}/foods/search",
                params={
                    "query": query,
                    "pageSize": max_results,
                    "api_key": api_key,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            foods = data.get("foods", [])[:max_results]

            if not foods:
                return f"No food data found for '{query}'."

            lines = [f"USDA FoodData results for '{query}':"]
            for food in foods:
                name = food.get("description", "N/A")
                brand = food.get("brandOwner", "")
                cat = food.get("foodCategory", "")
                fdc_id = food.get("fdcId", "")

                lines.append(f"\n  {name}" + (f" ({brand})" if brand else ""))
                if cat:
                    lines.append(f"    Category: {cat}")

                # Extract key nutrients
                nutrients = {
                    n.get("nutrientName", ""): n
                    for n in food.get("foodNutrients", [])
                }
                energy = nutrients.get("Energy", {})
                protein = nutrients.get("Protein", {})
                fat = nutrients.get("Total lipid (fat)", {})
                carbs = nutrients.get("Carbohydrate, by difference", {})
                fiber = nutrients.get("Fiber, total dietary", {})
                sugar = nutrients.get("Sugars, total including NLEA", {})

                lines.append(
                    f"    Calories: {energy.get('value', '?')} {energy.get('unitName', 'kcal')} | "
                    f"Protein: {protein.get('value', '?')}g | "
                    f"Fat: {fat.get('value', '?')}g | "
                    f"Carbs: {carbs.get('value', '?')}g"
                )
                if fiber.get("value"):
                    lines.append(
                        f"    Fiber: {fiber['value']}g | "
                        f"Sugar: {sugar.get('value', '?')}g"
                    )
                lines.append(
                    f"    FDC ID: {fdc_id} | "
                    f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{fdc_id}"
                )

            return "\n".join(lines)

        except requests.exceptions.HTTPError as e:
            return f"USDA FoodData error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"USDA FoodData error: {e}"
