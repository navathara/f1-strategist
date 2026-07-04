from .data_agent import run_data_agent
from .strategy_agent import run_strategy_agent


def run_agent(
    user_query: str,
    preference: str = "balanced",
    history: list = None
) -> tuple:
    """
    Orchestrates the two-agent pipeline.
    Returns (data_summary, lineup_response).
    Agent 1 collects data. Agent 2 builds the strategy.
    """
    data_summary = run_data_agent()
    lineup = run_strategy_agent(
        race_data=data_summary,
        user_query=user_query,
        preference=preference,
        history=history
    )
    return data_summary, lineup


if __name__ == "__main__":
    print("🏎️ Testing two-agent pipeline...\n")
    print("Agent 1: Data Collection Agent running...")
    data, lineup = run_agent(
        "Build me the best value 5-driver lineup for the upcoming race."
    )
    print("Agent 2: Strategy Agent running...\n")
    print(lineup)