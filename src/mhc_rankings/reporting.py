from pathlib import Path
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader

from .plotting import get_matplotlib_base64, get_plotly_html

# Assuming this file is at src/mhc_rankings/reporting.py
# and the template is at src/mhc_rankings/templates/report.html
TEMPLATE_DIR = Path(__file__).parent / "templates"


def prepare_rankings_data(rankings: List[Tuple[str, float, Dict[str, Any], float]], weekly_ratings: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    """
    Transforms the raw rankings list into a list of dictionaries for easier templating.
    """
    sorted_weeks = sorted(weekly_ratings.keys())
    if len(sorted_weeks) >= 2:
        prev_week = sorted_weeks[-2]
        prev_ratings = weekly_ratings[prev_week]
        prev_ranked_teams = sorted(prev_ratings.keys(), key=lambda t: prev_ratings[t], reverse=True)
        prev_ranks = {team: idx + 1 for idx, team in enumerate(prev_ranked_teams)}
    else:
        prev_ranks = {team: idx + 1 for idx, (team, *_) in enumerate(rankings)}

    current_ranks = {team: idx + 1 for idx, (team, *_) in enumerate(rankings)}

    formatted_rankings = []
    for team, rating, stats, sos in rankings:
        w = stats["W"]
        l = stats["L"]
        t = stats["T"]
        gf = stats["GF"]
        ga = stats["GA"]
        
        total_games = w + l + t
        win_pct = (w + 0.5 * t) / total_games if total_games > 0 else 0.0
        gd = gf - ga
        
        rank_change = prev_ranks.get(team, current_ranks[team]) - current_ranks[team]
        
        formatted_rankings.append({
            "team": team,
            "rating": rating,
            "sos": sos,
            "win_pct": win_pct,
            "w": w,
            "l": l,
            "t": t,
            "gf": gf,
            "ga": ga,
            "gd": gd,
            "rank_change": rank_change
        })
    return formatted_rankings


def prepare_all_weeks_rankings_data(
    weekly_ratings: Dict[str, Dict[str, float]],
    weekly_sos: Dict[str, Dict[str, float]],
    weekly_stats: Dict[str, Dict[str, Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    
    sorted_weeks = sorted(weekly_ratings.keys())
    all_weeks_data = {}
    
    for i, week in enumerate(sorted_weeks):
        ratings = weekly_ratings[week]
        sos_dict = weekly_sos.get(week, {})
        stats_dict = weekly_stats.get(week, {})
        
        # Sort teams by rating for this week
        sorted_teams_this_week = sorted(ratings.keys(), key=lambda t: ratings[t], reverse=True)
        current_ranks = {team: idx + 1 for idx, team in enumerate(sorted_teams_this_week)}
        
        # Get previous week's ranks
        if i > 0:
            prev_week = sorted_weeks[i-1]
            prev_ratings = weekly_ratings[prev_week]
            prev_sorted = sorted(prev_ratings.keys(), key=lambda t: prev_ratings[t], reverse=True)
            prev_ranks = {team: idx + 1 for idx, team in enumerate(prev_sorted)}
        else:
            prev_ranks = current_ranks
            
        formatted_rankings = []
        for team in sorted_teams_this_week:
            rating = ratings[team]
            sos = sos_dict.get(team, 0.0)
            stats = stats_dict.get(team, {"W": 0, "L": 0, "T": 0, "GF": 0, "GA": 0})
            
            w, l, t = stats["W"], stats["L"], stats["T"]
            gf, ga = stats["GF"], stats["GA"]
            
            total_games = w + l + t
            win_pct = (w + 0.5 * t) / total_games if total_games > 0 else 0.0
            gd = gf - ga
            
            rank_change = prev_ranks.get(team, current_ranks[team]) - current_ranks[team]
            
            formatted_rankings.append({
                "team": team,
                "rating": rating,
                "sos": sos,
                "win_pct": win_pct,
                "w": w,
                "l": l,
                "t": t,
                "gf": gf,
                "ga": ga,
                "gd": gd,
                "rank_change": rank_change
            })
            
        all_weeks_data[week] = formatted_rankings
        
    return all_weeks_data


def generate_html_report(
    date_str: str,
    rankings: List[Tuple[str, float, Dict[str, Any], float]],
    matrix: Any,
    teams: List[str],
    weekly_ratings: Dict[str, Dict[str, float]],
    plot_engine: str,
    output_path: str | Path,
    weekly_sos: Dict[str, Dict[str, float]] | None = None,
    weekly_stats: Dict[str, Dict[str, Dict[str, Any]]] | None = None
) -> None:
    """
    Generates the final HTML report using Jinja2 and writes it to the output path.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    
    formatted_rankings = prepare_rankings_data(rankings, weekly_ratings)
    all_weeks_data = prepare_all_weeks_rankings_data(weekly_ratings, weekly_sos or {}, weekly_stats or {})
    sorted_weeks = sorted(all_weeks_data.keys())
    
    if plot_engine == "matplotlib":
        plot_data = get_matplotlib_base64(weekly_ratings, teams, "MHC Colley Ratings Progress", "Colley Rating")
        sos_plot_data = get_matplotlib_base64(weekly_sos, teams, "Strength of Schedule Progress", "SOS") if weekly_sos else None
    elif plot_engine == "plotly":
        plot_data = get_plotly_html(weekly_ratings, teams, "MHC Colley Ratings Progress", "Colley Rating")
        sos_plot_data = get_plotly_html(weekly_sos, teams, "Strength of Schedule Progress", "SOS") if weekly_sos else None
    else:
        raise ValueError(f"Unknown plot engine: {plot_engine}")
        
    html_content = template.render(
        date=date_str,
        rankings=formatted_rankings,
        matrix=matrix,
        teams=teams,
        plot_engine=plot_engine,
        plot_data=plot_data,
        sos_plot_data=sos_plot_data,
        all_weeks_data=all_weeks_data,
        sorted_weeks=sorted_weeks
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
