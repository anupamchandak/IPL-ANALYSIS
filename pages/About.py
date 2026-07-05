import streamlit as st
from utils.helper import init_page, render_header_banner

init_page("About & Metrics")

render_header_banner(
    "About the Analytics Hub",
    "Detailed guide to advanced metrics, NRR rules, and methodological documentation."
)

st.markdown("""
### 📊 Advanced Metrics Documentation

This platform calculates and tracks a variety of proprietary advanced metrics to evaluate team DNA and player efficiency directly from ball-by-ball deliveries.

---

#### 1. ⚡ Pressure Index (Chase)
* **What it is**: Measures the situational pressure on a chasing batsman ball-by-ball.
* **Formula**:
  $$Pressure\\ Index = \\frac{Required\\ Run\\ Rate}{Current\\ Run\\ Rate} \\times (Wickets\\ Lost + 1)$$
* **Interpretation**:
  - **< 1.5**: comfort zone.
  - **1.5 - 3.5**: Match is balanced.
  - **3.5 - 6.0**: High pressure.
  - **> 6.0**: Extreme pressure.

---

#### 2. 🎯 Pressure Bowling Score
* **What it is**: A rating of a bowler's contribution to restricting runs and capturing wickets.
* **Formula**:
  $$Pressure\\ Bowling\\ Score = (Wickets \\times 25) + (Dot\\ Balls \\times 1.5) - Runs\\ Conceded$$

---

#### 3. 💥 Boundary Dependency
* **What it is**: The percentage of runs a player or team scores purely through boundaries.
* **Formula**:
  $$Boundary\\ Dependency\\ \\% = \\frac{Boundary\\ Runs}{Total\\ Runs} \\times 100$$

---

#### 4. 📈 Batting Collapse Risk
* **What it is**: The probability of a batting lineup losing wickets in quick succession.
* **Formula**: Measured by the frequency of losing $\\ge 3$ wickets within 15 runs in an innings.

---

#### 5. 🏟️ Net Run Rate (NRR) Calculation Rules
In accordance with official IPL playing conditions:
- **Bowled Out Rule**: If a team is bowled out (i.e. loses 10 wickets) before completing their 20 overs, the overs faced is counted as **20.0** (120 balls).
- **Opposition Bowled Out Rule**: If a team bowls out the opposition before completing 20 overs, the overs bowled is counted as **20.0** (120 balls).
""")
