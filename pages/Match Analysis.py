import streamlit as st
import pandas as pd
import numpy as np
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.visualizations import (
    plot_run_worm, plot_manhattan_chart, plot_momentum_timeline, 
    plot_partnership_network, plot_sankey_wickets
)
from models.prediction import estimate_win_probability
from config import TEAM_COLORS, SEASONS
import plotly.express as px
import plotly.graph_objects as go

init_page("Match Analysis")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']

# ----------------- MATCH SELECTION -----------------
st.sidebar.markdown("### Match selector")
selected_season = st.sidebar.selectbox("Select Season", SEASONS)

df_season_matches = df_matches[df_matches['season'] == selected_season].sort_values(by='match_id')

match_options = []
for idx, row in df_season_matches.iterrows():
    match_options.append({
        'id': int(row['match_id']),
        'label': f"Match {row['match_no']}: {row['team1']} vs {row['team2']} ({row['date']})"
    })

if not match_options:
    st.warning("No matches recorded for this season.")
    st.stop()
    
selected_match_label = st.sidebar.selectbox("Select Match", [m['label'] for m in match_options])
selected_match_id = next(m['id'] for m in match_options if m['label'] == selected_match_label)

match_row = df_season_matches[df_season_matches['match_id'] == selected_match_id].iloc[0]

team1 = match_row['team1']
team2 = match_row['team2']
winner = match_row['match_winner']
first_score = int(match_row['first_ings_score'])
first_wkts = int(match_row['first_ings_wkts'])
second_score = int(match_row['second_ings_score'])
second_wkts = int(match_row['second_ings_wkts'])

t1_color = TEAM_COLORS.get(team1, ('#38bdf8',))[0]
t2_color = TEAM_COLORS.get(team2, ('#ec4899',))[0]

# Banner
render_header_banner(
    f"{team1} vs {team2}",
    f"Match {match_row['match_no']} | {match_row['venue']} | Date: {match_row['date']}"
)

# ----------------- SCORECARD KPIs -----------------
col1, col2, col3 = st.columns([1, 1, 1.2])
with col1:
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.5); padding: 18px; border-radius: 12px; border-left: 5px solid {t1_color}; text-align: center;">
            <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">1st Innings - {team1}</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{first_score}/{first_wkts}</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.5); padding: 18px; border-radius: 12px; border-left: 5px solid {t2_color}; text-align: center;">
            <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">2nd Innings - {team2}</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{second_score}/{second_wkts}</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    margin_str = f"won by {int(match_row['margin_val'])} {match_row['margin_type']}" if match_row['margin_val'] > 0 else "won"
    st.markdown(f"""
        <div style="background: rgba(30,41,59,0.7); padding: 18px; border-radius: 12px; border: 1.5px solid #10b981; text-align: center; height: 100%;">
            <div style="font-size: 0.85rem; color: #10b981; font-weight: 700; text-transform: uppercase;">🏆 Winner</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 4px;">{winner}</div>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 2px;">{winner} {margin_str}</div>
        </div>
    """, unsafe_allow_html=True)

df_match_deliv = df_deliv[df_deliv['match_id'] == selected_match_id].copy()

if df_match_deliv.empty:
    st.warning("No deliveries recorded for this match.")
    st.stop()

# ----------------- SCORECARDS -----------------
st.markdown('<div class="section-header">Detailed Innings Scorecards</div>', unsafe_allow_html=True)

tab_ings1, tab_ings2 = st.tabs([f"🏏 {team1} Batting ({team2} Bowling)", f"🏏 {team2} Batting ({team1} Bowling)"])

with tab_ings1:
    df_ings1 = df_match_deliv[df_match_deliv['innings'] == 1].copy()
    
    # Batting
    bat_stats = []
    for batsman in df_ings1['striker'].unique():
        df_b = df_ings1[df_ings1['striker'] == batsman]
        runs_b = df_b['runs_of_bat'].sum()
        balls_b = df_b['is_legal_ball'].sum()
        fours_b = df_b['is_four'].sum()
        sixes_b = df_b['is_six'].sum()
        sr_b = (runs_b / balls_b * 100) if balls_b > 0 else 0.0
        
        df_out = df_ings1[df_ings1['player_dismissed'] == batsman]
        dismissal = df_out.iloc[0]['wicket_type'] if not df_out.empty else "not out"
        
        bat_stats.append({
            'Batter': batsman, 'Dismissal': dismissal, 'Runs': runs_b, 'Balls': balls_b, '4s': fours_b, '6s': sixes_b, 'SR': round(sr_b, 1)
        })
    st.dataframe(pd.DataFrame(bat_stats), use_container_width=True, hide_index=True)
    
    # Bowling
    bowl_stats = []
    for bowler in df_ings1['bowler'].unique():
        df_bo = df_ings1[df_ings1['bowler'] == bowler]
        runs_c = df_bo['bowler_runs'].sum()
        balls_bo = df_bo['is_legal_ball'].sum()
        wkts_bo = df_bo['is_bowler_wicket'].sum()
        
        overs_bo = f"{balls_bo // 6}.{balls_bo % 6}"
        econ_bo = (runs_c / (balls_bo / 6.0)) if balls_bo > 0 else 0.0
        
        bowl_stats.append({
            'Bowler': bowler, 'Overs': overs_bo, 'Runs': runs_c, 'Wickets': wkts_bo, 'Economy': round(econ_bo, 2)
        })
    st.dataframe(pd.DataFrame(bowl_stats), use_container_width=True, hide_index=True)

