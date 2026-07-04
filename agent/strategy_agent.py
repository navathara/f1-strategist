import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

PREFERENCE_INSTRUCTIONS = {
    "safe": "The user prefers SAFE picks — prioritise drivers with consistent top-5 finishes. Avoid anyone with DNFs in recent races.",
    "balanced": "The user prefers a BALANCED lineup — mix reliable top performers with good-value mid-grid picks.",
    "aggressive": "The user prefers HIGH RISK, HIGH REWARD — include at least one outside-the-box pick who has shown flashes of brilliance but may be inconsistent."
}

# Try models in order until one works
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]


def run_strategy_agent(
    race_data: str,
    user_query: str,
    preference: str = "balanced",
    history: list = None
) -> str:
    """Strategy Agent — reasons over collected data to build the optimal lineup."""

    pref_text = PREFERENCE_INSTRUCTIONS.get(preference, PREFERENCE_INSTRUCTIONS["balanced"])

    STRATEGY_PROMPT = f"""You are an F1 Strategy Agent. A Data Collection Agent has already gathered all race data for you.

Your job is to analyse this data and build the optimal 5-driver lineup.

Budget rule: Total cost must be 80 credits or under.
If your first selection exceeds 80 credits, swap the driver with the lowest value_per_credit for the next best cheaper alternative and recalculate until the budget is met.

User preference: {pref_text}

Output format:
1. A markdown table: Driver | Team | Cost | Value Score | Reason
2. A line showing: **Total Budget Used: X credits**
3. A 2-sentence strategy summary for this specific race and circuit."""

    contents = f"Race data collected by the Data Agent:\n\n{race_data}\n\nUser request: {user_query}"

    if history:
        recent = history[-4:]
        history_text = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in recent])
        contents = f"Previous conversation:\n{history_text}\n\n{contents}"

    last_error = None
    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=STRATEGY_PROMPT,
                    )
                )
                return response.text
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str:
                    time.sleep(65)
                elif "503" in error_str:
                    time.sleep(10)
                else:
                    break

    raise last_error