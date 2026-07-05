import streamlit as st
import pandas as pd
import numpy as np
from utils.helper import init_page, render_header_banner, render_kpi_card, get_team_styled_header
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from utils.metrics import get_team_dna_metrics
from utils.visualizations import plot_radar_chart, plot_opponent_heatmap
from config import TEAM_FULL_NAMES, TEAM_COLORS, SEASONS

init_page("Team Analysis")

# Load and preprocess datasets
df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("Data files could not be loaded.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']
df_team_sum = data['team_summary']
df_bat_sum = data['batting_summary']
df_bowl_sum = data['bowling_summary']
df_field_sum = data['fielding_summary']
df_venue_sum = data['venue_summary']

# ----------------- TEAM SELECTION -----------------
teams_list = sorted(list(TEAM_FULL_NAMES.keys()))
selected_team_code = st.sidebar.selectbox("Select Team", teams_list, format_func=lambda x: f"{x} - {TEAM_FULL_NAMES[x]}")
selected_season = st.sidebar.selectbox("Select Season", ["All Seasons"] + SEASONS)

team_name = TEAM_FULL_NAMES[selected_team_code]
primary_color, secondary_color = TEAM_COLORS.get(selected_team_code, ('#38bdf8', '#a855f7'))

# Banner
render_header_banner(
    f"{team_name} ({selected_team_code})",
    f"Analysis of performance, DNA ratings, and opposition breakdown for {selected_season}."
)

# Filter matches for the selected team
if selected_season == "All Seasons":
    df_team_matches = df_matches[
        (df_matches['team1'] == selected_team_code) | (df_matches['team2'] == selected_team_code)
    ].copy()
    
    # Calculate standing as average standing across seasons
    standing_avg = df_team_sum[df_team_sum['team'] == selected_team_code]['position'].mean()
    standing_str = f"{standing_avg:.1f} (Avg)"
    
    # Total wins / losses
    wins = df_team_matches[df_team_matches['match_winner'] == selected_team_code].shape[0]
    losses = df_team_matches.shape[0] - wins
    played = df_team_matches.shape[0]
    points_str = "-"
    nrr_str = "-"
else:
    df_team_matches = df_matches[
        ((df_matches['team1'] == selected_team_code) | (df_matches['team2'] == selected_team_code)) &
        (df_matches['season'] == selected_season)
    ].copy()
    
    team_points_row = df_team_sum[
        (df_team_sum['team'] == selected_team_code) & 
        (df_team_sum['season'] == selected_season)
    ]
    
    if not team_points_row.empty:
        standing_str = str(int(team_points_row.iloc[0]['position']))
        points_str = str(int(team_points_row.iloc[0]['points']))
        nrr_str = f"{team_points_row.iloc[0]['nrr']:+.3f}"
        wins = int(team_points_row.iloc[0]['wins'])
        losses = int(team_points_row.iloc[0]['defeats'])
        played = int(team_points_row.iloc[0]['played'])
    else:
        standing_str = "-"
        points_str = "0"
        nrr_str = "0.00"
        wins = losses = played = 0

# Home vs Away wins
# Heuristic for home advantage: match venues in venue summary
# Check home team in venue stats
home_played = 0
home_wins = 0
away_played = 0
away_wins = 0

# Define a simple home mapping: MI at Mumbai (Wankhede), KKR at Kolkata, RCB at Bengaluru, etc.
home_city_keywords = {
    'MI': 'mumbai', 'RCB': 'bengaluru', 'KKR': 'kolkata', 'CSK': 'chennai', 
    'DC': 'delhi', 'PBKS': 'punjab', 'LSG': 'lucknow', 'SRH': 'hyderabad', 
    'RR': 'jaipur', 'GT': 'ahmedabad'
}
home_city = home_city_keywords.get(selected_team_code, "non_existent_city")

for idx, row in df_team_matches.iterrows():
    venue = row['venue'].lower()
    is_home = home_city in venue
    is_win = (row['match_winner'] == selected_team_code)
    
    if is_home:
        home_played += 1
        if is_win:
            home_wins += 1
    else:
        away_played += 1
        if is_win:
            away_wins += 1
            
home_win_pct = (home_wins / home_played * 100) if home_played > 0 else 0.0
away_win_pct = (away_wins / away_played * 100) if away_played > 0 else 0.0

# Toss stats
toss_wins = df_team_matches[df_team_matches['toss_winner'] == selected_team_code].shape[0]
toss_win_pct = (toss_wins / played * 100) if played > 0 else 0.0
toss_match_wins = df_team_matches[
    (df_team_matches['toss_winner'] == selected_team_code) & 
    (df_team_matches['match_winner'] == selected_team_code)
].shape[0]
toss_conversion_pct = (toss_match_wins / toss_wins * 100) if toss_wins > 0 else 0.0

# Compute team custom DNA metrics (Cached)
team_season_val = None if selected_season == "All Seasons" else selected_season
team_metrics = get_team_dna_metrics(df_deliv, selected_team_code, team_season_val)

# ----------------- OVERVIEW KPIs -----------------
st.markdown(get_team_styled_header(selected_team_code, "Performance Summary"), unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    render_kpi_card(f"{standing_str}", "Standing Position", "🏆")
with col2:
    render_kpi_card(f"{played}", "Matches Played", "🏏")
with col3:
    render_kpi_card(f"{wins} - {losses}", "W - L Record", "📊")
with col4:
    render_kpi_card(f"{points_str}", "Points", "⭐")
with col5:
    render_kpi_card(f"{nrr_str}", "Net Run Rate", "📈")

col_t1, col_t2, col_t3, col_t4 = st.columns(4)
with col_t1:
    render_kpi_card(f"{home_win_pct:.1f}%", "Home Win %", "🏠")
with col_t2:
    render_kpi_card(f"{away_win_pct:.1f}%", "Away Win %", "✈️")
with col_t3:
    render_kpi_card(f"{toss_win_pct:.1f}%", "Toss Win %", "🪙")
with col_t4:
    render_kpi_card(f"{toss_conversion_pct:.1f}%", "Toss Conversion %", "🔄")

# ----------------- BATTING, BOWLING, ROSTER TABS -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏏 Batting DNA", "🎯 Bowling Defense", "🛡️ Roster Depth", "🏟️ Venue Splits", "⚔️ Opposition Analysis"])

with tab1:
    st.markdown("##### 🏏 Batting Analytics")
    col_bat1, col_bat2 = st.columns(2)
    
    with col_bat1:
        # Display key batting phase scores
        bat_ph_df = pd.DataFrame({
            'Phase': ['Powerplay (Overs 1-6)', 'Middle (Overs 7-15)', 'Death (Overs 16-20)'],
            'Run Rate': [team_metrics[f'bat_rr_{p}'] for p in ['Powerplay', 'Middle', 'Death']]
        })
        st.dataframe(bat_ph_df, use_container_width=True, hide_index=True)
        
        # Display custom metrics
        st.markdown(f"""
            <div style="background: rgba(30,41,59,0.4); padding: 18px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-top: 15px;">
                <h6 style="color: {primary_color}; margin-top:0;">Advanced Batting Indicators</h6>
                <p style="margin: 4px 0;">Win percentage when chasing: <b>{team_metrics['chasing_pct']:.1f}%</b></p>
                <p style="margin: 4px 0;">Win percentage when defending: <b>{team_metrics['defending_pct']:.1f}%</b></p>
            </div>
        """, unsafe_allow_html=True)
        
    with col_bat2:
        # Top Batters for this team
        if selected_season == "All Seasons":
            df_t_bat = df_bat_sum[df_bat_sum['team'] == selected_team_code].groupby('batsman').agg({
                'runs': 'sum',
                'balls_faced': 'sum',
                'not_outs': 'sum',
                'high_score': 'max',
                'innings': 'sum'
            }).reset_index()
            if not df_t_bat.empty:
                df_t_bat['dismissals'] = df_t_bat['innings'] - df_t_bat['not_outs']
                df_t_bat['average'] = np.where(df_t_bat['dismissals'] > 0, df_t_bat['runs'] / df_t_bat['dismissals'], df_t_bat['runs'])
                df_t_bat['strike_rate'] = np.where(df_t_bat['balls_faced'] > 0, df_t_bat['runs'] / df_t_bat['balls_faced'] * 100, 0.0)
        else:
            df_t_bat = df_bat_sum[
                (df_bat_sum['team'] == selected_team_code) & 
                (df_bat_sum['season'] == selected_season)
            ]
            
        if not df_t_bat.empty:
            st.markdown("###### Leading Batters")
            st.dataframe(
                df_t_bat[['batsman', 'runs', 'average', 'strike_rate', 'high_score']].sort_values(by='runs', ascending=False).head(5),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No batter records found for this team.")

with tab2:
    st.markdown("##### 🎯 Bowling Analytics")
    col_bowl1, col_bowl2 = st.columns(2)
    
    with col_bowl1:
        # Bowling phase table
        bowl_ph_df = pd.DataFrame({
            'Phase': ['Powerplay (Overs 1-6)', 'Middle (Overs 7-15)', 'Death (Overs 16-20)'],
            'Economy Rate': [team_metrics[f'bowl_econ_{p}'] for p in ['Powerplay', 'Middle', 'Death']]
        })
        st.dataframe(bowl_ph_df, use_container_width=True, hide_index=True)
        
    with col_bowl2:
        # Top Bowlers for this team
        if selected_season == "All Seasons":
            df_t_bowl = df_bowl_sum[df_bowl_sum['team'] == selected_team_code].groupby('bowler').agg({
                'wickets': 'sum',
                'runs': 'sum',
                'balls': 'sum'
            }).reset_index()
            if not df_t_bowl.empty:
                df_t_bowl['overs'] = df_t_bowl['balls'] / 6.0
                df_t_bowl['economy'] = np.where(df_t_bowl['overs'] > 0, df_t_bowl['runs'] / df_t_bowl['overs'], 0.0)
                df_t_bowl['avg'] = np.where(df_t_bowl['wickets'] > 0, df_t_bowl['runs'] / df_t_bowl['wickets'], df_t_bowl['runs'])
        else:
            df_t_bowl = df_bowl_sum[
                (df_bowl_sum['team'] == selected_team_code) & 
                (df_bowl_sum['season'] == selected_season)
            ]
            
        if not df_t_bowl.empty:
            st.markdown("###### Leading Bowlers")
            st.dataframe(
                df_t_bowl[['bowler', 'wickets', 'economy', 'avg', 'overs']].sort_values(by='wickets', ascending=False).head(5),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No bowler records found for this team.")

with tab3:
    st.markdown("##### 🛡️ Roster Depth Chart (Dynamic)")
    # Extract squad names
    squad_batsmen = df_deliv[df_deliv['batting_team'] == selected_team_code]['striker'].unique()
    squad_bowlers = df_deliv[df_deliv['bowling_team'] == selected_team_code]['bowler'].unique()
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("###### Active Batsmen")
        st.write(", ".join(sorted(squad_batsmen)))
    with col_r2:
        st.markdown("###### Active Bowlers")
        st.write(", ".join(sorted(squad_bowlers)))

with tab4:
    st.markdown("##### 🏟️ Venue Performance Splits")
    venue_splits = []
    
    for venue, v_grp in df_team_matches.groupby('venue'):
        played_v = v_grp.shape[0]
        wins_v = v_grp[v_grp['match_winner'] == selected_team_code].shape[0]
        win_pct = (wins_v / played_v * 100)
        
        venue_splits.append({
            'Venue': venue,
            'Matches Played': played_v,
            'Wins': wins_v,
            'Win %': round(win_pct, 1)
        })
        
    df_v_splits = pd.DataFrame(venue_splits)
    if not df_v_splits.empty:
        st.dataframe(df_v_splits.sort_values(by='Win %', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No venue data found.")

with tab5:
    st.markdown("##### ⚔️ Opposition Records Heatmap")
    fig_opp = plot_opponent_heatmap(df_matches, selected_team_code)
    if fig_opp:
        st.plotly_chart(fig_opp, use_container_width=True)
    else:
        st.info("No opposition matchups available.")

# ----------------- TEAM DNA RADAR CHART -----------------
st.markdown(get_team_styled_header(selected_team_code, "Team DNA Profile Radar"), unsafe_allow_html=True)

col_radar, col_desc = st.columns([1.2, 1])

categories = ['Aggression', 'Consistency', 'Powerplay Batting', 'Middle Overs Batting', 'Death Overs Batting', 'Bowling Quality']
values = [
    team_metrics['aggression_score'],
    team_metrics['consistency_score'],
    team_metrics['powerplay_rating'],
    team_metrics['middle_overs_rating'],
    team_metrics['death_overs_rating'],
    team_metrics['bowling_rating']
]

with col_radar:
    st.plotly_chart(
        plot_radar_chart(categories, values, f"{selected_team_code} Team DNA Profile", selected_team_code, primary_color),
        use_container_width=True
    )
    
with col_desc:
    st.markdown("##### 🧬 Decoding Team DNA")
    st.markdown(f"""
    - **Aggression Score ({team_metrics['aggression_score']:.1f}/10)**: Represents the overall batting strike rate relative to the tournament.
    - **Consistency Score ({team_metrics['consistency_score']:.1f}/10)**: Reflects stability in total runs scored match-to-match.
    - **Powerplay Batting ({team_metrics['powerplay_rating']:.1f}/10)**: Based on the average runs scored in overs 0-6.
    - **Middle Overs Batting ({team_metrics['middle_overs_rating']:.1f}/10)**: Reflects middle-overs run rates.
    - **Death Overs Batting ({team_metrics['death_overs_rating']:.1f}/10)**: Measures execution rate and scoring efficiency in final 5 overs.
    - **Bowling Quality ({team_metrics['bowling_rating']:.1f}/10)**: Aggregate rating reflecting defensive economy across all phases.
    """)
