import os
try:
    import streamlit as st
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

import streamlit as st
from agent.agent import run_agent
from agent.tools import call_log

st.set_page_config(
    page_title="F1 Strategy Agent",
    page_icon="🏎️",
    layout="centered"
)

st.title("🏎️ F1 Race Strategy Agent")
st.caption("Autonomous driver lineup builder · Powered by Gemini 2.5 Flash · Live 2026 F1 data")

col1, col2, col3 = st.columns(3)
col1.metric("Next Race", "British Grand Prix")
col2.metric("Circuit", "Silverstone")
col3.metric("Budget", "80 credits")

st.divider()

F1_KEYWORDS = [
    "driver", "race", "lineup", "circuit", "grand prix", "f1",
    "formula", "team", "standings", "strategy", "silverstone",
    "qualify", "lap", "pit", "tyre", "tire", "constructor", "season"
]

def is_f1_query(text: str) -> bool:
    return any(word in text.lower() for word in F1_KEYWORDS)

query = st.text_input(
    "Ask the agent:",
    value="Build me the best value 5-driver lineup for the upcoming F1 race. Stay within the 80-credit budget."
)

if st.button("🏁 Run Agent", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a question.")
        st.stop()

    if not is_f1_query(query):
        st.error("⛔ This agent only answers F1-related questions. Try asking about drivers, lineups, or race strategy.")
        st.stop()

    call_log.clear()

    with st.spinner("Agent is working autonomously... (~30 seconds)"):
        result = run_agent(query)

    st.success("✅ Analysis complete")
    st.markdown("---")
    st.markdown(result)
    st.markdown("---")

    with st.expander(f"🔍 Agent reasoning trace — {len(call_log)} tool calls made"):
        for i, entry in enumerate(call_log, 1):
            st.markdown(f"`step {i}` {entry}")