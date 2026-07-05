import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.visualizations import (
    plot_runs_distribution, plot_dismissal_sunburst, 
    plot_boundary_wheel, plot_win_margins, plot_player_scatter
)
from config import SEASONS, TEAM_FULL_NAMES
import plotly.express as px

# 1. Initialize Page and Theme
init_page("Home Dashboard")

# 2. Ingest and Process master deliveries dataset (Cached)
df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries datasets found in the dataset directory.")
    st.stop()

# Extracted derived tables
df_deliv = data['deliveries']
df_matches = data['matches']
df_team_sum = data['team_summary']
df_bat_sum = data['batting_summary']
df_bowl_sum = data['bowling_summary']
df_field_sum = data['fielding_summary']
df_venue_sum = data['venue_summary']

# ----------------- SEASON FILTER -----------------
st.sidebar.markdown("### Dashboard Filters")
selected_season = st.sidebar.selectbox("Select Season", ["All Seasons"] + SEASONS)

# Filter summaries by season
if selected_season == "All Seasons":
    df_deliv_f = df_deliv
    df_matches_f = df_matches
    df_bat_f = data['player_batting'] # Aggregated Career Batting
    df_bowl_f = data['player_bowling'] # Aggregated Career Bowling
    
    # Rename columns to match standard keys for leaders
    df_bat_f = df_bat_f.rename(columns={'batsman': 'batsman'})
    df_bowl_f = df_bowl_f.rename(columns={'bowler': 'bowler'})
else:
    df_deliv_f = df_deliv[df_deliv['season'] == selected_season]
    df_matches_f = df_matches[df_matches['season'] == selected_season]
    df_bat_f = df_bat_sum[df_bat_sum['season'] == selected_season]
    df_bowl_f = df_bowl_sum[df_bowl_sum['season'] == selected_season]

# Banner
render_header_banner(
    f"IPL Analytics Hub - {selected_season}",
    "Dynamically derived statistics, advanced player DNA, and SWOT recommendations from ball-by-ball datasets."
)

# ----------------- TOURNAMENT KPIs -----------------
st.markdown('<div class="section-header">Tournament Overview KPIs</div>', unsafe_allow_html=True)

total_matches = df_matches_f.shape[0]
num_teams = df_deliv_f['batting_team'].nunique()

total_runs = df_deliv_f['total_runs'].sum()
total_wickets = df_deliv_f['is_wicket'].sum()
total_sixes = df_deliv_f['is_six'].sum()
total_fours = df_deliv_f['is_four'].sum()

# Averages
avg_first_ings = df_matches_f['first_ings_score'].mean()
highest_score_idx = df_matches_f['first_ings_score'].idxmax()
highest_score_row = df_matches_f.loc[highest_score_idx]
highest_score = f"{int(highest_score_row['first_ings_score'])}/{int(highest_score_row['first_ings_wkts'])} ({highest_score_row['team1']})"

lowest_score_idx = df_matches_f['first_ings_score'].idxmin()
lowest_score_row = df_matches_f.loc[lowest_score_idx]
lowest_score = f"{int(lowest_score_row['first_ings_score'])}/{int(lowest_score_row['first_ings_wkts'])} ({lowest_score_row['team1']})"

total_balls = df_deliv_f['is_legal_ball'].sum()
avg_run_rate = (total_runs / (total_balls / 6.0)) if total_balls > 0 else 0.0

chases = df_matches_f[
    (df_matches_f['match_winner'] == df_matches_f['team2']) & 
    (df_matches_f['margin_type'] == 'wickets')
]
if not chases.empty:
    highest_chase_row = df_matches_f.loc[chases['second_ings_score'].idxmax()]
    highest_chase = f"{int(highest_chase_row['second_ings_score'])}/{int(highest_chase_row['second_ings_wkts'])} by {highest_chase_row['team2']} vs {highest_chase_row['team1']}"
else:
    highest_chase = "N/A"

# Render KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card(f"{total_matches}", "Total Matches", "🏏")
    render_kpi_card(f"{avg_first_ings:.1f}", "Avg 1st Innings Score", "📈")
with col2:
    render_kpi_card(f"{num_teams}", "Active Teams", "🛡️")
    render_kpi_card(f"{highest_score}", "Highest Score", "🔥")
with col3:
    render_kpi_card(f"{total_runs:,}", "Total Runs Scored", "🏃")
    render_kpi_card(f"{lowest_score}", "Lowest Score", "📉")
with col4:
    render_kpi_card(f"{total_wickets}", "Wickets Fallen", "🎯")
    render_kpi_card(f"{avg_run_rate:.2f}", "Avg Run Rate", "⚡")

col_a, col_b = st.columns(2)
with col_a:
    render_kpi_card(f"{total_sixes} / {total_fours}", "Sixes / Fours", "💥")
with col_b:
    render_kpi_card(f"{highest_chase}", "Highest Successful Chase", "🏆")

# ----------------- STANDINGS & HONOURS -----------------
st.markdown('<div class="section-header">Standings & Honours</div>', unsafe_allow_html=True)

col_pt, col_caps = st.columns([2, 1.2])

with col_pt:
    if selected_season != "All Seasons":
        st.markdown(f"##### 🏆 Points Table - {selected_season}")
        df_season_pt = df_team_sum[df_team_sum['season'] == selected_season].sort_values(by='position')
        st.dataframe(
            df_season_pt[['position', 'team_name', 'played', 'wins', 'defeats', 'points', 'nrr']].style.format({'nrr': '{:+.3f}'}),
            use_container_width=True, hide_index=True
        )
    else:
        st.markdown("##### 🏆 Standings Summary (Aggregated wins over 5 seasons)")
        df_agg_pt = df_team_sum.groupby('team_name').agg({
            'played': 'sum', 'wins': 'sum', 'defeats': 'sum', 'points': 'sum'
        }).reset_index().sort_values(by='wins', ascending=False)
        st.dataframe(df_agg_pt, use_container_width=True, hide_index=True)

