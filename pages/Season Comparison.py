import streamlit as st
import pandas as pd
from utils.helper import init_page, render_header_banner
from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data
from config import SEASONS
import plotly.express as px
import plotly.graph_objects as go

init_page("Season Comparison")

df_master = load_and_align_deliveries()
data = build_processed_data(df_master)

if not data:
    st.error("No deliveries database available.")
    st.stop()

df_matches = data['matches']
df_deliv = data['deliveries']
df_team_sum = data['team_summary']

# ----------------- SEASON SELECTION -----------------
st.sidebar.markdown("### Select Seasons to Compare")
season_a = st.sidebar.selectbox("Season A", SEASONS, index=0)
season_b = st.sidebar.selectbox("Season B", SEASONS, index=1)

if season_a == season_b:
    st.warning("Please select two different seasons.")
    st.stop()

# Banner
render_header_banner(
    "Season Comparison",
    f"Year-over-year tournament comparison: **{season_a}** vs **{season_b}**"
)

# Calculate Stats for Season A and B
def get_season_aggregate_stats(s):
    s_deliv = df_deliv[df_deliv['season'] == s]
    s_matches = df_matches[df_matches['season'] == s]
    
    runs = s_deliv['total_runs'].sum()
    wkts = s_deliv['is_wicket'].sum()
    sixes = s_deliv['is_six'].sum()
    fours = s_deliv['is_four'].sum()
    
    balls = s_deliv['is_legal_ball'].sum()
    rr = (runs / (balls / 6.0)) if balls > 0 else 0.0
    
    avg_score = s_matches['first_ings_score'].mean()
    scores_200 = s_matches[s_matches['first_ings_score'] >= 200].shape[0] + s_matches[s_matches['second_ings_score'] >= 200].shape[0]
    
    return {
        'Matches': s_matches.shape[0],
        'Total Runs': runs,
        'Total Wickets': wkts,
        'Sixes': sixes,
        'Fours': fours,
        'Average Run Rate': round(rr, 2),
        'Avg 1st Innings Score': round(avg_score, 1),
        '200+ Scores': scores_200
    }

stats_a = get_season_aggregate_stats(season_a)
stats_b = get_season_aggregate_stats(season_b)

# Compare table
comp_data = {
    'Tournament Parameter': list(stats_a.keys()),
    f'Season {season_a}': list(stats_a.values()),
    f'Season {season_b}': list(stats_b.values())
}

st.markdown('<div class="section-header">Aggregate Tournament Comparisons</div>', unsafe_allow_html=True)
st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

# Visual comparison
col1, col2 = st.columns(2)
with col1:
    # Comparison of boundaries
    boundary_comp = pd.DataFrame({
        'Boundary': ['Fours', 'Sixes', 'Fours', 'Sixes'],
        'Count': [stats_a['Fours'], stats_a['Sixes'], stats_b['Fours'], stats_b['Sixes']],
        'Season': [str(season_a), str(season_a), str(season_b), str(season_b)]
    })
    fig_bound = px.bar(
        boundary_comp, x='Boundary', y='Count', color='Season', barmode='group',
        title="Boundaries Comparison", color_discrete_sequence=['#38bdf8', '#ec4899']
    )
    fig_bound.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
    st.plotly_chart(fig_bound, use_container_width=True)

with col2:
    # Run Rate comparison
    fig_rr = go.Figure()
    fig_rr.add_trace(go.Bar(x=[str(season_a), str(season_b)], y=[stats_a['Average Run Rate'], stats_b['Average Run Rate']],
                           marker_color=['#38bdf8', '#ec4899'], text=[stats_a['Average Run Rate'], stats_b['Average Run Rate']],
                           textposition='auto', name='Run Rate'))
    fig_rr.update_layout(title="Average Run Rate Comparison", yaxis=dict(range=[0, 12]))
    fig_rr.update_layout(paper_bgcolor='rgba(11, 15, 25, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0)', font=dict(color='#cbd5e1'))
    st.plotly_chart(fig_rr, use_container_width=True)

# ----------------- STANDINGS COMPARE -----------------
st.markdown('<div class="section-header">Standing Rank Comparisons</div>', unsafe_allow_html=True)

# Merge standings
df_pt_a = df_team_sum[df_team_sum['season'] == season_a][['team_name', 'position', 'points', 'nrr']].rename(
    columns={'position': f'pos_{season_a}', 'points': f'pts_{season_a}', 'nrr': f'nrr_{season_a}'}
)
df_pt_b = df_team_sum[df_team_sum['season'] == season_b][['team_name', 'position', 'points', 'nrr']].rename(
    columns={'position': f'pos_{season_b}', 'points': f'pts_{season_b}', 'nrr': f'nrr_{season_b}'}
)

df_pt_compare = pd.merge(df_pt_a, df_pt_b, on='team_name', how='outer').fillna("-")
st.dataframe(df_pt_compare, use_container_width=True, hide_index=True)
