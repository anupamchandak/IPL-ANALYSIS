import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.metrics import get_player_advanced_bowling
from utils.visualizations import plot_dismissal_types
from config import TEAM_FULL_NAMES, TEAM_COLORS, SEASONS
import plotly.express as px

init_page("Bowler Analysis")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_deliv = data['deliveries']
df_bowl_sum = data['bowling_summary']

# ----------------- BOWLER NAVIGATION -----------------
st.sidebar.markdown("### Bowler Filter")
team_choice = st.sidebar.selectbox("Filter by Team", ["All"] + sorted(list(TEAM_FULL_NAMES.keys())), format_func=lambda x: f"{x} - {TEAM_FULL_NAMES[x]}" if x != "All" else "All Teams")
selected_season = st.sidebar.selectbox("Select Season", ["All Seasons"] + SEASONS)

# Get unique bowlers
if team_choice == "All":
    bowlers_list = sorted(df_deliv['bowler'].unique())
else:
    bowlers_list = sorted(df_deliv[df_deliv['bowling_team'] == team_choice]['bowler'].unique())

selected_bowler = st.sidebar.selectbox("Select Bowler", bowlers_list)

player_team_row = df_deliv[df_deliv['bowler'] == selected_bowler]
team_code = player_team_row['bowling_team'].iloc[0] if not player_team_row.empty else "N/A"
primary_color, secondary_color = TEAM_COLORS.get(team_code, ('#38bdf8', '#a855f7'))

# Banner
render_header_banner(
    f"{selected_bowler}",
    f"Detailed bowler analysis, phase economies, and dynamic timelines for {selected_season}."
)

# ----------------- CALCULATE STATS -----------------
season_val = None if selected_season == "All Seasons" else selected_season
bowl_metrics = get_player_advanced_bowling(df_deliv, selected_bowler, season_val)

if not bowl_metrics:
    st.warning("No bowling records found for this bowler in the selected range.")
    st.stop()

# ----------------- DISPLAY -----------------
col_p1, col_p2 = st.columns([1, 2])

with col_p1:
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.5); padding: 24px; border-radius: 16px; border: 1.5px solid {primary_color}33; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 5rem; line-height: 1;">🎯</div>
            <h4 style="margin: 12px 0 4px 0; color: #ffffff;">{selected_bowler}</h4>
            <div style="font-size: 0.95rem; color: #a855f7; font-weight: 600;">Bowler</div>
            <hr style="border: 0; border-top: 1px solid #1e293b; margin: 15px 0;">
            <div style="text-align: left; font-size: 0.9rem; color: #cbd5e1;">
                <p style="margin: 4px 0;">🏢 Franchise: <b>{TEAM_FULL_NAMES.get(team_code, 'N/A')}</b></p>
                <p style="margin: 4px 0;">⚡ Economy: <b>{bowl_metrics['economy']:.2f}</b></p>
                <p style="margin: 4px 0;">🏏 Strike Rate: <b>{bowl_metrics['strike_rate']:.2f}</b></p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_p2:
    st.markdown("##### 📊 Advanced Bowling Metrics Summary")
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    with col_b1:
        render_kpi_card(str(bowl_metrics['wickets']), "Wickets Taken", "🎯")
        render_kpi_card(f"{bowl_metrics['powerplay_rating']:.1f}/10", "PP Bowling Rating", "🛡️")
    with col_b2:
        render_kpi_card(str(bowl_metrics['economy']), "Economy", "📉")
        render_kpi_card(f"{bowl_metrics['death_rating']:.1f}/10", "Death Bowling Rating", "🔥")
    with col_b3:
        render_kpi_card(str(bowl_metrics['strike_rate']), "Strike Rate", "⚡")
        render_kpi_card(f"{bowl_metrics['dot_ball_pct']:.1f}%", "Dot Ball %", "🛑")
    with col_b4:
        render_kpi_card(str(bowl_metrics['overs']), "Overs Bowled", "🏏")
        render_kpi_card(f"{bowl_metrics['pressure_bowling_score']:.1f}", "Pressure Score", "🧬")

