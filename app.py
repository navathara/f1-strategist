import os
import re

try:
    import streamlit as st
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

import streamlit as st
from agent.agent import run_agent
from agent.tools import call_log
from agent.memory import load_memory, save_memory

st.set_page_config(
    page_title="F1 Strategy Agent",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark F1 theme ──────────────────────────────────────────────
st.markdown("""
<style>
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background-color:#0f0f0f;}
    [data-testid="stSidebar"]{background-color:#141414;border-right:1px solid #222;}
    h1,h2,h3,h4{color:#ffffff !important;}
    p,li,span,div{color:#cccccc;}
    .stButton>button{background-color:#e10600 !important;color:white !important;border:none !important;
        border-radius:4px !important;font-weight:700 !important;font-size:15px !important;height:3rem;}
    .stButton>button:hover{background-color:#ff1801 !important;}
    [data-testid="metric-container"]{background-color:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:1rem 1.25rem;}
    [data-testid="metric-container"] label{color:#888 !important;font-size:11px !important;text-transform:uppercase;letter-spacing:1px;}
    [data-testid="stMetricValue"]{color:#ffffff !important;font-size:18px !important;font-weight:700 !important;}
    .stTextInput>div>div>input{background-color:#1a1a1a !important;border:1px solid #333 !important;color:#ffffff !important;border-radius:4px !important;}
    .stTextInput>div>div>input:focus{border-color:#e10600 !important;}
    .stTextInput label{color:#888 !important;}
    [data-testid="stExpander"]{background-color:#1a1a1a !important;border:1px solid #2a2a2a !important;border-radius:8px !important;}
    hr{border-color:#2a2a2a !important;}
    table{background-color:#1a1a1a !important;border-radius:8px;overflow:hidden;width:100%;}
    th{background-color:#e10600 !important;color:white !important;font-weight:700 !important;
        text-transform:uppercase;font-size:11px !important;letter-spacing:1px;padding:12px !important;}
    td{color:#cccccc !important;border-color:#2a2a2a !important;padding:10px 12px !important;}
    tr:nth-child(even) td{background-color:#222 !important;}
    .stSuccess{background-color:#0d2b1a !important;border-color:#1a6b3c !important;}
    .stError{background-color:#2b0d0d !important;border-color:#6b1a1a !important;}
    .stWarning{background-color:#2b2200 !important;border-color:#6b5500 !important;}
    code{background-color:#1a1a1a !important;color:#e10600 !important;border:1px solid #2a2a2a !important;}
    .stSpinner>div{border-top-color:#e10600 !important;}
    [data-testid="stRadio"] label{color:#cccccc !important;}
    ::-webkit-scrollbar{width:6px;}
    ::-webkit-scrollbar-track{background:#0f0f0f;}
    ::-webkit-scrollbar-thumb{background:#333;border-radius:3px;}
    ::-webkit-scrollbar-thumb:hover{background:#e10600;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "cached_data" not in st.session_state:
    st.session_state.cached_data = None
if "run_count" not in st.session_state:
    st.session_state.run_count = 0

# ── Load long-term memory ──────────────────────────────────────
memory = load_memory()

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem;">
        <span style="font-size:2.5rem;">🏎️</span>
        <h2 style="margin:0.5rem 0 0;font-size:1.1rem;font-weight:700;color:white;">F1 Strategy Agent</h2>
        <p style="color:#555;font-size:12px;margin:0;">Powered by Gemini 2.5 Flash</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:1rem;margin:1rem 0;">
        <p style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.75rem;">Next Race</p>
        <p style="color:white;font-weight:700;font-size:16px;margin:0;">🏁 British Grand Prix</p>
        <p style="color:#888;font-size:13px;margin:0.25rem 0 0;">📍 Silverstone · Round 9</p>
        <p style="color:#e10600;font-size:13px;font-weight:600;margin:0.25rem 0 0;">📅 July 5, 2026</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<p style='color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin:1rem 0 0.5rem;'>Your Pick Style</p>", unsafe_allow_html=True)
    preference = st.radio(
        "preference",
        options=["safe", "balanced", "aggressive"],
        index=["safe", "balanced", "aggressive"].index(memory.get("risk_preference", "balanced")),
        format_func=lambda x: {"safe": "🛡️ Safe", "balanced": "⚖️ Balanced", "aggressive": "🎲 Aggressive"}[x],
        label_visibility="collapsed"
    )

    if st.session_state.run_count > 0:
        st.markdown(f"""
        <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:1rem;margin:1rem 0;">
            <p style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.5rem;">Session Memory</p>
            <p style="color:#ccc;font-size:13px;margin:0.3rem 0;">🔄 Runs this session: {st.session_state.run_count}</p>
            <p style="color:#ccc;font-size:13px;margin:0.3rem 0;">💾 Total runs ever: {memory.get('runs', 0)}</p>
            <p style="color:#ccc;font-size:13px;margin:0.3rem 0;">🎯 Saved preference: {memory.get('risk_preference', 'balanced')}</p>
        </div>""", unsafe_allow_html=True)

    if st.button("🔄 Refresh Race Data", use_container_width=True):
        st.session_state.cached_data = None
        st.info("Data cache cleared — next run will re-fetch all data.")

# ── Main area ──────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(90deg,#e10600,#ff4422,#e10600);height:3px;border-radius:2px;margin-bottom:1.5rem;"></div>
<h1 style="font-size:2.2rem;font-weight:800;letter-spacing:-0.5px;margin-bottom:0.25rem;">F1 Race Strategy Agent</h1>
<p style="color:#555;font-size:0.95rem;margin-bottom:1.5rem;">
  Two-agent system · Live 2026 data · Gemini 2.5 Flash ·
  <span style="color:#e10600;">●</span> Data Agent + Strategy Agent
</p>""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

if "live_standings" not in st.session_state:
    from agent.tools import get_driver_standings, get_upcoming_race
    st.session_state.live_standings = get_driver_standings()
    st.session_state.live_race = get_upcoming_race()

standings = st.session_state.live_standings
race = st.session_state.live_race

if standings and "error" not in standings[0]:
    p1, p2, p3 = standings[0], standings[1], standings[2]
    col1.metric("🏆 Leader", p1["name"].split()[-1], f"{int(p1['points'])} pts")
    col2.metric("🥈 P2", p2["name"].split()[-1], f"{int(p2['points'])} pts")
    col3.metric("🥉 P3", p3["name"].split()[-1], f"{int(p3['points'])} pts")
else:
    col1.metric("🏆 Leader", "—", "—")
    col2.metric("🥈 P2", "—", "—")
    col3.metric("🥉 P3", "—", "—")

race_name = race.get("race_name", "British GP") if "error" not in race else "British GP"
circuit = race.get("circuit_name", "Silverstone") if "error" not in race else "Silverstone"
col4.metric("🏁 Next Race", race_name.replace(" Grand Prix", " GP"), circuit)

st.markdown("<div style='margin:1.5rem 0;'></div>", unsafe_allow_html=True)

# ── Guardrail ──────────────────────────────────────────────────
F1_KEYWORDS = [
    "driver", "race", "lineup", "circuit", "grand prix", "f1", "formula",
    "team", "standings", "strategy", "silverstone", "qualify", "lap",
    "pit", "tyre", "tire", "constructor", "season", "antonelli", "russell",
    "hamilton", "verstappen", "norris", "piastri", "leclerc"
]

def is_f1_query(text: str) -> bool:
    return any(word in text.lower() for word in F1_KEYWORDS)

def validate_budget(text: str):
    match = re.search(r'total budget used[:\s*]+(\d+)', text.lower())
    if match:
        used = int(match.group(1))
        return used <= 80, used
    return None, None

# ── Input ──────────────────────────────────────────────────────
query = st.text_input(
    "Ask the agent:",
    value="Build me the best value 5-driver lineup for the upcoming F1 race. Stay within the 80-credit budget.",
    placeholder="e.g. Who has the best form at Silverstone?"
)

if st.button("🏁 Generate Lineup", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a question.")
        st.stop()

    if not is_f1_query(query):
        st.error("⛔ This agent only answers F1-related questions.")
        st.stop()

    col_a, col_b = st.columns(2)
    with col_a:
        agent1_status = st.empty()
    with col_b:
        agent2_status = st.empty()

    agent1_status.info("🔵 **Data Agent** — collecting live F1 data...")

    call_log.clear()

    from agent.data_agent import run_data_agent
    from agent.strategy_agent import run_strategy_agent

    # ── Agent 1: Data collection (no Gemini calls, always fast) ──
    if st.session_state.cached_data is None:
        with st.spinner("🔵 Data Agent collecting live F1 data..."):
            try:
                data_summary = run_data_agent()
                st.session_state.cached_data = data_summary
                st.session_state.tool_trace = list(call_log)
                agent1_status.success("🔵 **Data Agent** — data collection complete ✓")
            except Exception as e:
                st.error(f"Data collection failed: {str(e)}")
                st.stop()
    else:
        data_summary = st.session_state.cached_data
        agent1_status.success("🔵 **Data Agent** — using cached race data ✓")

    # ── Agent: Strategy reasoning (one Gemini call) ────────────
    try:
        with st.spinner("🔴 Strategy Agent building lineup..."):
            lineup = run_strategy_agent(
                race_data=data_summary,
                user_query=query,
                preference=preference,
                history=st.session_state.history
            )
        agent2_status.success("🔴 **Strategy Agent** — lineup built ✓")
    except Exception as e:
        if "429" in str(e):
            st.error("⏳ Rate limit reached on Strategy Agent. Data is cached — wait 30 seconds and click Generate Lineup again.")
        else:
            st.error(f"Strategy Agent failed: {str(e)}")
        st.stop()

    agent1_status.success("🔵 **Data Agent** — data collection complete ✓")
    agent2_status.success("🔴 **Strategy Agent** — lineup built ✓")

    save_memory(preference=preference, race_name="British Grand Prix")
    st.session_state.history.append({"role": "user", "content": query})
    st.session_state.history.append({"role": "assistant", "content": lineup})
    st.session_state.run_count += 1

    st.markdown("---")
    st.markdown(lineup)
    st.markdown("---")

    is_valid, budget_used = validate_budget(lineup)
    if budget_used is not None:
        if is_valid:
            st.success(f"✅ Budget guardrail passed — {budget_used} / 80 credits used")
        else:
            st.error(f"⚠️ Budget guardrail failed — {budget_used} / 80 credits (agent should revise)")
    else:
        st.info("ℹ️ Budget total not detected in response")

    trace = st.session_state.get("tool_trace", [])
    with st.expander(f"🔍 Data Agent reasoning trace — {len(trace)} tool calls made"):
        for i, entry in enumerate(trace, 1):
            st.markdown(f"`step {i}` {entry}")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding-top:1rem;border-top:1px solid #1a1a1a;
            text-align:center;color:#333;font-size:12px;">
    F1 Strategy Agent · Two-agent system · Gemini 2.5 Flash · Jolpica F1 API
</div>""", unsafe_allow_html=True)