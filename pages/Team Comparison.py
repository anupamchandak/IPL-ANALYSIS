import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.metrics import get_team_dna_metrics
from utils.visualizations import plot_multi_radar_chart
from config import TEAM_FULL_NAMES, TEAM_COLORS, SEASONS

init_page("Team Comparison")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']
df_team_sum = data['team_summary']

# ----------------- TEAM SELECTION -----------------
teams_list = sorted(list(TEAM_FULL_NAMES.keys()))
st.sidebar.markdown("### Select Teams & Season")
team_a = st.sidebar.selectbox("Team A", teams_list, index=0, format_func=lambda x: f"{x} - {TEAM_FULL_NAMES[x]}")
team_b = st.sidebar.selectbox("Team B", teams_list, index=1, format_func=lambda x: f"{x} - {TEAM_FULL_NAMES[x]}")
selected_season = st.sidebar.selectbox("Select Season context", ["All Seasons"] + SEASONS)

if team_a == team_b:
    st.warning("Please select two different teams.")
    st.stop()

# Banner
render_header_banner(
    "Team Comparison",
    f"Head-to-head performance parameters comparing **{TEAM_FULL_NAMES[team_a]}** vs **{TEAM_FULL_NAMES[team_b]}** in **{selected_season}**"
)

# Get metrics
season_val = None if selected_season == "All Seasons" else selected_season
metrics_a = get_team_dna_metrics(df_deliv, team_a, season_val)
metrics_b = get_team_dna_metrics(df_deliv, team_b, season_val)

color_a = TEAM_COLORS.get(team_a, ('#38bdf8',))[0]
color_b = TEAM_COLORS.get(team_b, ('#ec4899',))[0]

# ----------------- H2H SUMMARY -----------------
st.markdown('<div class="section-header">Head-to-Head History</div>', unsafe_allow_html=True)

h2h_matches = df_matches[
    ((df_matches['team1'] == team_a) & (df_matches['team2'] == team_b)) |
    ((df_matches['team2'] == team_a) & (df_matches['team1'] == team_b))
]
if season_val:
    h2h_matches = h2h_matches[h2h_matches['season'] == season_val]
    
total_h2h = h2h_matches.shape[0]
wins_a = h2h_matches[h2h_matches['match_winner'] == team_a].shape[0]
wins_b = h2h_matches[h2h_matches['match_winner'] == team_b].shape[0]

col1, col2, col3 = st.columns([1, 1.2, 1])
with col1:
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.5); padding: 20px; border-radius: 12px; border-top: 5px solid {color_a}; text-align: center;">
            <div style="font-size: 0.95rem; color: #94a3b8; font-weight: 600;">{team_a} Wins</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: #ffffff; margin-top: 4px;">{wins_a}</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div style="background: rgba(15,23,42,0.6); padding: 20px; border-radius: 12px; border: 1.5px dashed #475569; text-align: center;">
            <div style="font-size: 0.95rem; color: #cbd5e1; font-weight: 500;">Total Head-to-Head Matches</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #cbd5e1; margin-top: 4px;">{total_h2h}</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.5); padding: 20px; border-radius: 12px; border-top: 5px solid {color_b}; text-align: center;">
            <div style="font-size: 0.95rem; color: #94a3b8; font-weight: 600;">{team_b} Wins</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: #ffffff; margin-top: 4px;">{wins_b}</div>
        </div>
    """, unsafe_allow_html=True)

# ----------------- PARAMS -----------------
st.markdown('<div class="section-header">Phase Economy & Run Rates</div>', unsafe_allow_html=True)

comp_data = {
    'Parameter': [
        'Powerplay Batting Run Rate', 'Middle Overs Batting Run Rate', 'Death Overs Batting Run Rate',
        'Powerplay Bowling Economy', 'Middle Overs Bowling Economy', 'Death Overs Bowling Economy',
        'Win % (Overall)', 'Win % Chasing', 'Win % Defending'
    ],
    f'{team_a}': [
        f"{metrics_a['bat_rr_Powerplay']:.2f}", f"{metrics_a['bat_rr_Middle']:.2f}", f"{metrics_a['bat_rr_Death']:.2f}",
        f"{metrics_a['bowl_econ_Powerplay']:.2f}", f"{metrics_a['bowl_econ_Middle']:.2f}", f"{metrics_a['bowl_econ_Death']:.2f}",
        f"{metrics_a['win_pct']:.1f}%", f"{metrics_a['chasing_pct']:.1f}%", f"{metrics_a['defending_pct']:.1f}%"
    ],
    f'{team_b}': [
        f"{metrics_b['bat_rr_Powerplay']:.2f}", f"{metrics_b['bat_rr_Middle']:.2f}", f"{metrics_b['bat_rr_Death']:.2f}",
        f"{metrics_b['bowl_econ_Powerplay']:.2f}", f"{metrics_b['bowl_econ_Middle']:.2f}", f"{metrics_b['bowl_econ_Death']:.2f}",
        f"{metrics_b['win_pct']:.1f}%", f"{metrics_b['chasing_pct']:.1f}%", f"{metrics_b['defending_pct']:.1f}%"
    ]
}

st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

# Radar Chart
st.markdown('<div class="section-header">DNA Profile Radar Overlay</div>', unsafe_allow_html=True)

categories = ['Aggression', 'Consistency', 'Powerplay Batting', 'Middle Overs Batting', 'Death Overs Batting', 'Bowling Quality']
values_dict = {
    team_a: [
        metrics_a['aggression_score'], metrics_a['consistency_score'], metrics_a['powerplay_rating'],
        metrics_a['middle_overs_rating'], metrics_a['death_overs_rating'], metrics_a['bowling_rating']
    ],
    team_b: [
        metrics_b['aggression_score'], metrics_b['consistency_score'], metrics_b['powerplay_rating'],
        metrics_b['middle_overs_rating'], metrics_b['death_overs_rating'], metrics_b['bowling_rating']
    ]
}

st.plotly_chart(plot_multi_radar_chart(categories, values_dict, "Overlay DNA Profile"), use_container_width=True)
