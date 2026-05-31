from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def get_teams(df: pd.DataFrame) -> List[str]:
    """Extracts a sorted list of unique teams from the games dataframe."""
    teams_set = set(df["Away Team"].dropna()) | set(df["Home Team"].dropna())
    return sorted(list(teams_set))


def create_colley_matrix(df: pd.DataFrame, teams: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[str, Dict[str, Any]]]:
    """
    Creates the Colley matrix (C) and the right-hand side vector (b).
    
    Args:
        df: DataFrame containing game results.
        teams: Sorted list of team names.
        
    Returns:
        C: The Colley matrix.
        b: The right-hand side vector.
        stats: Dictionary containing W, L, T, GF, GA for each team.
    """
    n_teams = len(teams)
    team_to_idx = {team: i for i, team in enumerate(teams)}
    
    C = np.zeros((n_teams, n_teams))
    b = np.ones(n_teams)
    
    for i in range(n_teams):
        C[i, i] = 2
        
    stats = {team: {"W": 0, "L": 0, "T": 0, "GF": 0, "GA": 0} for team in teams}
    
    # Filter for games that have valid scores
    valid_games = df.dropna(subset=["Away Score", "Home Score"])
    
    for _, row in valid_games.iterrows():
        away = row["Away Team"]
        home = row["Home Team"]
        away_score = int(row["Away Score"])
        home_score = int(row["Home Score"])
        
        i = team_to_idx[away]
        j = team_to_idx[home]
        
        # Update C
        C[i, i] += 1
        C[j, j] += 1
        C[i, j] -= 1
        C[j, i] -= 1
        
        # Update stats
        stats[away]["GF"] += away_score
        stats[away]["GA"] += home_score
        stats[home]["GF"] += home_score
        stats[home]["GA"] += away_score
        
        # Update b and W/L/T
        if away_score > home_score:
            b[i] += 0.5
            b[j] -= 0.5
            stats[away]["W"] += 1
            stats[home]["L"] += 1
        elif home_score > away_score:
            b[j] += 0.5
            b[i] -= 0.5
            stats[home]["W"] += 1
            stats[away]["L"] += 1
        else:
            stats[away]["T"] += 1
            stats[home]["T"] += 1
            
    return C, b, stats


def solve_colley_matrix(df: pd.DataFrame) -> Tuple[List[Tuple[str, float, Dict[str, Any], float]], np.ndarray, List[str]]:
    """
    Solves the Colley matrix and returns the sorted rankings.
    """
    teams = get_teams(df)
    C, b, stats = create_colley_matrix(df, teams)
    
    # Solve C * r = b
    r = np.linalg.solve(C, b)
    
    # Compute Strength of Schedule (SOS)
    sos = np.zeros(len(teams))
    for i in range(len(teams)):
        w = stats[teams[i]]["W"]
        l = stats[teams[i]]["L"]
        t_games = w + l + stats[teams[i]]["T"]

        if t_games > 0:
            sum_opp_ratings = C[i, i] * r[i] - b[i]
            sos[i] = sum_opp_ratings / t_games
        else:
            sos[i] = 0.0

    rankings = [(teams[i], float(r[i]), stats[teams[i]], float(sos[i])) for i in range(len(teams))]
    rankings.sort(key=lambda x: x[1], reverse=True)
    
    return rankings, C, teams


def compute_weekly_ratings(df: pd.DataFrame) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], List[str]]:
    """
    Computes the Colley ratings and SOS iteratively over each week.
    """
    valid_games = df.dropna(subset=["Away Score", "Home Score", "Date"]).copy()
    
    # Determine iso calendar weeks for valid games
    valid_games["ISO_Year"] = valid_games["Date"].dt.isocalendar().year
    valid_games["ISO_Week"] = valid_games["Date"].dt.isocalendar().week
    valid_games["Week_Key"] = valid_games.apply(lambda row: f"{row['ISO_Year']}-W{row['ISO_Week']:02d}", axis=1)
    
    teams = get_teams(df)
    n_teams = len(teams)
    team_to_idx = {team: i for i, team in enumerate(teams)}
    
    C = np.zeros((n_teams, n_teams))
    b = np.ones(n_teams)
    for i in range(n_teams):
        C[i, i] = 2
        
    weekly_ratings: Dict[str, Dict[str, float]] = {}
    weekly_sos: Dict[str, Dict[str, float]] = {}
    sorted_weeks = sorted(valid_games["Week_Key"].unique())
    
    for week in sorted_weeks:
        week_games = valid_games[valid_games["Week_Key"] == week]
        
        for _, row in week_games.iterrows():
            away = row["Away Team"]
            home = row["Home Team"]
            away_score = int(row["Away Score"])
            home_score = int(row["Home Score"])
            
            i = team_to_idx[away]
            j = team_to_idx[home]

            # Update C
            C[i, i] += 1
            C[j, j] += 1
            C[i, j] -= 1
            C[j, i] -= 1

            # Update b
            if away_score > home_score:
                b[i] += 0.5
                b[j] -= 0.5
            elif home_score > away_score:
                b[j] += 0.5
                b[i] -= 0.5

        # Solve for this week
        r = np.linalg.solve(C, b)
        weekly_ratings[week] = {teams[i]: float(r[i]) for i in range(n_teams)}
        
        week_sos = {}
        for i in range(n_teams):
            t_games = C[i, i] - 2
            if t_games > 0:
                sum_opp_ratings = C[i, i] * r[i] - b[i]
                week_sos[teams[i]] = float(sum_opp_ratings / t_games)
            else:
                week_sos[teams[i]] = 0.0
        weekly_sos[week] = week_sos

    return weekly_ratings, weekly_sos, teams
