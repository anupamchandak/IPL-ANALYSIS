import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.metrics import get_player_advanced_batting
from utils.visualizations import plot_dismissal_types
from config import TEAM_FULL_NAMES, TEAM_COLORS, SEASONS
import plotly.express as px

init_page("Player Explorer")

# Load and preprocess datasets
df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("Roster or deliveries data not available.")
    st.stop()

df_deliv = data['deliveries']
df_bat_sum = data['batting_summary']

# ----------------- PLAYER NAVIGATION -----------------
st.sidebar.markdown("### Player Filter")
team_choice = st.sidebar.selectbox("Filter by Team", ["All"] + sorted(list(TEAM_FULL_NAMES.keys())), format_func=lambda x: f"{x} - {TEAM_FULL_NAMES[x]}" if x != "All" else "All Teams")
selected_season = st.sidebar.selectbox("Select Season", ["All Seasons"] + SEASONS)

# Get unique strikers
if team_choice == "All":
    players_list = sorted(df_deliv['striker'].unique())
else:
    players_list = sorted(df_deliv[df_deliv['batting_team'] == team_choice]['striker'].unique())

selected_player = st.sidebar.selectbox("Select Player", players_list)

# Find corresponding team
player_team_row = df_deliv[df_deliv['striker'] == selected_player]
team_code = player_team_row['batting_team'].iloc[0] if not player_team_row.empty else "N/A"
primary_color, secondary_color = TEAM_COLORS.get(team_code, ('#38bdf8', '#a855f7'))

# Banner
render_header_banner(
    f"{selected_player}",
    f"Detailed batsman explorer splitting performance by opposition, venue, and over phase for {selected_season}."
)

# ----------------- CALCULATE PLAYER STATS -----------------
season_val = None if selected_season == "All Seasons" else selected_season
bat_metrics = get_player_advanced_batting(df_deliv, selected_player, season_val)

if not bat_metrics:
    st.warning("No batting records found for this player in the selected time range.")
    st.stop()

# ----------------- PROFILE DISPLAY -----------------
col_p1, col_p2 = st.columns([1, 2])

with col_p1:
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.5); padding: 24px; border-radius: 16px; border: 1.5px solid {primary_color}33; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 5rem; line-height: 1;">🏏</div>
            <h4 style="margin: 12px 0 4px 0; color: #ffffff;">{selected_player}</h4>
            <div style="font-size: 0.95rem; color: #38bdf8; font-weight: 600;">Batsman</div>
            <hr style="border: 0; border-top: 1px solid #1e293b; margin: 15px 0;">
            <div style="text-align: left; font-size: 0.9rem; color: #cbd5e1;">
                <p style="margin: 4px 0;">🏢 Franchise: <b>{TEAM_FULL_NAMES.get(team_code, 'N/A')}</b></p>
                <p style="margin: 4px 0;">⚡ Strike Rate: <b>{bat_metrics['strike_rate']:.2f}</b></p>
                <p style="margin: 4px 0;">📈 Average: <b>{bat_metrics['average']:.2f}</b></p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_p2:
    st.markdown("##### 📊 Advanced Batting Metrics Summary")
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    with col_b1:
        render_kpi_card(str(bat_metrics['runs']), "Runs Scored", "🏃")
        render_kpi_card(f"{bat_metrics['control_pct']:.1f}%", "Control Rating", "🎯")
    with col_b2:
        render_kpi_card(str(bat_metrics['average']), "Average", "📈")
        render_kpi_card(f"{bat_metrics['attack_pct']:.1f}%", "Attack Rating", "⚔️")
    with col_b3:
        render_kpi_card(str(bat_metrics['strike_rate']), "Strike Rate", "⚡")
        render_kpi_card(f"{bat_metrics['dot_ball_pct']:.1f}%", "Dot Ball %", "🛑")
    with col_b4:
        render_kpi_card(str(bat_metrics['balls']), "Balls Faced", "🏏")
        render_kpi_card(f"{bat_metrics['consistency_rating']:.1f}/10", "Consistency Rating", "🧬")

# ----------------- SPLITS AND VISUALIZATIONS -----------------
st.markdown('<div class="section-header">Performance Splits & Visualizations</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏏 Splits Analysis", "🎯 Wicket Dismissals", "🗓️ Match History"])

df_bat = df_deliv[df_deliv['striker'] == selected_player].copy()
if season_val:
    df_bat = df_bat[df_bat['season'] == season_val]

with tab1:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        opp_bat = df_bat.groupby('bowling_team')['runs_of_bat'].sum().reset_index()
        fig_opp = px.bar(
            opp_bat, x='bowling_team', y='runs_of_bat',
            title="Runs Scored vs Opposition Teams",
            labels={'bowling_team': 'Opponent', 'runs_of_bat': 'Runs'},
            color_discrete_sequence=[primary_color]
        )
        fig_opp.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_opp, use_container_width=True)
    with col_c2:
        venue_bat = df_bat.groupby('venue')['runs_of_bat'].sum().reset_index()
        venue_bat = venue_bat.sort_values(by='runs_of_bat', ascending=False).head(8)
        fig_ven = px.bar(
            venue_bat, y='venue', x='runs_of_bat', orientation='h',
            title="Runs Scored by Venue (Top 8)",
            labels={'venue': 'Venue', 'runs_of_bat': 'Runs'},
            color_discrete_sequence=[secondary_color]
        )
        fig_ven.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_ven, use_container_width=True)

with tab2:
    df_out = df_deliv[df_deliv['player_dismissed'] == selected_player]
    if season_val:
        df_out = df_out[df_out['season'] == season_val]
        
    if not df_out.empty:
        st.plotly_chart(plot_dismissal_types(df_out, "How Batsman Got Out"), use_container_width=True)
    else:
        st.info("No dismissals recorded for this batsman (remained Not Out in all innings).")

with tab3:
    st.markdown("##### 🗓️ Innings-by-Innings Match Timeline")
    match_list = []
    
    for m_id in sorted(list(df_bat['match_id'].unique())):
        df_m = df_bat[df_bat['match_id'] == m_id]
        date = df_m.iloc[0]['date']
        opp = df_m.iloc[0]['bowling_team']
        runs_s = df_m['runs_of_bat'].sum()
        balls_s = df_m['is_legal_ball'].sum()
        
        # Check if dismissed
        df_out_m = df_deliv[(df_deliv['match_id'] == m_id) & (df_deliv['player_dismissed'] == selected_player)]
        dismissal = df_out_m.iloc[0]['wicket_type'] if not df_out_m.empty else "Not Out"
        
        match_list.append({
            'Match ID': m_id,
            'Date': date,
            'Opponent': opp,
            'Runs Scored': runs_s,
            'Balls Faced': balls_s,
            'Dismissal': dismissal,
            'Strike Rate': round(runs_s / balls_s * 100, 1) if balls_s > 0 else 0.0
        })
        
    df_timeline = pd.DataFrame(match_list)
    if not df_timeline.empty:
        st.dataframe(df_timeline.sort_values(by='Match ID', ascending=False), use_container_width=True, hide_index=True)
        
        # Plot timeline
        fig_timeline = px.line(
            df_timeline, x='Match ID', y='Runs Scored', markers=True,
            title="Runs Timeline", color_discrete_sequence=[primary_color]
        )
        fig_timeline.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No match history available.")
