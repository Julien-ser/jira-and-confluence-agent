"""Reporting and audit trail generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .models import Report


class Reporter:
    """Generates execution reports and saves audit logs."""

    def __init__(self, output_dir: str = "logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, report: Report, dry_run: bool = False) -> str:
        """Generate human-readable and machine-readable reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "dry_run_" if dry_run else ""

        # JSON report for machine processing
        json_file = self.output_dir / f"{prefix}report_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "dry_run": dry_run,
                    "total": report.total,
                    "successful": report.successful,
                    "failed": report.failed,
                    "success_rate": report.success_rate,
                    "operations": report.operations,
                },
                f,
                indent=2,
            )

        # Text summary
        summary = f"""
Execution Report
================
Timestamp: {timestamp}
Dry Run: {dry_run}
Total Operations: {report.total}
Successful: {report.successful}
Failed: {report.failed}
Success Rate: {report.success_rate:.1f}%

"""
        if report.failed > 0:
            summary += "Failed Operations:\n"
            for op_result in report.operations:
                if not op_result["success"]:
                    summary += f"  - {op_result['operation']['resource']}:{op_result['operation']['id']}: {op_result['error']}\n"

        txt_file = self.output_dir / f"{prefix}summary_{timestamp}.txt"
        with open(txt_file, "w") as f:
            f.write(summary.strip())

        return str(json_file)

    def log_operation(self, operation_name: str, details: Dict[str, Any]) -> None:
        """Log individual operation to audit file."""
        audit_file = self.output_dir / "audit.log"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_name,
            "details": details,
        }
        with open(audit_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