with tab_ings2:
    df_ings2 = df_match_deliv[df_match_deliv['innings'] == 2].copy()
    
    # Batting
    bat_stats_2 = []
    for batsman in df_ings2['striker'].unique():
        df_b = df_ings2[df_ings2['striker'] == batsman]
        runs_b = df_b['runs_of_bat'].sum()
        balls_b = df_b['is_legal_ball'].sum()
        fours_b = df_b['is_four'].sum()
        sixes_b = df_b['is_six'].sum()
        sr_b = (runs_b / balls_b * 100) if balls_b > 0 else 0.0
        
        df_out = df_ings2[df_ings2['player_dismissed'] == batsman]
        dismissal = df_out.iloc[0]['wicket_type'] if not df_out.empty else "not out"
        
        bat_stats_2.append({
            'Batter': batsman, 'Dismissal': dismissal, 'Runs': runs_b, 'Balls': balls_b, '4s': fours_b, '6s': sixes_b, 'SR': round(sr_b, 1)
        })
    st.dataframe(pd.DataFrame(bat_stats_2), use_container_width=True, hide_index=True)
    
    # Bowling
    bowl_stats_2 = []
    for bowler in df_ings2['bowler'].unique():
        df_bo = df_ings2[df_ings2['bowler'] == bowler]
        runs_c = df_bo['bowler_runs'].sum()
        balls_bo = df_bo['is_legal_ball'].sum()
        wkts_bo = df_bo['is_bowler_wicket'].sum()
        
        overs_bo = f"{balls_bo // 6}.{balls_bo % 6}"
        econ_bo = (runs_c / (balls_bo / 6.0)) if balls_bo > 0 else 0.0
        
        bowl_stats_2.append({
            'Bowler': bowler, 'Overs': overs_bo, 'Runs': runs_c, 'Wickets': wkts_bo, 'Economy': round(econ_bo, 2)
        })
    st.dataframe(pd.DataFrame(bowl_stats_2), use_container_width=True, hide_index=True)

# ----------------- PLOTS TABS -----------------
st.markdown('<div class="section-header">In-Match Graph Overlays</div>', unsafe_allow_html=True)

tab_g, tab_prob, tab_net, tab_sankey = st.tabs(["📊 Worm, Manhattan & Momentum", "🔮 Chase Win Probability", "🤝 Partnership Network", "🔗 Wickets Sankey Flow"])

with tab_g:
    st.plotly_chart(plot_run_worm(df_match_deliv, team1, team2), use_container_width=True)
    st.plotly_chart(plot_manhattan_chart(df_match_deliv, team1, team2), use_container_width=True)
    st.plotly_chart(plot_momentum_timeline(df_match_deliv, team1, team2), use_container_width=True)

with tab_prob:
    df_c = df_match_deliv[df_match_deliv['innings'] == 2].copy()
    if not df_c.empty:
        df_c = df_c.sort_values(by='over').reset_index(drop=True)
        
        target = first_score + 1
        cum_runs = 0
        cum_wkts = 0
        balls_bowled = 0
        
        prob_history = []
        overs_timeline = []
        
        for idx, row in df_c.iterrows():
            cum_runs += row['total_runs']
            if row['is_wicket']:
                cum_wkts += 1
            if row['is_legal_ball']:
                balls_bowled += 1
                
            chase_prob, _ = estimate_win_probability(2, cum_runs, cum_wkts, target, balls_bowled)
            prob_history.append(chase_prob)
            overs_timeline.append(row['over'])
            
        fig_prob = px.area(
            pd.DataFrame({'Over': overs_timeline, 'Win Probability %': prob_history}),
            x='Over', y='Win Probability %', title=f"Chase Win Probability Timeline (Chasing: {team2})",
            color_discrete_sequence=[t2_color]
        )
        fig_prob.update_layout(yaxis=dict(range=[0, 100]), paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
        st.plotly_chart(fig_prob, use_container_width=True)
    else:
        st.info("Win probability timeline not available.")

with tab_net:
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.plotly_chart(plot_partnership_network(df_match_deliv, team1), use_container_width=True)
    with col_n2:
        st.plotly_chart(plot_partnership_network(df_match_deliv, team2), use_container_width=True)

with tab_sankey:
    st.plotly_chart(plot_sankey_wickets(df_match_deliv, "Match Wickets Flow"), use_container_width=True)
