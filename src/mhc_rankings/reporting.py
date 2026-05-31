from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader

from .models import TeamRecord
from .plotting import get_matplotlib_base64, get_plotly_html

# Assuming this file is at src/mhc_rankings/reporting.py
# and the template is at src/mhc_rankings/templates/report.html
TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html_report(
    date_str: str,
    rankings: List[TeamRecord],
    matrix: Any,
    teams: List[str],
    weekly_records: Dict[str, List[TeamRecord]],
    plot_engine: str,
    output_path: str | Path,
    include_sos_plot: bool = False
) -> None:
    """
    Generates the final HTML report using Jinja2 and writes it to the output path.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    
    # Convert dataclasses to dicts for JSON serialization in the template
    formatted_rankings = [asdict(r) for r in rankings]
    
    all_weeks_data = {}
    for week, records in weekly_records.items():
        all_weeks_data[week] = [asdict(r) for r in records]
        
    sorted_weeks = sorted(all_weeks_data.keys())
    
    if plot_engine == "matplotlib":
        plot_data = get_matplotlib_base64(weekly_records, teams, "MHC Colley Ratings Progress", "Colley Rating", "rating")
        sos_plot_data = get_matplotlib_base64(weekly_records, teams, "Strength of Schedule Progress", "SOS", "sos") if include_sos_plot else None
    elif plot_engine == "plotly":
        plot_data = get_plotly_html(weekly_records, teams, "MHC Colley Ratings Progress", "Colley Rating", "rating")
        sos_plot_data = get_plotly_html(weekly_records, teams, "Strength of Schedule Progress", "SOS", "sos") if include_sos_plot else None
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
