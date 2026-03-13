"""Main entry point for the Jira and Confluence Agent."""

import sys
from pathlib import Path
import argparse

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.parser import OperationParser
from src.engine import Engine
from src.reporter import Reporter
from src.utils import load_config, setup_logging


def main():
    """Main entry point for the agent."""
    parser = argparse.ArgumentParser(
        description="Jira and Confluence Agent - Automate administrative tasks"
    )
    parser.add_argument(
        "config",
        help="Path to configuration file (YAML or JSON)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without executing them",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for logs and reports (default: logs)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_dir=args.log_dir, level=log_level)

    try:
        # Load configuration
        print(f"Loading configuration from {args.config}...")
        config = load_config(args.config)

        # Parse operations
        print("Parsing operations...")
        operation_parser = OperationParser()
        operations = operation_parser.parse_file(args.config)

        if not operations:
            print("No operations to execute.")
            return 0

        print(f"Found {len(operations)} operations to execute.")
        print(f"Dry run: {args.dry_run}")

        # Get connections from config
        connections = config.get("connections", {})

        # Create and run engine
        print("Starting execution...")
        engine = Engine(
            connections=connections,
            dry_run=args.dry_run,
            log_dir=args.log_dir,
        )

        with engine:
            report = engine.run(operations)

        # Print summary
        print("\n" + "=" * 50)
        print("EXECUTION COMPLETE")
        print("=" * 50)
        print(f"Total: {report.total}")
        print(f"Successful: {report.successful}")
        print(f"Failed: {report.failed}")
        print(f"Success Rate: {report.success_rate:.1f}%")
        print(f"Logs: {args.log_dir}/")
        print("=" * 50)

        return 0 if report.failed == 0 else 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
