import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_and_align_deliveries
from utils.preprocessing import build_processed_data

print("--- Running Multi-Season Pipeline Verification ---")

print("1. Loading deliveries and aligning schemas...")
df_master = load_and_align_deliveries()
print(f"Master deliveries loaded successfully. Shape: {df_master.shape}")

print("\n2. Processing data and building summaries...")
data = build_processed_data(df_master)
print("Pipeline built successfully. Extracted tables:")
for key, df in data.items():
    print(f"  - {key}: Shape: {df.shape}")

# Spot checks
df_matches = data['matches']
df_team_sum = data['team_summary']

print("\n3. Verifying Standings and NRR...")
for s in sorted(df_matches['season'].unique()):
    pt = df_team_sum[df_team_sum['season'] == s].sort_values(by='position')
    print(f"Season {s} Champions (Topper): {pt.iloc[0]['team_name']} with {pt.iloc[0]['points']} pts, NRR: {pt.iloc[0]['nrr']:+.3f}")

print("\n--- Pipeline Verification Completed Successfully! ---")
