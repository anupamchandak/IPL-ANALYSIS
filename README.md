# 🏏 IPL Analytics Hub (Seasons 2022–2026)

Welcome to the **IPL Analytics Hub**, a production-grade Streamlit application designed for franchise analysts, selectors, and sports data scientists.

The application aggregates **87,000+ ball-by-ball deliveries** across seasons 2022–2026 to dynamically calculate all match outcomes, team standings, player summaries, and venue behaviors on the fly. It features custom visual overlays, advanced metrics, and an **AI Coach** SWOT dashboard.

---

## 📂 Project Structure

```
IPL/
├── app.py                      # Main entrypoint (redirects to Home.py)
├── requirements.txt            # Project dependencies
├── README.md                   # Technical documentation
├── config.py                   # Styling, mappings, and global theme parameters
├── dataset/                    # Ball-by-ball deliveries datasets
│   ├── ipl_2022_deliveries.csv
│   ├── ipl_2023_deliveries.csv
│   ├── ipl_2024_deliveries.csv
│   ├── ipl_2025_deliveries.csv
│   └── ipl_2026_deliveries.csv
├── pages/                      # Multipage Streamlit frontend (13 pages)
│   ├── Home.py                 # Multi-season overview KPIs & cap leaders
│   ├── Season Overview.py      # Year-by-year summary stats, records
│   ├── Team Analysis.py        # Team DNA, phase splits, opposition
│   ├── Player Explorer.py      # Detailed batsman profiles & timeline splits
│   ├── Bowler Analysis.py      # Bowler profiles, economy phases, impact
│   ├── Venue Analysis.py       # Pitch behavior, pace/spin wicket breakdowns
│   ├── Match Analysis.py       # Scorecard, worm, momentum, win probability
│   ├── Team Comparison.py      # Head-to-head comparisons, DNA overlays
│   ├── Player Comparison.py    # Side-by-side comparison of batsman/bowler
│   ├── Season Comparison.py    # Year-over-year trends and comparison
│   ├── Records & Milestones.py # High scores, quick wickets, boundary records
│   ├── AI Coach.py             # SWOT and statistical strategy recommendations
│   └── About.py                # Formulation of metrics
├── utils/                      # Modular functional utilities
│   ├── data_loader.py          # Dynamic load & validation of deliveries files
│   ├── preprocessing.py        # Master aggregation engine & derived tables
│   ├── metrics.py              # Advanced metric calculations
│   ├── visualizations.py       # Reusable Plotly charts
│   ├── recommendation_engine.py# Heuristic stats-based coach generator
│   └── helper.py               # Custom UI, dark CSS theme and layouts
└── models/                     # Analytics models
    └── prediction.py           # Logistic win probability & score forecasting
```

---

## ⚡ Setup & Installation

1. **Verify workspace directory** contains the `dataset/` directory with all 5 deliveries CSV files.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Launch the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

---

## 📈 Advanced Metrics Included

* **Pressure Index (Chase)**: Estimates chase pressure ball-by-ball based on the ratio of required vs current run rate, scaled by wickets lost:
  $$Pressure = \\frac{Required\\ Run\\ Rate}{Current\\ Run\\ Rate} \\times (Wickets\\ Lost + 1)$$
* **Pressure Bowling Score**: Ranks bowler effectiveness weighting wickets, dot balls, and runs conceded:
  $$Pressure\\ Bowling\\ Score = Wickets \\times 25 + Dot\\ Balls \\times 1.5 - Runs$$
* **Batting Control %**: Heuristic of shots played in control (excluding wickets and dot ball penalties).
* **Fielding Impact Score**: Evaluates fielding value:
  $$Fielding\\ Impact = Catches \\times 10 + Run\\ Outs \\times 15$$

---

## 🤖 AI Coach (Franchise USP)

The **AI Coach** analyzes match deliveries and team aggregates. It compares team statistics to tournament averages to dynamically identify:
1. **Strengths**: Statistically superior phases (e.g. elite Powerplay batting or disciplined death-overs bowling).
2. **Weaknesses**: Deficiencies (e.g. high collapse risk or excessive dot ball percentages).
3. **Coaching Action Directives**: Specific tactics, such as opening with a high-SR bench player or increasing bowling allocation for economical death specialists.
