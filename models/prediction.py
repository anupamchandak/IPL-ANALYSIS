import numpy as np

def estimate_win_probability(innings, current_runs, wickets, target, balls_bowled, total_balls=120):
    """
    Computes the win probability for both teams ball-by-ball.
    Returns: (batting_team_prob, bowling_team_prob)
    """
    balls_left = total_balls - balls_bowled
    wickets_left = 10 - wickets
    
    # Innings 1: Win probability is harder to estimate without historic match data,
    # but we can base it on run rate vs a par score of 180.
    if innings == 1:
        if balls_bowled == 0:
            return 50.0, 50.0
            
        crr = (current_runs / (balls_bowled / 6.0))
        projected = crr * 20.0
        
        # Scale between 20% and 80% based on projected score
        # 180 runs is a standard par score (50%)
        diff = projected - 180.0
        prob = 50.0 + (diff * 0.3)
        prob = max(min(prob, 95.0), 5.0) # limit extremes in innings 1
        
        return round(prob, 1), round(100.0 - prob, 1)
        
    # Innings 2: Chase Win Probability
    # Target is set.
    runs_needed = target - current_runs
    
    # Edge cases
    if runs_needed <= 0:
        return 100.0, 0.0
    if wickets_left <= 0:
        return 0.0, 100.0
    if balls_left <= 0:
        return 0.0, 100.0
        
    crr = (current_runs / (balls_bowled / 6.0)) if balls_bowled > 0 else 6.0
    rrr = (runs_needed / (balls_left / 6.0))
    
    # Logistic odds-based calculation
    # Log-odds factors:
    # 1. RRR relative to a baseline of 8.0: higher RRR decreases probability.
    # 2. Wickets remaining: more wickets increases probability.
    # 3. Balls left: as balls left decreases, the impact of RRR increases.
    
    # Base value
    x = 1.8 - 0.45 * rrr + 0.65 * wickets_left - 0.025 * balls_left
    
    # Adjust for extreme RRR situations
    if rrr > 24.0: # more than 24 runs per over needed
        prob = 0.5
    elif rrr > 18.0 and wickets_left < 3:
        prob = 1.0
    else:
        prob = 100.0 / (1.0 + np.exp(-x))
        
    # Boundary constraints
    prob = max(min(prob, 99.5), 0.5)
    
    return round(prob, 1), round(100.0 - prob, 1)

def project_innings_score(current_runs, wickets, balls_bowled, total_balls=120):
    """
    Projects the final score of the innings.
    Uses a weighted combination of current run rate and a standard par rate,
    adjusted down for wickets lost.
    """
    balls_left = total_balls - balls_bowled
    wickets_left = 10 - wickets
    
    if balls_bowled == 0:
        return 180, 180, 180 # (Low, Mid, High)
        
    crr = current_runs / (balls_bowled / 6.0)
    
    # Par rate for remaining overs is 8.5, but scaled down if wickets are lost
    # losing wickets decreases the run rate of remaining balls
    remaining_rate = 8.5 * (wickets_left / 10.0) + (crr * 0.4)
    
    projected_runs = current_runs + (remaining_rate * (balls_left / 6.0))
    
    # Calculate confidence interval
    # standard deviation of final scores is around 25 runs
    std_dev = 25.0 * (balls_left / total_balls)
    
    projected_mid = int(round(projected_runs))
    projected_low = int(round(projected_runs - 1.96 * std_dev))
    projected_high = int(round(projected_runs + 1.96 * std_dev))
    
    return projected_low, projected_mid, projected_high
