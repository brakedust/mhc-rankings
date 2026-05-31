# MHC Rankings

MHC Rankings is a Python-based tool for calculating unbiased, mathematically robust team rankings using the **Colley Matrix** method. Originally designed for analyzing hockey game results, it generates accurate ratings, tracks week-by-week progress, calculates Strength of Schedule (SOS), and produces beautiful, interactive HTML reports.

## Features

- **Colley Matrix Algorithm:** Implements the Colley Matrix method, a bias-free ranking system that solves a system of linear equations based on wins, losses, and opponent strength.
- **Strength of Schedule (SOS):** Automatically tracks and computes the SOS for every team.
- **Weekly Progress Tracking:** Computes how team ratings and SOS change on a week-by-week basis.
- **Interactive HTML Reports:** Generates responsive HTML reports with interactive progress plots (supporting Plotly and Matplotlib).
- **Data Export:** Outputs raw ranking data and the complete Colley matrix into easy-to-read TSV files.

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (for dependency management and running the app)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/brakedust/mhc-rankings.git
   cd mhc-rankings
   ```

2. Sync dependencies:
   ```bash
   uv sync
   ```

## Usage

You can run the ranking generator using `uv run`. 

```bash
uv run mhc-rankings --input data/mhc-hockey/game_results_2025-26.tsv --output-dir data/mhc-hockey --plot-engine plotly --include-sos-plot
```

### Command Line Arguments

- `--input` (Required): Path to the input TSV file containing game results.
- `--output-dir`: Directory to save the generated report and data files. Defaults to the current directory (`.`).
- `--plot-engine`: The plotting engine to use in the HTML report. Choices are `matplotlib` or `plotly`. Defaults to `matplotlib`.
- `--skip-raw`: Skip saving the raw TSV data files and plot PNGs to the output directory.
- `--include-sos-plot`: Include an interactive progress plot of the Strength of Schedule in the HTML report.

### Input Data Format

The input should be a TSV (Tab-Separated Values) file containing the following columns at a minimum:
- `Date` (e.g., `2025-11-20`)
- `Away Team`
- `Home Team`
- `Score` (Formatted as `AwayScore-HomeScore`, e.g., `3-2`)

### Outputs

When run, the application will generate the following in the specified output directory:
- `mhc_rankings_report.html`: The main interactive visual report.
- `rankings_output.tsv`: Final rankings table data.
- `weekly_ratings_output.tsv`: Matrix of team ratings over time.
- `colley_matrix_output.tsv`: The final calculated Colley Matrix.

## References

- Colley, Wesley N. (Ph.D., Princeton University). *[Colley’s Bias Free College Football Ranking Method: The Colley Matrix Explained](https://www.colleyrankings.com/matrate.pdf)*

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.