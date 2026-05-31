from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from .models import TeamRecord


def get_teams(df: pd.DataFrame) -> List[str]:
    """Extracts a sorted list of unique teams from the games dataframe."""
    teams_set = set(df["Away Team"].dropna()) | set(df["Home Team"].dropna())
    return sorted(list(teams_set))


class ColleySystem:
    def __init__(self, teams: List[str]):
        self.teams = teams
        self.n_teams = len(teams)
        self.team_to_idx = {team: i for i, team in enumerate(teams)}
        
        self.C = np.zeros((self.n_teams, self.n_teams))
        self.b = np.ones(self.n_teams)
        for i in range(self.n_teams):
            self.C[i, i] = 2
            
        self.stats = {team: {"W": 0, "L": 0, "T": 0, "GF": 0, "GA": 0} for team in teams}
        
    def add_game(self, away: str, home: str, away_score: int, home_score: int) -> None:
        i = self.team_to_idx[away]
        j = self.team_to_idx[home]
        
        # Update C
        self.C[i, i] += 1
        self.C[j, j] += 1
        self.C[i, j] -= 1
        self.C[j, i] -= 1
        
        # Update stats
        self.stats[away]["GF"] += away_score
        self.stats[away]["GA"] += home_score
        self.stats[home]["GF"] += home_score
        self.stats[home]["GA"] += away_score
        
        # Update b and W/L/T
        if away_score > home_score:
            self.b[i] += 0.5
            self.b[j] -= 0.5
            self.stats[away]["W"] += 1
            self.stats[home]["L"] += 1
        elif home_score > away_score:
            self.b[j] += 0.5
            self.b[i] -= 0.5
            self.stats[home]["W"] += 1
            self.stats[away]["L"] += 1
        else:
            self.stats[away]["T"] += 1
            self.stats[home]["T"] += 1
            
    def solve(self) -> List[TeamRecord]:
        r = np.linalg.solve(self.C, self.b)
        
        records = []
        for i, team in enumerate(self.teams):
            st = self.stats[team]
            t_games = st["W"] + st["L"] + st["T"]
            
            sos = 0.0
            if t_games > 0:
                sum_opp_ratings = self.C[i, i] * r[i] - self.b[i]
                sos = sum_opp_ratings / t_games
                
            record = TeamRecord(
                team=team,
                rating=float(r[i]),
                sos=float(sos),
                w=st["W"],
                l=st["L"],
                t=st["T"],
                gf=st["GF"],
                ga=st["GA"]
            )
            records.append(record)
            
        records.sort(key=lambda x: x.rating, reverse=True)
        return records


def solve_colley_matrix(df: pd.DataFrame) -> Tuple[List[TeamRecord], np.ndarray, List[str]]:
    """
    Solves the Colley matrix and returns the sorted rankings.
    """
    teams = get_teams(df)
    system = ColleySystem(teams)
    
    valid_games = df.dropna(subset=["Away Score", "Home Score"])
    for away, home, away_score, home_score in zip(
        valid_games["Away Team"], valid_games["Home Team"], 
        valid_games["Away Score"], valid_games["Home Score"]
    ):
        system.add_game(away, home, int(away_score), int(home_score))
        
    return system.solve(), system.C, teams


def compute_weekly_ratings(df: pd.DataFrame) -> Tuple[Dict[str, List[TeamRecord]], List[str]]:
    """
    Computes the Colley ratings and SOS iteratively over each week.
    """
    valid_games = df.dropna(subset=["Away Score", "Home Score", "Date"]).copy()
    valid_games = valid_games.sort_values("Date")
    
    # Determine iso calendar weeks for valid games
    valid_games["ISO_Year"] = valid_games["Date"].dt.isocalendar().year
    valid_games["ISO_Week"] = valid_games["Date"].dt.isocalendar().week
    valid_games["Week_Key"] = valid_games.apply(lambda row: f"{row['ISO_Year']}-W{row['ISO_Week']:02d}", axis=1)
    
    teams = get_teams(df)
    system = ColleySystem(teams)
    
    weekly_records: Dict[str, List[TeamRecord]] = {}
    sorted_weeks = sorted(valid_games["Week_Key"].unique())
    prev_ranks = {}
    
    for week in sorted_weeks:
        week_games = valid_games[valid_games["Week_Key"] == week]
        
        for away, home, away_score, home_score in zip(
            week_games["Away Team"], week_games["Home Team"], 
            week_games["Away Score"], week_games["Home Score"]
        ):
            system.add_game(away, home, int(away_score), int(home_score))

        # Solve for this week
        records = system.solve()
        
        # Calculate rank changes
        for idx, rec in enumerate(records):
            current_rank = idx + 1
            rec.rank_change = prev_ranks.get(rec.team, current_rank) - current_rank
            
        weekly_records[week] = records
        prev_ranks = {rec.team: idx + 1 for idx, rec in enumerate(records)}

    return weekly_records, teams

