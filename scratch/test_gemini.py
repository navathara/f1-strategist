import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def get_next_race() -> dict:
    """Returns the next upcoming F1 race."""
    return {
        "race": "British Grand Prix",
        "circuit": "Silverstone",
        "date": "2026-07-05"
    }


chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        tools=[get_next_race],
    )
)

response = chat.send_message("What is the next F1 race this weekend?")
print(response.text)
print("\n✅ Gemini function calling works!")
