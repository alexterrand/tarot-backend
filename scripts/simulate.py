#!/usr/bin/env python3
"""
CLI script to run AI-vs-AI tarot game simulations.

Usage:
    python scripts/simulate.py --games 100 --p1 bot-naive --p2 bot-random --p3 bot-naive --p4 bot-random
    python scripts/simulate.py --games 1000 --all-bots bot-naive
    python scripts/simulate.py --games 50 --p1 bot-naive --p2 bot-random --p3 bot-naive --p4 bot-random --seed 42
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import app modules
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.simulation_service import SimulationService


def main():
    """Main CLI entry point for running simulations."""
    parser = argparse.ArgumentParser(
        description="Run AI-vs-AI Tarot game simulations for benchmarking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 100 games with mixed strategies
  python scripts/simulate.py --games 100 --p1 bot-naive --p2 bot-random --p3 bot-naive --p4 bot-random

  # Run 1000 games with all naive bots
  python scripts/simulate.py --games 1000 --all-bots bot-naive

  # Run with seed for reproducibility
  python scripts/simulate.py --games 50 --p1 bot-naive --p2 bot-random --p3 bot-naive --p4 bot-random --seed 42
        """,
    )

    parser.add_argument(
        "--games",
        type=int,
        required=True,
        help="Number of games to simulate",
    )

    parser.add_argument(
        "--p1",
        type=str,
        help="Strategy for Player 1 (e.g., bot-naive, bot-random)",
    )
    parser.add_argument(
        "--p2",
        type=str,
        help="Strategy for Player 2",
    )
    parser.add_argument(
        "--p3",
        type=str,
        help="Strategy for Player 3",
    )
    parser.add_argument(
        "--p4",
        type=str,
        help="Strategy for Player 4",
    )

    parser.add_argument(
        "--all-bots",
        type=str,
        help="Use the same strategy for all players (overrides individual --p1, --p2, etc.)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility (optional)",
    )

    args = parser.parse_args()

    # Validate and build player strategies
    if args.all_bots:
        # All players use the same strategy
        player_strategies = {
            "player_1": args.all_bots,
            "player_2": args.all_bots,
            "player_3": args.all_bots,
            "player_4": args.all_bots,
        }
        print(f"All players using strategy: {args.all_bots}\n")
    else:
        # Check that all player strategies are specified
        if not all([args.p1, args.p2, args.p3, args.p4]):
            parser.error(
                "Must specify either --all-bots or all of --p1, --p2, --p3, --p4"
            )

        player_strategies = {
            "player_1": args.p1,
            "player_2": args.p2,
            "player_3": args.p3,
            "player_4": args.p4,
        }
        print(f"Player strategies: {player_strategies}\n")

    # Validate number of games
    if args.games <= 0:
        parser.error("Number of games must be positive")

    # Create simulation service
    sim_service = SimulationService()

    # Run simulation
    try:
        print(f"Starting simulation of {args.games} games...")
        if args.seed is not None:
            print(f"Using seed: {args.seed}")
        print()

        results = sim_service.run_simulation(
            num_games=args.games, player_strategies=player_strategies, seed=args.seed
        )

        # Display results
        print("\n" + "=" * 60)
        print("=== SIMULATION RESULTS ===")
        print("=" * 60)
        print(f"\nTotal Games: {results.total_games}")
        print(f"Strategies:")
        for player_id, strategy in results.player_strategies.items():
            print(f"  {player_id}: {strategy}")

        print(f"\nWin Counts:")
        for player_id in sorted(results.win_counts.keys()):
            count = results.win_counts[player_id]
            rate = results.win_rates[player_id]
            print(f"  {player_id}: {count} ({rate:.1%})")

        print(f"\nAverage Scores:")
        for player_id in sorted(results.avg_scores.keys()):
            avg = results.avg_scores[player_id]
            print(f"  {player_id}: {avg:.1f}")

        print(f"\nAll {results.games_logged_to_supabase} games logged to Supabase.")
        print("=" * 60)

    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
