import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.metrics import get_player_advanced_batting, get_player_advanced_bowling
from utils.visualizations import plot_multi_radar_chart
from config import TEAM_COLORS, SEASONS
import plotly.graph_objects as go

init_page("Player Comparison")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_deliv = data['deliveries']

# ----------------- PLAYER SELECTION -----------------
st.sidebar.markdown("### Player Filter")
comparison_type = st.sidebar.radio("Comparison Type", ["🏏 Batsmen", "🎯 Bowlers"])
selected_season = st.sidebar.selectbox("Select Season context", ["All Seasons"] + SEASONS)

# Get unique lists
if comparison_type == "🏏 Batsmen":
    players_list = sorted(df_deliv['striker'].unique())
    label_a = "Select Batsman A"
    label_b = "Select Batsman B"
else:
    players_list = sorted(df_deliv['bowler'].unique())
    label_a = "Select Bowler A"
    label_b = "Select Bowler B"

player_a = st.sidebar.selectbox(label_a, players_list, index=0)
player_b = st.sidebar.selectbox(label_b, players_list, index=1 if len(players_list) > 1 else 0)

if player_a == player_b:
    st.warning("Please select two different players.")
    st.stop()

# Banner
render_header_banner(
    "Player Comparison",
    f"Side-by-side visual analysis comparing **{player_a}** vs **{player_b}** in **{selected_season}**"
)

# ----------------- CALCULATIONS -----------------
season_val = None if selected_season == "All Seasons" else selected_season

if comparison_type == "🏏 Batsmen":
    metrics_a = get_player_advanced_batting(df_deliv, player_a, season_val)
    metrics_b = get_player_advanced_batting(df_deliv, player_b, season_val)
    
    if not metrics_a or not metrics_b:
        st.error("One of the selected players has no batting records in this range.")
        st.stop()
        
    # Compare Batting
    comp_data = {
        'Parameter': ['Total Runs', 'Batting Average', 'Strike Rate', 'Dot Ball %', 'Boundary %', 'Control %', 'Attack %', 'Powerplay SR', 'Death SR'],
        player_a: [
            metrics_a['runs'], metrics_a['average'], metrics_a['strike_rate'],
            f"{metrics_a['dot_ball_pct']:.1f}%", f"{metrics_a['boundary_pct']:.1f}%",
            f"{metrics_a['control_pct']:.1f}%", f"{metrics_a['attack_pct']:.1f}%",
            metrics_a['powerplay_sr'], metrics_a['death_sr']
        ],
        player_b: [
            metrics_b['runs'], metrics_b['average'], metrics_b['strike_rate'],
            f"{metrics_b['dot_ball_pct']:.1f}%", f"{metrics_b['boundary_pct']:.1f}%",
            f"{metrics_b['control_pct']:.1f}%", f"{metrics_b['attack_pct']:.1f}%",
            metrics_b['powerplay_sr'], metrics_b['death_sr']
        ]
    }
    
    # Normalise values for radar chart (1-10 scale)
    categories = ['Average Rating', 'Strike Rate Rating', 'Control', 'Attack', 'Powerplay', 'Death']
    
    # Heuristics
    val_a = [
        min(metrics_a['average'] / 5.0, 10.0), min(metrics_a['strike_rate'] / 18.0, 10.0),
        metrics_a['control_pct'] / 10.0, metrics_a['attack_pct'] / 5.0,
        min(metrics_a['powerplay_sr'] / 18.0, 10.0), min(metrics_a['death_sr'] / 22.0, 10.0)
    ]
    val_b = [
        min(metrics_b['average'] / 5.0, 10.0), min(metrics_b['strike_rate'] / 18.0, 10.0),
        metrics_b['control_pct'] / 10.0, metrics_b['attack_pct'] / 5.0,
        min(metrics_b['powerplay_sr'] / 18.0, 10.0), min(metrics_b['death_sr'] / 22.0, 10.0)
    ]
    
else:
    metrics_a = get_player_advanced_bowling(df_deliv, player_a, season_val)
    metrics_b = get_player_advanced_bowling(df_deliv, player_b, season_val)
    
    if not metrics_a or not metrics_b:
        st.error("One of the selected players has no bowling records in this range.")
        st.stop()
        
    comp_data = {
        'Parameter': ['Wickets Taken', 'Overs Bowled', 'Economy Rate', 'Bowling Average', 'Strike Rate', 'Dot Ball %', 'Boundary Conceded %', 'Pressure Score'],
        player_a: [
            metrics_a['wickets'], metrics_a['overs'], metrics_a['economy'], metrics_a['average'],
            metrics_a['strike_rate'], f"{metrics_a['dot_ball_pct']:.1f}%", f"{metrics_a['boundary_conceded_pct']:.1f}%",
            metrics_a['pressure_bowling_score']
        ],
        player_b: [
            metrics_b['wickets'], metrics_b['overs'], metrics_b['economy'], metrics_b['average'],
            metrics_b['strike_rate'], f"{metrics_b['dot_ball_pct']:.1f}%", f"{metrics_b['boundary_conceded_pct']:.1f}%",
            metrics_b['pressure_bowling_score']
        ]
    }
    
    # Normalise values for bowling radar (1-10)
    categories = ['Wicket Rating', 'Economy Control', 'Strike Rate', 'Dot Pressure', 'Powerplay Skill', 'Death Skill']
    val_a = [
        min(metrics_a['wickets'] * 0.5, 10.0), max(10.0 - metrics_a['economy'], 1.0),
        max(10.0 - metrics_a['strike_rate'] * 0.25, 1.0), metrics_a['dot_ball_pct'] / 10.0,
        metrics_a['powerplay_rating'], metrics_a['death_rating']
    ]
    val_b = [
        min(metrics_b['wickets'] * 0.5, 10.0), max(10.0 - metrics_b['economy'], 1.0),
        max(10.0 - metrics_b['strike_rate'] * 0.25, 1.0), metrics_b['dot_ball_pct'] / 10.0,
        metrics_b['powerplay_rating'], metrics_b['death_rating']
    ]

# Render stats table
st.markdown('<div class="section-header">Performance Metrics Comparison</div>', unsafe_allow_html=True)
st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

# Render Radar chart overlay
st.markdown('<div class="section-header">Skills Radar Overlay Comparison</div>', unsafe_allow_html=True)
values_dict = {player_a: val_a, player_b: val_b}
st.plotly_chart(plot_multi_radar_chart(categories, values_dict, "Overlay Skills Comparison Profile"), use_container_width=True)
