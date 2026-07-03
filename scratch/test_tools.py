import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import (
    get_upcoming_race,
    get_driver_standings,
    get_recent_form,
    get_circuit_history,
    get_value_score
)

print("1. Upcoming race:")
print(get_upcoming_race())

print("\n2. Top 3 in standings:")
for d in get_driver_standings()[:3]:
    print(f"  {d['position']}. {d['name']} — {d['points']} pts — cost: {d['cost']}")

print("\n3. Antonelli recent form:")
form = get_recent_form("antonelli")
print(f"  Avg position last 5 races: {form['avg_position_last_5']}")

print("\n4. Silverstone history:")
history = get_circuit_history("silverstone")
for h in history["history"]:
    print(f"  {h['year']}: {h['winner']}")

print("\n5. Value score for Antonelli:")
print(get_value_score("antonelli"))

print("\n✅ All tools working!")