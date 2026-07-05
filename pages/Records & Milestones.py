import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data

init_page("Records & Milestones")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']
df_bat_sum = data['batting_summary']
df_bowl_sum = data['bowling_summary']

# Banner
render_header_banner(
    "Tournament Records & Milestones",
    "All-time records, highest totals, best bowling performances, and fastest batting milestones from 2022–2026."
)

tab1, tab2, tab3 = st.tabs(["🏛️ Innings & Match Records", "🏏 Batting Records", "🎯 Bowling Records"])

with tab1:
    st.markdown("##### 🏟️ Highest Innings Totals")
    high_totals = df_matches.sort_values(by='first_ings_score', ascending=False).head(10)
    st.dataframe(
        high_totals[['season', 'date', 'venue', 'team1', 'team2', 'first_ings_score', 'first_ings_wkts', 'match_winner']],
        use_container_width=True, hide_index=True
    )
    
    st.markdown("##### 🏟️ Lowest Innings Totals")
    low_totals = df_matches.sort_values(by='first_ings_score', ascending=True).head(10)
    st.dataframe(
        low_totals[['season', 'date', 'venue', 'team1', 'team2', 'first_ings_score', 'first_ings_wkts', 'match_winner']],
        use_container_width=True, hide_index=True
    )

with tab2:
    st.markdown("##### 🏏 Highest Individual Batsman Scores")
    # Group by match and batsman in deliveries
    df_bat_inns = df_deliv.groupby(['match_id', 'season', 'striker', 'batting_team'])['runs_of_bat'].sum().reset_index()
    top_scores = df_bat_inns.sort_values(by='runs_of_bat', ascending=False).head(15)
    st.dataframe(top_scores, use_container_width=True, hide_index=True)
    
    st.markdown("##### 💥 Most Sixes in a Career (2022-2026)")
    # Sum sixes across all seasons from batting summary
    career_sixes = df_bat_sum.groupby('batsman')['sixes'].sum().reset_index()
    st.dataframe(career_sixes.sort_values(by='sixes', ascending=False).head(15), use_container_width=True, hide_index=True)

with tab3:
    st.markdown("##### 🎯 Best Bowling Figures in a Match")
    # Group by match and bowler in bowler wickets and runs
    # Runs conceded by bowler = runs off bat + wide + noballs
    df_deliv['bowler_runs'] = df_deliv['runs_of_bat'] + df_deliv['wide'] + df_deliv['noballs']
    
    bowl_inns = df_deliv.groupby(['match_id', 'season', 'bowler', 'bowling_team']).agg({
        'is_bowler_wicket': 'sum',
        'bowler_runs': 'sum',
        'is_legal_ball': 'sum'
    }).reset_index()
    
    bowl_inns['overs'] = bowl_inns['is_legal_ball'] // 6 + (bowl_inns['is_legal_ball'] % 6) / 10.0
    top_bowling = bowl_inns.sort_values(by=['is_bowler_wicket', 'bowler_runs'], ascending=[False, True]).head(15)
    st.dataframe(
        top_bowling[['season', 'bowler', 'bowling_team', 'is_bowler_wicket', 'bowler_runs', 'overs']],
        use_container_width=True, hide_index=True
    )