# ----------------- SPLITS AND VISUALS -----------------
st.markdown('<div class="section-header">Performance Splits & Timelines</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎯 Opposition & Venue Splits", "🛡️ Phase Distribution", "🗓️ Match History"])

df_bowl = df_deliv[df_deliv['bowler'] == selected_bowler].copy()
if season_val:
    df_bowl = df_bowl[df_bowl['season'] == season_val]

with tab1:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        opp_bowl = df_bowl.groupby('batting_team')['is_bowler_wicket'].sum().reset_index()
        fig_opp = px.bar(
            opp_bowl, x='batting_team', y='is_bowler_wicket',
            title="Wickets Taken vs Opposition Teams",
            labels={'batting_team': 'Opponent', 'is_bowler_wicket': 'Wickets'},
            color_discrete_sequence=[primary_color]
        )
        fig_opp.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_opp, use_container_width=True)
    with col_c2:
        venue_bowl = df_bowl.groupby('venue')['is_bowler_wicket'].sum().reset_index()
        venue_bowl = venue_bowl.sort_values(by='is_bowler_wicket', ascending=False).head(8)
        fig_ven = px.bar(
            venue_bowl, y='venue', x='is_bowler_wicket', orientation='h',
            title="Wickets Taken by Venue (Top 8)",
            labels={'venue': 'Venue', 'is_bowler_wicket': 'Wickets'},
            color_discrete_sequence=[secondary_color]
        )
        fig_ven.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_ven, use_container_width=True)

with tab2:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        # Phase wise wickets
        phase_wkts = df_bowl.groupby('phase')['is_bowler_wicket'].sum().reset_index()
        fig_p_wkts = px.pie(
            phase_wkts, names='phase', values='is_bowler_wicket',
            title="Wickets by Over Phase",
            color_discrete_sequence=px.colors.sequential.Electric
        )
        fig_p_wkts.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_p_wkts, use_container_width=True)
    with col_d2:
        # Phase wise economy
        phase_econ_list = []
        for phase in ['Powerplay', 'Middle', 'Death']:
            df_p = df_bowl[df_bowl['phase'] == phase]
            p_runs = df_p['bowler_runs'].sum()
            p_balls = df_p['is_legal_ball'].sum()
            p_econ = (p_runs / (p_balls / 6.0)) if p_balls > 0 else 0.0
            phase_econ_list.append({'Phase': phase, 'Economy': p_econ})
        
        fig_p_econ = px.bar(
            pd.DataFrame(phase_econ_list), x='Phase', y='Economy',
            title="Economy Rate by Phase",
            color='Phase', color_discrete_map={'Powerplay': '#38bdf8', 'Middle': '#a855f7', 'Death': '#ec4899'}
        )
        fig_p_econ.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_p_econ, use_container_width=True)

with tab3:
    st.markdown("##### 🗓️ Bowling Innings Match History")
    match_list = []
    
    for m_id in sorted(list(df_bowl['match_id'].unique())):
        df_m = df_bowl[df_bowl['match_id'] == m_id]
        date = df_m.iloc[0]['date']
        opp = df_m.iloc[0]['batting_team']
        runs_c = df_m['bowler_runs'].sum()
        balls_b = df_m['is_legal_ball'].sum()
        wkts_t = df_m['is_bowler_wicket'].sum()
        overs_b = f"{balls_b // 6}.{balls_b % 6}"
        
        match_list.append({
            'Match ID': m_id,
            'Date': date,
            'Opponent': opp,
            'Overs': overs_b,
            'Runs Conceded': runs_c,
            'Wickets': wkts_t,
            'Economy': round(runs_c / (balls_b / 6.0), 2) if balls_b > 0 else 0.0
        })
        
    df_timeline = pd.DataFrame(match_list)
    if not df_timeline.empty:
        st.dataframe(df_timeline.sort_values(by='Match ID', ascending=False), use_container_width=True, hide_index=True)
        
        fig_timeline = px.line(
            df_timeline, x='Match ID', y='Wickets', markers=True,
            title="Wickets Timeline", color_discrete_sequence=[secondary_color]
        )
        fig_timeline.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No match history available.")
