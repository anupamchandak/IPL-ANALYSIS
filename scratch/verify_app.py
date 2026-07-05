import os
import sys

# Add root folder to sys.path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_all_datasets
from utils.preprocessing import clean_and_preprocess_data
from utils.metrics import get_team_metrics, get_player_batting_metrics, get_player_bowling_metrics

print("--- Initializing App Verification ---")

# 1. Load data
print("Loading datasets...")
raw_data = load_all_datasets()
for name, df in raw_data.items():
    print(f"Loaded {name}.csv - Shape: {df.shape}")

# 2. Preprocess data
print("\nPreprocessing data...")
data = clean_and_preprocess_data(raw_data)
df_matches = data.get('matches')
df_deliv = data.get('deliveries')
df_merged = data.get('merged_deliveries')

print(f"Merged deliveries dataset rows: {df_merged.shape[0]}")

# 3. Test Metric Calculation
print("\nCalculating metrics for teams...")
all_teams = df_matches['team1'].unique()
for team in all_teams:
    m = get_team_metrics(df_merged, team)
    print(f"Team {team}: Aggression={m['aggression_score']:.2f}, Powerplay Rating={m['powerplay_rating']:.2f}, Bowling Econ PP={m['bowl_econ_Powerplay']:.2f}")

# 4. Scorecard Check
print("\nVerifying Score matches...")
mismatches = 0
for idx, row in df_matches.iterrows():
    if row['match_result'] != 'completed':
        continue
    m_id = int(row['match_id'])
    
    # 1st Innings runs
    df_i1 = df_merged[(df_merged['match_no'] == m_id) & (df_merged['innings'] == 1)]
    calc_runs_1 = df_i1['total_runs'].sum()
    act_runs_1 = int(row['first_ings_score'])
    
    # 2nd Innings runs
    df_i2 = df_merged[(df_merged['match_no'] == m_id) & (df_merged['innings'] == 2)]
    calc_runs_2 = df_i2['total_runs'].sum()
    act_runs_2 = int(row['second_ings_score'])
    
    diff1 = abs(calc_runs_1 - act_runs_1)
    diff2 = abs(calc_runs_2 - act_runs_2)
    
    if diff1 > 5 or diff2 > 5:
        mismatches += 1
        print(f"Mismatch Match {m_id}: 1st Ings Diff={calc_runs_1 - act_runs_1}, 2nd Ings Diff={calc_runs_2 - act_runs_2}")

print(f"Total Matches with heavy score mismatches (>5 runs): {mismatches}")
print("\n--- Verification Completed Successfully! ---")
