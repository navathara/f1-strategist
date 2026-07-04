from .tools import (
    get_upcoming_race,
    get_driver_standings,
    get_recent_form,
    get_circuit_history,
    get_value_score
)


def run_data_agent() -> str:
    """
    Data Collection Agent — collects all race data directly using F1 tools.
    No LLM calls needed here — data collection is deterministic.
    Only the Strategy Agent needs Gemini.
    """
    # Step 1: Upcoming race
    race = get_upcoming_race()
    circuit_id = race.get("circuit_id", "silverstone")

    # Step 2: Full standings
    standings = get_driver_standings()

    # Step 3: Circuit history
    history = get_circuit_history(circuit_id)

    # Step 4: Form + value for top 6 drivers only
    top_drivers = standings[:6] if standings and "error" not in standings[0] else []
    driver_data = []
    for driver in top_drivers:
        form = get_recent_form(driver["driver_id"])
        value = get_value_score(driver["driver_id"])
        driver_data.append({
            "name": driver["name"],
            "driver_id": driver["driver_id"],
            "team": driver["team"],
            "points": driver["points"],
            "cost": driver["cost"],
            "avg_position": form.get("avg_position_last_5", "N/A"),
            "races_counted": form.get("races_counted", 0),
            "value_score": value.get("value_score", "N/A"),
            "value_per_credit": value.get("value_per_credit", "N/A"),
            "recent_races": form.get("recent_races", [])
        })

    # Step 5: Also grab positions 7-15 for budget picks (standings only, no form calls)
    budget_picks = standings[6:15] if len(standings) > 6 else []

    # Format clean summary for Strategy Agent
    lines = [
        f"UPCOMING RACE: {race.get('race_name')} at {race.get('circuit_name')} on {race.get('date')}",
        f"CIRCUIT ID: {circuit_id}",
        "",
        "CIRCUIT HISTORY (last 3 years):"
    ]
    for h in history.get("history", []):
        lines.append(f"  {h['year']}: Winner={h['winner']}, Top3={h['top_3']}")

    lines += ["", "TOP 6 DRIVERS — FULL ANALYSIS:"]
    for d in driver_data:
        lines.append(
            f"  {d['name']} | Team: {d['team']} | Champ pts: {d['points']} | "
            f"Cost: {d['cost']} | Avg pos last 5: {d['avg_position']} | "
            f"Value score: {d['value_score']} | Value/credit: {d['value_per_credit']}"
        )
        for r in d.get("recent_races", []):
            lines.append(f"    - {r['race']}: P{r['position']} ({r['status']})")

    lines += ["", "BUDGET PICKS (P7-P15, standings only):"]
    for d in budget_picks:
        lines.append(
            f"  {d['name']} | Team: {d['team']} | "
            f"Champ pts: {d['points']} | Cost: {d['cost']}"
        )

    return "\n".join(lines)