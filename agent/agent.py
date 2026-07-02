import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from .tools import (
    get_upcoming_race,
    get_driver_standings,
    get_recent_form,
    get_circuit_history,
    get_value_score
)

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = """You are an F1 Race Strategy Analyst. Your job is to identify the best-value drivers for the upcoming race.

You have a budget of 80 credits to pick a 5-driver lineup. Each driver has a cost based on their championship position.

When asked to build a lineup, always follow these steps in order:
1. Call get_upcoming_race() to find the circuit
2. Call get_driver_standings() to see all drivers and their costs
3. Call get_circuit_history() with the circuit_id from step 1
4. For the top 6 drivers by standings, call get_recent_form() one at a time
5. Call get_value_score() for your top candidates
6. Pick 5 drivers where total cost is 80 credits or under
7. If total exceeds 80, replace the lowest value_per_credit driver with the next best cheaper option
8. Show the final lineup as: Driver | Team | Cost | Value Score | Reason
9. Show the total budget used at the end

Think step by step and explain your reasoning."""


def run_agent(user_query: str) -> str:
    """Run the F1 strategy agent."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[
                get_upcoming_race,
                get_driver_standings,
                get_recent_form,
                get_circuit_history,
                get_value_score
            ],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=False,
                maximum_remote_calls=15
            )
        )
    )
    return response.text


if __name__ == "__main__":
    print("🏎️  F1 Strategy Agent\n")
    result = run_agent(
        "Who is leading the championship and what is their recent form?")
    print(result)
