import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from config import SEASONS
import plotly.express as px

init_page("Season Overview")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries data found.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']
df_team_sum = data['team_summary']
df_bat_sum = data['batting_summary']
df_bowl_sum = data['bowling_summary']

# Banner
render_header_banner(
    "Season Overview & History",
    "Analysis of tournament trends, scoring growth, and team standings across seasons 2022–2026."
)

# ----------------- SEASON TRENDS CALCULATIONS -----------------
st.markdown('<div class="section-header">Year-over-Year Tournament Stats</div>', unsafe_allow_html=True)

trends = []
for s in SEASONS:
    s_deliv = df_deliv[df_deliv['season'] == s]
    s_matches = df_matches[df_matches['season'] == s]
    
    matches = s_matches.shape[0]
    runs = s_deliv['total_runs'].sum()
    wickets = s_deliv['is_wicket'].sum()
    sixes = s_deliv['is_six'].sum()
    fours = s_deliv['is_four'].sum()
    
    balls = s_deliv['is_legal_ball'].sum()
    rr = (runs / (balls / 6.0)) if balls > 0 else 0.0
    
    # 200+ totals
    scores_200 = s_matches[s_matches['first_ings_score'] >= 200].shape[0] + s_matches[s_matches['second_ings_score'] >= 200].shape[0]
    
    trends.append({
        'Season': s,
        'Matches': matches,
        'Total Runs': runs,
        'Total Wickets': wickets,
        'Sixes': sixes,
        'Fours': fours,
        'Run Rate': round(rr, 2),
        '200+ Scores': scores_200
    })
    
df_trends = pd.DataFrame(trends)
st.dataframe(df_trends, use_container_width=True, hide_index=True)

# Plot Year-over-Year Trends
col1, col2 = st.columns(2)

with col1:
    fig_runs = px.line(
        df_trends, x='Season', y='Total Runs', markers=True,
        title="Total Runs Scored YoY",
        color_discrete_sequence=['#38bdf8']
    )
    fig_runs.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
    st.plotly_chart(fig_runs, use_container_width=True)

with col2:
    fig_rr = px.line(
        df_trends, x='Season', y='Run Rate', markers=True,
        title="Average Run Rate YoY",
        color_discrete_sequence=['#ec4899']
    )
    fig_rr.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
    st.plotly_chart(fig_rr, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    fig_six = px.bar(
        df_trends, x='Season', y='Sixes',
        title="Total Sixes Hit YoY",
        color_discrete_sequence=['#a855f7']
    )
    fig_six.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
    st.plotly_chart(fig_six, use_container_width=True)
with col4:
    fig_200 = px.bar(
        df_trends, x='Season', y='200+ Scores',
        title="Number of 200+ Totals YoY",
        color_discrete_sequence=['#f59e0b']
    )
    fig_200.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
    st.plotly_chart(fig_200, use_container_width=True)

# ----------------- CHAMPIONS & STANDINGS BY SEASON -----------------
st.markdown('<div class="section-header">Yearly Standings & League Winners</div>', unsafe_allow_html=True)

# Champions are position 1 in points table
champions_list = []
for s in SEASONS:
    s_pt = df_team_sum[df_team_sum['season'] == s].sort_values(by='position')
    if not s_pt.empty:
        champ = s_pt.iloc[0]['team_name']
        points = int(s_pt.iloc[0]['points'])
        nrr = s_pt.iloc[0]['nrr']
        
        # Orange Cap
        s_bat = df_bat_sum[df_bat_sum['season'] == s].sort_values(by='runs', ascending=False)
        orange = s_bat.iloc[0]['batsman'] if not s_bat.empty else "N/A"
        runs = int(s_bat.iloc[0]['runs']) if not s_bat.empty else 0
        
        # Purple Cap
        s_bowl = df_bowl_sum[df_bowl_sum['season'] == s].sort_values(by='wickets', ascending=False)
        purple = s_bowl.iloc[0]['bowler'] if not s_bowl.empty else "N/A"
        wkts = int(s_bowl.iloc[0]['wickets']) if not s_bowl.empty else 0
        
        champions_list.append({
            'Season': s,
            'Table Topper (League Winner)': champ,
            'Points': points,
            'NRR': f"{nrr:+.3f}",
            'Orange Cap (Runs)': f"{orange} ({runs})",
            'Purple Cap (Wkts)': f"{purple} ({wkts})"
        })

df_champs = pd.DataFrame(champions_list)
st.dataframe(df_champs, use_container_width=True, hide_index=True)

# Select a season to view details
st.markdown("##### 🔍 View Detailed Standings by Season")
details_season = st.selectbox("Select Season to View standings", SEASONS)

df_s_standings = df_team_sum[df_team_sum['season'] == details_season].sort_values(by='position')
st.dataframe(
    df_s_standings[['position', 'team_name', 'played', 'wins', 'defeats', 'points', 'nrr']].style.format({'nrr': '{:+.3f}'}),
    use_container_width=True, hide_index=True
)
