#!/usr/bin/env python3
"""Main CLI entry point for Jira and Confluence Agent."""

import argparse
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.parser import OperationParser
from src.engine import Engine
from src.utils import load_config


def main():
    """Run the Jira and Confluence Agent."""
    parser = argparse.ArgumentParser(
        description="Jira and Confluence Agent - Automate admin tasks"
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to configuration file (YAML or JSON)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for logs and reports (default: logs)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    log_level = "DEBUG" if args.verbose else "INFO"

    try:
        # Load configuration
        config = load_config(args.config)
        connections = config.get("connections", {})

        if not connections:
            print("Error: No connections configured in the config file")
            sys.exit(1)

        # Create and run engine
        with Engine(
            connections=connections,
            dry_run=args.dry_run,
            log_dir=args.log_dir,
        ) as engine:
            # Parse operations
            parser_obj = OperationParser()
            operations = parser_obj.parse_file(args.config)

            if not operations:
                print("No operations found in configuration")
                sys.exit(0)

            # Execute
            print(f"Executing {len(operations)} operations...")
            if args.dry_run:
                print("DRY RUN - no changes will be made")

            report = engine.run(operations)

            # Print summary
            print("\n" + "=" * 50)
            print("Execution Complete")
            print("=" * 50)
            print(f"Total: {report.total}")
            print(f"Successful: {report.successful}")
            print(f"Failed: {report.failed}")
            print(f"Success Rate: {report.success_rate:.1f}%")

            if report.failed > 0:
                print("\nFailed operations:")
                for op_result in report.operations:
                    if not op_result["success"]:
                        print(
                            f"  - {op_result['operation']['resource']}:"
                            f"{op_result['operation']['id']}: "
                            f"{op_result['error']}"
                        )
                sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
