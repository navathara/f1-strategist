import requests

BASE = "https://api.jolpi.ca/ergast/f1"


def test_standings():
    r = requests.get(f"{BASE}/current/driverStandings.json", timeout=10)
    data = r.json()
    standings = data["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
    print("\n🏆Top 5 drivers (current standings):")
    for d in standings[:5]:
        print(
            f"  {d['position']}. {d['Driver']['familyName']} — {d['points']} pts")


def test_last_race():
    r = requests.get(f"{BASE}/current/last/results.json", timeout=10)
    data = r.json()
    race = data["MRData"]["RaceTable"]["Races"][0]
    print(f"\n🏁 Last race: {race['raceName']}")
    for result in race["Results"][:3]:
        print(f"  {result['position']}. {result['Driver']['familyName']}")


def test_circuit_history():
    r = requests.get(
        f"{BASE}/circuits/silverstone/results.json?limit=3", timeout=10)
    data = r.json()
    races = data["MRData"]["RaceTable"]["Races"]
    print("\n📍 Silverstone recent winners:")
    for race in races:
        winner = race["Results"][0]["Driver"]["familyName"]
        print(f"  {race['season']}: {winner}")


test_standings()
test_last_race()
test_circuit_history()
print("\n All F1 API tests passed")
