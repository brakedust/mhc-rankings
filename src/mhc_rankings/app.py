import argparse
import sys
from pathlib import Path

from .io import (
    get_latest_game_date,
    load_games_data,
    save_colley_matrix_tsv,
    save_rankings_tsv,
    save_weekly_ratings_tsv,
)
from .plotting import save_matplotlib_plot
from .rankings_math import compute_weekly_ratings, solve_colley_matrix
from .reporting import generate_html_report


def main() -> None:
    parser = argparse.ArgumentParser(description="MHC Hockey Colley Matrix Rankings Generator")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to the input TSV file containing game results."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=".", 
        help="Directory to save the generated report and data files."
    )
    parser.add_argument(
        "--plot-engine", 
        type=str, 
        choices=["matplotlib", "plotly"], 
        default="matplotlib",
        help="The plotting engine to use in the HTML report."
    )
    parser.add_argument(
        "--skip-raw", 
        action="store_true", 
        help="Skip saving the raw TSV and PNG files."
    )
    parser.add_argument(
        "--include-sos-plot", 
        action="store_true", 
        help="Include a progress plot of the Strength of Schedule in the HTML report."
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data from {input_path}...")
    df = load_games_data(input_path)
    
    if df.empty:
        print("Error: No data found in the input file.", file=sys.stderr)
        sys.exit(1)
        
    latest_date = get_latest_game_date(df)
    print(f"Latest game date identified as: {latest_date}")
    
    print("Computing Colley matrix and rankings...")
    rankings, matrix, teams = solve_colley_matrix(df)
    
    print("Computing weekly ratings progress...")
    weekly_ratings, weekly_sos, _ = compute_weekly_ratings(df)
    
    if not args.skip_raw:
        rankings_file = output_dir / "rankings_output.tsv"
        matrix_file = output_dir / "colley_matrix_output.tsv"
        weekly_file = output_dir / "weekly_ratings_output.tsv"
        plot_file = output_dir / "weekly_ratings_plot.png"
        
        print("Saving raw data files...")
        save_rankings_tsv(rankings, rankings_file)
        save_colley_matrix_tsv(matrix, teams, matrix_file)
        save_weekly_ratings_tsv(weekly_ratings, teams, weekly_file)
        save_matplotlib_plot(weekly_ratings, teams, plot_file, "MHC Colley Ratings Progress", "Colley Rating")
        
        if args.include_sos_plot:
            sos_plot_file = output_dir / "weekly_sos_plot.png"
            save_matplotlib_plot(weekly_sos, teams, sos_plot_file, "Strength of Schedule Progress", "SOS")
        
    report_file = output_dir / "mhc_rankings_report.html"
    print(f"Generating HTML report ({args.plot_engine})...")
    generate_html_report(
        date_str=latest_date,
        rankings=rankings,
        matrix=matrix,
        teams=teams,
        weekly_ratings=weekly_ratings,
        plot_engine=args.plot_engine,
        output_path=report_file,
        weekly_sos=weekly_sos if args.include_sos_plot else None
    )
    
    print(f"Done! Report saved to {report_file}")


if __name__ == "__main__":
    main()
