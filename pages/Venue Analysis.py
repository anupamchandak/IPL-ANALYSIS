import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner, render_kpi_card
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.visualizations import plot_runs_distribution, plot_dismissal_types
from config import TEAM_COLORS, TEAM_FULL_NAMES
import plotly.express as px

init_page("Venue Analysis")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']

# ----------------- VENUE SELECTION -----------------
st.sidebar.markdown("### Venue Filter")
venues_list = sorted(list(df_matches['venue'].unique()))
selected_venue = st.sidebar.selectbox("Select Venue", venues_list)

# Filter matches
df_venue_matches = df_matches[df_matches['venue'] == selected_venue].copy()
df_venue_completed = df_venue_matches[df_venue_matches['margin_type'] != 'abandoned'].copy()

# Banner
render_header_banner(
    f"{selected_venue}",
    f"Comprehensive analysis of pitch behavior, average scores, and match results history."
)

if df_venue_completed.empty:
    st.warning("No completed matches recorded at this venue.")
    st.stop()

# ----------------- KPIs -----------------
st.markdown('<div class="section-header">Venue Averages & Ratios</div>', unsafe_allow_html=True)

matches_played = df_venue_completed.shape[0]
avg_1st = df_venue_completed['first_ings_score'].mean()
avg_2nd = df_venue_completed['second_ings_score'].mean()

bat_first_wins = df_venue_completed[df_venue_completed['match_winner'] == df_venue_completed['team1']].shape[0]
chase_wins = df_venue_completed[df_venue_completed['match_winner'] == df_venue_completed['team2']].shape[0]

bat_first_pct = (bat_first_wins / matches_played * 100) if matches_played > 0 else 0.0
chase_pct = (chase_wins / matches_played * 100) if matches_played > 0 else 0.0

highest_score = df_venue_completed['first_ings_score'].max()
highest_team = df_venue_completed.loc[df_venue_completed['first_ings_score'].idxmax()]['team1']

lowest_score = df_venue_completed['first_ings_score'].min()
lowest_team = df_venue_completed.loc[df_venue_completed['first_ings_score'].idxmin()]['team1']

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card(str(matches_played), "Matches Played", "🏟️")
with col2:
    render_kpi_card(f"{avg_1st:.1f}", "Avg 1st Innings Score", "📈")
with col3:
    render_kpi_card(f"{avg_2nd:.1f}", "Avg 2nd Innings Score", "📉")
with col4:
    render_kpi_card(f"{bat_first_pct:.1f}% / {chase_pct:.1f}%", "Defend / Chase Win %", "🔄")

col_s1, col_s2 = st.columns(2)
with col_s1:
    render_kpi_card(f"{int(highest_score)} ({highest_team})", "Highest 1st Innings Score", "🔥")
with col_s2:
    render_kpi_card(f"{int(lowest_score)} ({lowest_team})", "Lowest 1st Innings Score", "❄️")

# ----------------- PLOTS -----------------
st.markdown('<div class="section-header">Pitch & Scoring Analysis</div>', unsafe_allow_html=True)

df_venue_deliv = df_deliv[df_deliv['venue'] == selected_venue].copy()

if df_venue_deliv.empty:
    st.info("No delivery level details found.")
else:
    tab1, tab2 = st.tabs(["🏏 Runs & Boundaries", "🎯 Wickets & Spinner Split"])
    
    with tab1:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(plot_runs_distribution(df_venue_deliv, "Runs Distribution at Venue"), use_container_width=True)
        with col_g2:
            # Average runs by over
            df_venue_deliv['over_num'] = df_venue_deliv['over'].astype(int) + 1
            df_overs = df_venue_deliv.groupby('over_num')['runs_of_bat'].mean().reset_index(name='avg_runs')
            df_overs['avg_runs'] = df_overs['avg_runs'] * 6
            fig_overs = px.line(
                df_overs, x='over_num', y='avg_runs', markers=True,
                title="Runs Scored per Over at this Venue",
                labels={'over_num': 'Over', 'avg_runs': 'Average Runs per Over'},
                color_discrete_sequence=['#a855f7']
            )
            fig_overs.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
            st.plotly_chart(fig_overs, use_container_width=True)
            
    with tab2:
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            st.plotly_chart(plot_dismissal_types(df_venue_deliv, "Wicket Types at Venue"), use_container_width=True)
        with col_g4:
            # Pace vs Spin split
            known_spinners = {
                'Ravi Bishnoi', 'Krunal Pandya', 'AM Ghazanfar', 'Mitchell Santner', 'Mayank Markande',
                'Suyash Sharma', 'Anukul Roy', 'Rashid Khan', 'Rahul Chahar', 'Yuzvendra Chahal',
                'Kuldeep Yadav', 'Varun Chakaravarthy', 'Axar Patel', 'Ravindra Jadeja', 'Harpreet Brar',
                'Sunil Narine', 'R Ashwin', 'Karan Sharma', 'Cooper Connolly', 'Harsh Dubey'
            }
            df_venue_deliv['bowler_style'] = df_venue_deliv['bowler'].apply(
                lambda x: 'Spin' if x in known_spinners else 'Pace'
            )
            df_wkts = df_venue_deliv[df_venue_deliv['is_bowler_wicket'] == 1]
            if not df_wkts.empty:
                df_style = df_wkts.groupby('bowler_style').size().reset_index(name='wickets')
                fig_style = px.pie(
                    df_style, names='bowler_style', values='wickets',
                    title="Pace vs Spin Wicket Split",
                    color='bowler_style', color_discrete_map={'Pace': '#38bdf8', 'Spin': '#e11d48'}
                )
                fig_style.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
                st.plotly_chart(fig_style, use_container_width=True)
            else:
                st.info("No bowling wickets logged at this venue.")

# ----------------- MATCH LIST -----------------
st.markdown('<div class="section-header">Match History at this Stadium</div>', unsafe_allow_html=True)
st.dataframe(
    df_venue_matches[['match_id', 'season', 'date', 'team1', 'team2', 'first_ings_score', 'second_ings_score', 'match_winner']],
    use_container_width=True, hide_index=True
)
