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
        
    all_vals = [val for week_data in data_dict.values() for val in week_data.values()]
    min_y = min(all_vals) if all_vals else 0
    max_y = max(all_vals) if all_vals else 1
    y_padding = (max_y - min_y) * 0.05 if max_y > min_y else 0.1
    y_range = [min_y - y_padding, max_y + y_padding]
        
    final_week = sorted_weeks[-1]
    sorted_teams = sorted(teams, key=lambda team: data_dict[final_week].get(team, 0), reverse=True)
    
    fig = go.Figure()
    
    # Consistent markers and colors with Matplotlib implementation
    line_dash_styles = ["solid", "dash", "dashdot", "longdash", "longdashdot", "dot"]
    markers = ["circle", "square", "triangle-up", "diamond", "triangle-down", "triangle-left", "triangle-right", "pentagon", "star", "hexagon", "hexagon2", "cross", "x"]
    # Replicating plt.cm.tab20.colors in hex for Plotly
    colors = [
        '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a',
        '#d62728', '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94',
        '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d',
        '#17becf', '#9edae5'
    ]
    
    for idx, team in enumerate(sorted_teams):
        ratings = [data_dict[week].get(team, 0.0) for week in sorted_weeks]
        dash_style = line_dash_styles[idx % len(line_dash_styles)]
        marker = markers[idx % len(markers)]
        color = colors[idx % len(colors)]
        
        fig.add_trace(go.Scatter(
            x=sorted_weeks,
            y=ratings,
            mode='lines+markers',
            name=team,
            line=dict(width=2, color=color, dash=dash_style),
            marker=dict(symbol=marker, size=8)
        ))
        
    # Dropdown menus for filtering teams
    top_6_teams = sorted_teams[:6]
    bottom_6_teams = sorted_teams[6:]
    
    dropdown_buttons = [
        dict(
            label="All Teams",
            method="update",
            args=[{"visible": [True] * len(sorted_teams)}]
        ),
        dict(
            label="Top 6 Teams",
            method="update",
            args=[{"visible": [team in top_6_teams for team in sorted_teams]}]
        ),
        dict(
            label="Bottom 6 Teams",
            method="update",
            args=[{"visible": [team in bottom_6_teams for team in sorted_teams]}]
        )
    ]
    
    # Add an individual option for each team
    for target_team in sorted_teams:
        dropdown_buttons.append(
            dict(
                label=target_team,
                method="update",
                args=[{"visible": [team == target_team for team in sorted_teams]}]
            )
        )
    
    updatemenus = [
        dict(
            type="dropdown",
            direction="down",
            x=0.0,
            xanchor="left",
            y=1.15,
            yanchor="top",
            buttons=dropdown_buttons
        )
    ]
        
    fig.update_layout(
        # title=title,
        xaxis_title="Week",
        yaxis=dict(title=ylabel, range=y_range),
        legend_title="Teams",
        hovermode="x unified",
        template="plotly_white",
        updatemenus=updatemenus,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01,
            itemclick="toggleothers", # Clicking a legend item isolates it
            itemdoubleclick="toggle"
        ),
        xaxis=dict(
            type="category" # Ensure weeks are treated categorically
        ),
        margin=dict(r=150, t=100), # Make room for legend and dropdown
        width=1100,
        height=733
    )
    
    # Configure interactive options and high-res export
    config = {
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'mhc_plot',
            'height': 800,
            'width': 1200,
            'scale': 2 # High resolution export
        },
        'displaylogo': False
    }
    
    return fig.to_html(full_html=False, include_plotlyjs="cdn", config=config)