with col_caps:
    st.markdown("##### 🎖️ Individual Cap Leaders")
    # Orange Cap
    if not df_bat_f.empty:
        orange_cap = df_bat_f.sort_values(by='runs', ascending=False).iloc[0]
        # Handle column names difference for aggregated
        name_key = 'batsman' if 'batsman' in orange_cap else 'batsman'
        team_str = f" | Team: <b>{orange_cap['team']}</b>" if 'team' in orange_cap else ""
        avg_str = f"Avg: {orange_cap['average']:.2f} | " if 'average' in orange_cap else ""
        sr_str = f"SR: {orange_cap['strike_rate']:.2f}" if 'strike_rate' in orange_cap else ""
        
        st.markdown(f"""
            <div style="background: rgba(249, 115, 22, 0.15); border: 1.5px solid #f97316; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
                <div style="font-size: 0.8rem; color: #f97316; font-weight: 700; text-transform: uppercase;">🍊 Orange Cap Leader</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{orange_cap[name_key]}</div>
                <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 2px;">Runs: <b>{int(orange_cap['runs'])}</b>{team_str}</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">{avg_str}{sr_str}</div>
            </div>
        """, unsafe_allow_html=True)
        
    # Purple Cap
    if not df_bowl_f.empty:
        purple_cap = df_bowl_f.sort_values(by='wickets', ascending=False).iloc[0]
        name_key = 'bowler' if 'bowler' in purple_cap else 'bowler'
        team_str = f" | Team: <b>{purple_cap['team']}</b>" if 'team' in purple_cap else ""
        econ_str = f"Econ: {purple_cap['economy']:.2f} | " if 'economy' in purple_cap else ""
        sr_str = f"SR: {purple_cap['strike_rate']:.2f}" if 'strike_rate' in purple_cap else ""
        
        st.markdown(f"""
            <div style="background: rgba(168, 85, 247, 0.15); border: 1.5px solid #a855f7; border-radius: 12px; padding: 18px;">
                <div style="font-size: 0.8rem; color: #a855f7; font-weight: 700; text-transform: uppercase;">🔮 Purple Cap Leader</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{purple_cap[name_key]}</div>
                <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 2px;">Wickets: <b>{int(purple_cap['wickets'])}</b>{team_str}</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">{econ_str}{sr_str}</div>
            </div>
        """, unsafe_allow_html=True)

# ----------------- VISUALIZATIONS TABS -----------------
st.markdown('<div class="section-header">Tournament Insights</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏏 Scoring & Runs", "🎯 Dismissals & Margins", "📊 Player Comparison Scatter"])

with tab1:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.plotly_chart(plot_runs_distribution(df_deliv_f, "Ball-by-Ball Runs Distribution"), use_container_width=True)
    with col_c2:
        st.plotly_chart(plot_boundary_wheel(df_deliv_f, "Boundary Run Splits Wheel"), use_container_width=True)

with tab2:
    col_c3, col_c4 = st.columns(2)
    with col_c3:
        st.plotly_chart(plot_dismissal_sunburst(df_deliv_f, "Dismissals Breakdown by Over Phase"), use_container_width=True)
    with col_c4:
        st.plotly_chart(plot_win_margins(df_matches_f, "Tournament Win Margins Ranges"), use_container_width=True)

with tab3:
    st.plotly_chart(plot_player_scatter(df_bat_f, "Batsman Strike Rate vs Average Bubble Chart (Bubble size is total runs)"), use_container_width=True)

# ----------------- LEADERBOARDS -----------------
st.markdown('<div class="section-header">Top Players & Recent Matches</div>', unsafe_allow_html=True)
tab_bat, tab_bowl, tab_rec = st.tabs(["🏏 Top Batters", "🎯 Top Bowlers", "📜 Recent Matches"])

with tab_bat:
    if not df_bat_f.empty:
        cols_b = ['batsman', 'runs', 'average', 'strike_rate', 'high_score', 'sixes', 'fours']
        if 'team' in df_bat_f.columns:
            cols_b.insert(1, 'team')
        st.dataframe(df_bat_f[cols_b].sort_values(by='runs', ascending=False).head(15), use_container_width=True, hide_index=True)
        
with tab_bowl:
    if not df_bowl_f.empty:
        cols_bo = ['bowler', 'wickets', 'economy', 'avg', 'strike_rate', 'overs', 'dot_balls']
        if 'team' in df_bowl_f.columns:
            cols_bo.insert(1, 'team')
        st.dataframe(df_bowl_f[cols_bo].sort_values(by='wickets', ascending=False).head(15), use_container_width=True, hide_index=True)

with tab_rec:
    if not df_matches_f.empty:
        recent = df_matches_f.sort_values(by='match_id', ascending=False).head(10)
        rec_list = []
        for idx, row in recent.iterrows():
            winner = row['match_winner']
            margin = f"won by {int(row['margin_val'])} {row['margin_type']}" if row['margin_val'] > 0 else "won"
            rec_list.append({
                'Match ID': row['match_id'],
                'Season': row['season'],
                'Date': row['date'],
                'Teams': f"{row['team1']} vs {row['team2']}",
                'Venue': row['venue'],
                'Outcome': f"{winner} {margin}",
                'POTM': row['player_of_the_match']
            })
        st.dataframe(pd.DataFrame(rec_list), use_container_width=True, hide_index=True)
