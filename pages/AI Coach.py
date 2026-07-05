import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.recommendation_engine import generate_team_recommendations
from config import TEAM_FULL_NAMES, TEAM_COLORS, SEASONS
import plotly.express as px

init_page("AI Coach")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_deliv = data['deliveries']
df_batting = data['batting_summary']
df_bowling = data['bowling_summary']

# ----------------- TEAM SELECTION -----------------
teams_list = sorted(list(TEAM_FULL_NAMES.keys()))
selected_team_code = st.sidebar.selectbox("Select Franchise", teams_list, format_func=lambda x: f"{x} - {TEAM_FULL_NAMES[x]}")
selected_season = st.sidebar.selectbox("Select Season context", ["All Seasons"] + SEASONS)

team_name = TEAM_FULL_NAMES[selected_team_code]
primary_color, secondary_color = TEAM_COLORS.get(selected_team_code, ('#38bdf8', '#a855f7'))

# Banner
render_header_banner(
    f"🤖 AI Coach - {team_name}",
    f"Statistically derived coaching directives and roster improvements for {selected_season}."
)

st.markdown("""
    > **How it works:** The AI Coach analyses ball-by-ball deliveries, match outcomes, and individual player stats. 
    > It compares your franchise's parameters (Powerplay scoring rate, death-overs economy, collapse frequency, etc.) 
    > against the tournament-wide average to highlight specific strengths, weaknesses, and player-level recommendations.
""", unsafe_allow_html=True)

# Generate recommendations
season_val = None if selected_season == "All Seasons" else selected_season
recs = generate_team_recommendations(df_deliv, df_batting, df_bowling, selected_team_code, season_val)

# ----------------- SWOT -----------------
st.markdown("### 📊 SWOT Analysis Highlights")
col_s, col_w = st.columns(2)

with col_s:
    st.markdown(f"<h4 style='color: #10b981; font-weight:700;'>🟢 Strengths</h4>", unsafe_allow_html=True)
    for strength in recs['strengths']:
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.08); border-left: 4px solid #10b981; padding: 15px; border-radius: 4px; margin-bottom: 12px;">
                <h6 style="color: #10b981; margin: 0 0 6px 0; font-weight: 700; font-size: 1rem;">{strength['title']}</h6>
                <p style="margin: 0; color: #cbd5e1; font-size: 0.9rem;">{strength['desc']}</p>
            </div>
        """, unsafe_allow_html=True)

with col_w:
    st.markdown(f"<h4 style='color: #f43f5e; font-weight:700;'>🔴 Weaknesses</h4>", unsafe_allow_html=True)
    for weakness in recs['weaknesses']:
        st.markdown(f"""
            <div style="background: rgba(244, 63, 94, 0.08); border-left: 4px solid #f43f5e; padding: 15px; border-radius: 4px; margin-bottom: 12px;">
                <h6 style="color: #f43f5e; margin: 0 0 6px 0; font-weight: 700; font-size: 1rem;">{weakness['title']}</h6>
                <p style="margin: 0; color: #cbd5e1; font-size: 0.9rem;">{weakness['desc']}</p>
            </div>
        """, unsafe_allow_html=True)

# ----------------- STRATEGIES -----------------
st.markdown("### 💡 Recommended Strategies & Directives")
st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.4); border: 1.5px solid {primary_color}44; border-radius: 12px; padding: 24px;">
        <h5 style="color: #ffffff; margin-top:0; font-weight:700; font-size: 1.15rem; border-bottom: 1px solid #1e293b; padding-bottom: 8px;">
            🎯 Actionable Coaching Directive
        </h5>
        <ul style="margin-top: 15px; color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
            {"".join([f"<li style='margin-bottom: 10px;'>{item}</li>" for item in recs['strategies']])}
        </ul>
    </div>
""", unsafe_allow_html=True)
st.write("")
