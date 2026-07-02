from agent.agent import run_agent

print("🏎️  Generating lineup for upcoming race...\n")
print("This will take 30-40 seconds while the agent calls tools.\n")

result = run_agent(
    "Build me the best value 5-driver lineup for the upcoming F1 race. Stay within the 80-credit budget.")
print(result)
