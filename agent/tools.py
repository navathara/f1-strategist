import requests
import logging
import os
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    filename="data/agent.log",
    level=logging.INFO,
    format="%(asctime)s — %(message)s"
)

call_log = []

BASE = "https://api.jolpi.ca/ergast/f1"


def _position_to_cost(position: int) -> int:
    cost_map = {1: 26, 2: 24, 3: 22, 4: 20, 5: 18, 6: 16}
    if position in cost_map:
        return cost_map[position]
    elif position <= 10:
        return 14
    elif position <= 15:
        return 12
    return 10


def get_upcoming_race() -> dict:
    """Get the next scheduled F1 race, including the circuit ID needed for history lookups."""
    call_log.append("get_upcoming_race() → finding next scheduled race")
    logging.info("TOOL: get_upcoming_race called")
    try:
        r = requests.get(f"{BASE}/current/next.json", timeout=10)
        r.raise_for_status()
        race = r.json()["MRData"]["RaceTable"]["Races"]
        if not race:
            return {"error": "No upcoming race found"}
        race = race[0]
        return {
            "race_name": race["raceName"],
            "circuit_id": race["Circuit"]["circuitId"],
            "circuit_name": race["Circuit"]["circuitName"],
            "date": race["date"],
            "round": race["round"]
        }
    except Exception as e:
        return {"error": str(e)}


def get_driver_standings() -> list:
    """Get current F1 driver championship standings with points, team, and fantasy cost per driver."""
    call_log.append("get_driver_standings() → fetching 2026 championship standings")
    logging.info("TOOL: get_driver_standings called")
    try:
        r = requests.get(f"{BASE}/current/driverStandings.json", timeout=10)
        r.raise_for_status()
        standings = r.json()["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
        return [
            {
                "position": int(d["position"]),
                "driver_id": d["Driver"]["driverId"],
                "name": f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                "team": d["Constructors"][0]["name"] if d["Constructors"] else "Unknown",
                "points": float(d["points"]),
                "wins": int(d["wins"]),
                "cost": _position_to_cost(int(d["position"]))
            }
            for d in standings
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_recent_form(driver_id: str) -> dict:
    """Get a driver's last 5 race results this season. Use driver_id from get_driver_standings."""
    if not driver_id or not isinstance(driver_id, str):
        return {"error": "driver_id must be a non-empty string"}
    call_log.append(f"get_recent_form('{driver_id}') → checking last 5 race results")
    logging.info(f"TOOL: get_recent_form called | driver_id={driver_id}")
    try:
        r = requests.get(f"{BASE}/current/drivers/{driver_id}/results.json", timeout=10)
        r.raise_for_status()
        races = r.json()["MRData"]["RaceTable"]["Races"]
        recent = races[-5:] if len(races) >= 5 else races
        results = []
        for race in recent:
            result = race["Results"][0] if race["Results"] else {}
            results.append({
                "race": race["raceName"],
                "round": int(race["round"]),
                "position": int(result.get("position", 20)),
                "points": float(result.get("points", 0)),
                "status": result.get("status", "Unknown")
            })
        positions = [r["position"] for r in results]
        avg_pos = round(sum(positions) / len(positions), 1) if positions else 20.0
        return {
            "driver_id": driver_id,
            "recent_races": results,
            "avg_position_last_5": avg_pos,
            "races_counted": len(results)
        }
    except Exception as e:
        return {"error": str(e), "driver_id": driver_id}


def get_circuit_history(circuit_id: str) -> dict:
    """Get the last 3 years of race results at a circuit. Use circuit_id from get_upcoming_race."""
    if not circuit_id or not isinstance(circuit_id, str):
        return {"error": "circuit_id must be a non-empty string"}
    call_log.append(f"get_circuit_history('{circuit_id}') → looking up circuit winners 2023-2025")
    logging.info(f"TOOL: get_circuit_history called | circuit_id={circuit_id}")
    try:
        history = []
        for year in [2025, 2024, 2023]:
            r = requests.get(f"{BASE}/{year}/circuits/{circuit_id}/results.json?limit=3", timeout=10)
            r.raise_for_status()
            races = r.json()["MRData"]["RaceTable"]["Races"]
            if races:
                race = races[0]
                top3 = race["Results"][:3]
                history.append({
                    "year": year,
                    "winner_id": top3[0]["Driver"]["driverId"] if top3 else None,
                    "winner": f"{top3[0]['Driver']['givenName']} {top3[0]['Driver']['familyName']}" if top3 else "Unknown",
                    "top_3": [f"{r['Driver']['givenName']} {r['Driver']['familyName']}" for r in top3]
                })
        return {"circuit_id": circuit_id, "history": history}
    except Exception as e:
        return {"error": str(e)}


def get_value_score(driver_id: str) -> dict:
    """Calculate a value score for a driver based on standings and recent form. Higher score = better pick."""
    if not driver_id or not isinstance(driver_id, str):
        return {"error": "driver_id must be a non-empty string"}
    call_log.append(f"get_value_score('{driver_id}') → computing value and cost score")
    logging.info(f"TOOL: get_value_score called | driver_id={driver_id}")
    try:
        standings = get_driver_standings()
        if standings and "error" in standings[0]:
            return {"error": "Could not fetch standings"}
        driver = next((d for d in standings if d["driver_id"] == driver_id), None)
        if not driver:
            return {"error": f"Driver '{driver_id}' not found. Check driver_id from get_driver_standings."}
        form = get_recent_form(driver_id)
        avg_pos = form.get("avg_position_last_5", 10.0) if "error" not in form else 10.0
        leader_points = standings[0]["points"]
        champ_score = (driver["points"] / leader_points * 100) if leader_points > 0 else 0
        form_score = max(0, (20 - avg_pos) / 19 * 100)
        value_score = round((champ_score * 0.5) + (form_score * 0.5), 1)
        cost = driver["cost"]
        return {
            "driver_id": driver_id,
            "name": driver["name"],
            "team": driver["team"],
            "championship_points": driver["points"],
            "avg_finishing_position": avg_pos,
            "cost": cost,
            "value_score": value_score,
            "value_per_credit": round(value_score / cost, 2)
        }
    except Exception as e:
        return {"error": str(e)}