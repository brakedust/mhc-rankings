import csv
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np


def create_colley_matrix(tsv_file_path):
    """
    Reads a TSV file of game results and returns the Colley matrix (C),
    the right-hand side vector (b), and the list of teams.
    
    The Colley Matrix method solves the linear system C * r = b for the rating vector r.
    """
    games = []
    teams_set = set()

    with open(tsv_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            away_team = row["Away Team"]
            home_team = row["Home Team"]
            score = row["Score"]

            teams_set.add(away_team)
            teams_set.add(home_team)

            # Assuming score format is 'AwayScore-HomeScore'
            parts = score.split("-")
            if len(parts) == 2:
                away_score = int(parts[0])
                home_score = int(parts[1])
                games.append((away_team, home_team, away_score, home_score))

    teams = sorted(list(teams_set))
    n_teams = len(teams)
    team_to_idx = {team: i for i, team in enumerate(teams)}

    # Initialize Colley matrix C and vector b
    C = np.zeros((n_teams, n_teams))
    b = np.ones(n_teams) # b_i = 1 + (w_i - l_i) / 2

    for i in range(n_teams):
        C[i, i] = 2

    stats = {team: {"W": 0, "L": 0, "T": 0, "GF": 0, "GA": 0} for team in teams}

    for away, home, away_score, home_score in games:
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
            # For a tie, win-loss diff doesn't change, so b remains unchanged
            stats[away]["T"] += 1
            stats[home]["T"] += 1

    return C, b, teams, stats

def solve_colley_matrix(tsv_file_path):
    """
    Solves the Colley matrix for the given TSV file and returns the sorted rankings.
    """
    C, b, teams, stats = create_colley_matrix(tsv_file_path)
    r = np.linalg.solve(C, b)

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

    rankings = [(teams[i], r[i], stats[teams[i]], sos[i]) for i in range(len(teams))]
    rankings.sort(key=lambda x: x[1], reverse=True)

    return rankings, C, teams

def save_results_to_tsv(rankings, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Rank", "Team", "Rating", "SOS", "Raw Win%", "W", "L", "T", "GF", "GA", "GD"])
        for idx, (team, rating, stats, sos) in enumerate(rankings, 1):
            w, l, t = stats["W"], stats["L"], stats["T"]
            gf, ga = stats["GF"], stats["GA"]
            total_games = w + l + t
            win_pct = (w + 0.5 * t) / total_games if total_games > 0 else 0.0
            gd = gf - ga
            writer.writerow([idx, team, f"{rating:.4f}", f"{sos:.4f}", f"{win_pct:.3f}", w, l, t, gf, ga, gd])

def save_colley_matrix_to_tsv(C, teams, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Team"] + teams)
        for i, team in enumerate(teams):
            row = [team] + [str(int(val)) if val.is_integer() else str(val) for val in C[i]]
            writer.writerow(row)

def compute_weekly_ratings(tsv_file_path):
    """
    Computes the Colley ratings iteratively over each week.
    Returns a dictionary of week -> {team: rating}
    """
    games_by_week = defaultdict(list)
    teams_set = set()

    with open(tsv_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            away_team = row["Away Team"]
            home_team = row["Home Team"]
            score = row["Score"]
            date_str = row["Date"]

            teams_set.add(away_team)
            teams_set.add(home_team)

            # Assuming score format is 'AwayScore-HomeScore'
            parts = score.split("-")
            if len(parts) == 2:
                away_score = int(parts[0])
                home_score = int(parts[1])

                # Parse date to determine week
                dt = datetime.strptime(date_str, "%b %d, %Y")
                iso_year, iso_week, _ = dt.isocalendar()
                week_key = f"{iso_year}-W{iso_week:02d}"

                games_by_week[week_key].append((away_team, home_team, away_score, home_score))

    teams = sorted(list(teams_set))
    n_teams = len(teams)
    team_to_idx = {team: i for i, team in enumerate(teams)}

    # Sort weeks chronologically
    sorted_weeks = sorted(games_by_week.keys())

    # Initialize Colley matrix C and vector b
    C = np.zeros((n_teams, n_teams))
    b = np.ones(n_teams)
    for i in range(n_teams):
        C[i, i] = 2

    weekly_ratings = {}

    for week in sorted_weeks:
        games = games_by_week[week]
        for away, home, away_score, home_score in games:
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
        weekly_ratings[week] = {teams[i]: r[i] for i in range(n_teams)}

    return weekly_ratings, teams

def save_weekly_ratings_to_tsv(weekly_ratings, teams, output_path):
    sorted_weeks = sorted(weekly_ratings.keys())
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Week"] + teams)
        for week in sorted_weeks:
            row = [week] + [f"{weekly_ratings[week][team]:.4f}" for team in teams]
            writer.writerow(row)

def plot_weekly_ratings(weekly_ratings, teams, output_path):
    sorted_weeks = sorted(weekly_ratings.keys())

    plt.figure(figsize=(12, 8))

    # Define an array of distinct styles and markers to help differentiate the teams
    line_styles = ["-", "--", "-.", (5, (10, 3)), (0, (5, 10)), (0, (1, 1))]
    markers = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h", "H", "+", "x"]
    colors = plt.cm.tab20.colors  # Using a colormap with 20 distinct colors

    # Sort teams by their final week ranking
    final_week = sorted_weeks[-1]
    sorted_teams = sorted(teams, key=lambda team: weekly_ratings[final_week][team], reverse=True)

    for idx, team in enumerate(sorted_teams):
        ratings = [weekly_ratings[week][team] for week in sorted_weeks]
        style = line_styles[idx % len(line_styles)]
        marker = markers[idx % len(markers)]
        color = colors[idx % len(colors)]

        plt.plot(sorted_weeks, ratings, linestyle=style, marker=marker, color=color, label=team, linewidth=2, markersize=8)

    plt.title("2025-26 MHC Colley Ratings", fontsize=16)
    plt.xlabel("Week", fontsize=14)
    plt.ylabel("Colley Rating", fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    file_path = "data/mhc-hockey/game_results_2025-26.tsv"
    rankings, C, teams = solve_colley_matrix(file_path)

    results_file = "data/mhc-hockey/rankings_output.tsv"
    matrix_file = "data/mhc-hockey/colley_matrix_output.tsv"
    weekly_ratings_file = "data/mhc-hockey/weekly_ratings_output.tsv"
    plot_file = "data/mhc-hockey/weekly_ratings_plot.png"

    save_results_to_tsv(rankings, results_file)
    save_colley_matrix_to_tsv(C, teams, matrix_file)

    weekly_ratings, _ = compute_weekly_ratings(file_path)
    save_weekly_ratings_to_tsv(weekly_ratings, teams, weekly_ratings_file)
    plot_weekly_ratings(weekly_ratings, teams, plot_file)

    print(f"Results saved to {results_file}")
    print(f"Colley matrix saved to {matrix_file}")
    print(f"Weekly ratings saved to {weekly_ratings_file}")
    print(f"Weekly ratings plot saved to {plot_file}\n")

    print(f"{'Rank':<5} {'Team':<25} {'Rating':<8} {'SOS':<8} {'Raw Win%':<10} {'W':<3} {'L':<3} {'T':<3} {'GF':<4} {'GA':<4} {'GD':<4}")
    print("-" * 90)
    for idx, (team, rating, stats, sos) in enumerate(rankings, 1):
        w, l, t = stats["W"], stats["L"], stats["T"]
        gf, ga = stats["GF"], stats["GA"]
        gd = gf - ga
        total_games = w + l + t
        win_pct = (w + 0.5 * t) / total_games if total_games > 0 else 0.0
        print(f"{idx:<5} {team:<25} {rating:.4f}   {sos:.4f}   {win_pct:.3f}      {w:<3} {l:<3} {t:<3} {gf:<4} {ga:<4} {gd:<4}")
