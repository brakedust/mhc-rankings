import base64
import io
from typing import Dict, List

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


def create_matplotlib_figure(data_dict: Dict[str, Dict[str, float]], teams: List[str], title: str, ylabel: str) -> plt.Figure:
    """
    Creates a matplotlib figure for progress data over weeks.
    """
    sorted_weeks = sorted(data_dict.keys())
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    line_styles = ["-", "--", "-.", (5, (10, 3)), (0, (5, 10)), (0, (1, 1))]
    markers = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h", "H", "+", "x"]
    colors = plt.cm.tab20.colors
    
    if not sorted_weeks:
        return fig
        
    final_week = sorted_weeks[-1]
    sorted_teams = sorted(teams, key=lambda team: data_dict[final_week].get(team, 0), reverse=True)
    
    for idx, team in enumerate(sorted_teams):
        ratings = [data_dict[week].get(team, 0.0) for week in sorted_weeks]
        style = line_styles[idx % len(line_styles)]
        marker = markers[idx % len(markers)]
        color = colors[idx % len(colors)]
        
        ax.plot(sorted_weeks, ratings, linestyle=style, marker=marker, color=color, 
                label=team, linewidth=2, markersize=8)
                
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Week", fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()
    
    return fig


def get_matplotlib_base64(data_dict: Dict[str, Dict[str, float]], teams: List[str], title: str, ylabel: str) -> str:
    """
    Generates the matplotlib plot and returns it as a base64 encoded string for HTML embedding.
    """
    fig = create_matplotlib_figure(data_dict, teams, title, ylabel)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def save_matplotlib_plot(data_dict: Dict[str, Dict[str, float]], teams: List[str], output_path: str, title: str, ylabel: str) -> None:
    """
    Saves the matplotlib plot to disk as an image.
    """
    fig = create_matplotlib_figure(data_dict, teams, title, ylabel)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def get_plotly_html(data_dict: Dict[str, Dict[str, float]], teams: List[str], title: str, ylabel: str) -> str:
    """
    Generates an interactive Plotly plot and returns it as an HTML div string.
    """
    sorted_weeks = sorted(data_dict.keys())
    if not sorted_weeks:
        return "<p>No data available for plotting.</p>"
        
    final_week = sorted_weeks[-1]
    sorted_teams = sorted(teams, key=lambda team: data_dict[final_week].get(team, 0), reverse=True)
    
    fig = go.Figure()
    
    # We can use Plotly Express colors
    colors = px.colors.qualitative.Alphabet
    
    for idx, team in enumerate(sorted_teams):
        ratings = [data_dict[week].get(team, 0.0) for week in sorted_weeks]
        color = colors[idx % len(colors)]
        
        fig.add_trace(go.Scatter(
            x=sorted_weeks,
            y=ratings,
            mode='lines+markers',
            name=team,
            line=dict(width=2, color=color),
            marker=dict(size=8)
        ))
        
    fig.update_layout(
        title=title,
        xaxis_title="Week",
        yaxis_title=ylabel,
        legend_title="Teams",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        ),
        margin=dict(r=150) # Make room for legend
    )
    
    return fig.to_html(full_html=False, include_plotlyjs="cdn")
