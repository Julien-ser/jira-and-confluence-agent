"""Core operation engine - orchestrates execution of operations."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    Operation,
    OperationType,
    ResourceType,
    Report,
)
from .jira_client import JiraClient
from .confluence_client import ConfluenceClient
from .reporter import Reporter
from .utils import setup_logging

logger = logging.getLogger(__name__)


class Engine:
    """Orchestrates execution of administrative operations."""

    def __init__(
        self,
        connections: Dict[str, Any],
        dry_run: bool = False,
        log_dir: str = "logs",
    ):
        self.connections = connections
        self.dry_run = dry_run
        self.reporter = Reporter(output_dir=log_dir)
        setup_logging(log_dir=log_dir)

        # Clients will be created on demand
        self._jira_client: Optional[JiraClient] = None
        self._confluence_client: Optional[ConfluenceClient] = None

    @property
    def jira_client(self) -> Optional[JiraClient]:
        """Get or create Jira client."""
        if self._jira_client is None:
            jira_cfg = self.connections.get("jira")
            if jira_cfg:
                self._jira_client = JiraClient(
                    base_url=jira_cfg["url"],
                    username=jira_cfg["username"],
                    password=jira_cfg["password"],
                    verify_ssl=jira_cfg.get("verify_ssl", True),
                )
        return self._jira_client

    @property
    def confluence_client(self) -> Optional[ConfluenceClient]:
        """Get or create Confluence client."""
        if self._confluence_client is None:
            confluence_cfg = self.connections.get("confluence")
            if confluence_cfg:
                self._confluence_client = ConfluenceClient(
                    base_url=confluence_cfg["url"],
                    username=confluence_cfg["username"],
                    password=confluence_cfg["password"],
                    verify_ssl=confluence_cfg.get("verify_ssl", True),
                )
        return self._confluence_client

    def execute_operation(self, operation: Operation) -> Dict[str, Any]:
        """Execute a single operation."""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would execute: {operation.description}")
                return {
                    "success": True,
                    "dry_run": True,
                    "message": "Dry run - not executed",
                }

            client = self._get_client_for_resource(operation.resource_type)
            if client is None:
                error_msg = (
                    f"No client available for resource type {operation.resource_type}"
                )
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            result = self._dispatch_operation(client, operation)
            logger.info(f"Executed: {operation.description}")
            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Operation failed: {operation.description}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _get_client_for_resource(self, resource_type: ResourceType):
        """Get the appropriate client for a resource type."""
        jira_resources = [
            ResourceType.JIRA_PROJECT,
            ResourceType.JIRA_ISSUE_TYPE,
            ResourceType.JIRA_WORKFLOW,
            ResourceType.JIRA_CUSTOM_FIELD,
            ResourceType.JIRA_FIELD,
            ResourceType.JIRA_SCREEN,
        ]
        confluence_resources = [
            ResourceType.CONFLUENCE_SPACE,
            ResourceType.CONFLUENCE_PAGE,
            ResourceType.CONFLUENCE_TEMPLATE,
        ]

        if resource_type in jira_resources:
            return self.jira_client
        elif resource_type in confluence_resources:
            return self.confluence_client
        else:
            logger.error(f"Unknown resource type: {resource_type}")
            return None

    def _dispatch_operation(self, client, operation: Operation) -> Any:
        """Dispatch operation to the appropriate client method."""
        resource = operation.resource_type
        op_type = operation.op_type
        params = operation.params

        # Map resource type and operation to method
        if resource == ResourceType.JIRA_PROJECT:
            if op_type == OperationType.CREATE:
                return client.create_project(**params)
            elif op_type == OperationType.UPDATE:
                return client.update_project(operation.resource_id, **params)
            elif op_type == OperationType.GET:
                return client.get_project(operation.resource_id)
            elif op_type == OperationType.DELETE:
                return client.delete_project(operation.resource_id)
            else:
                raise ValueError(f"Unsupported operation {op_type} for JIRA_PROJECT")

        elif resource == ResourceType.JIRA_CUSTOM_FIELD:
            if op_type == OperationType.CREATE:
                return client.create_custom_field(**params)
            elif op_type == OperationType.GET:
                return client.get_custom_fields()
            elif op_type == OperationType.DELETE:
                return client.delete_custom_field(operation.resource_id)
            else:
                raise ValueError(
                    f"Unsupported operation {op_type} for JIRA_CUSTOM_FIELD"
                )

        elif resource == ResourceType.JIRA_ISSUE_TYPE:
            if op_type in [OperationType.CREATE, OperationType.UPDATE]:
                return client.create_issue_type(**params)
            elif op_type == OperationType.DELETE:
                return client.delete_issue_type(operation.resource_id)
            else:
                raise ValueError(f"Unsupported operation {op_type} for JIRA_ISSUE_TYPE")

        elif resource == ResourceType.JIRA_WORKFLOW:
            if op_type in [OperationType.CREATE, OperationType.UPDATE]:
                return client.create_workflow(**params)
            elif op_type == OperationType.DELETE:
                return client.delete_workflow(operation.resource_id)
            else:
                raise ValueError(f"Unsupported operation {op_type} for JIRA_WORKFLOW")

        elif resource == ResourceType.CONFLUENCE_SPACE:
            if op_type == OperationType.CREATE:
                return client.create_space(**params)
            elif op_type == OperationType.UPDATE:
                return client.update_space(operation.resource_id, **params)
            elif op_type == OperationType.GET:
                return client.get_space(operation.resource_id)
            elif op_type == OperationType.DELETE:
                return client.delete_space(operation.resource_id)
            else:
                raise ValueError(
                    f"Unsupported operation {op_type} for CONFLUENCE_SPACE"
                )

        elif resource == ResourceType.CONFLUENCE_PAGE:
            if op_type == OperationType.CREATE:
                return client.create_page(**params)
            elif op_type == OperationType.UPDATE:
                # For update, need to get page_id from params or lookup
                page_id = params.get("id") or self._lookup_page_id(client, operation)
                if page_id:
                    # Need version for update
                    existing = client.get_page_by_title(
                        params.get("space_key"), operation.resource_id
                    )
                    if existing:
                        version = existing.get("version", {}).get("number")
                        return client.update_page(
                            page_id=page_id,
                            title=params.get("title", operation.resource_id),
                            content=params.get("content", ""),
                            version=version,
                        )
                raise ValueError(f"Cannot find page {operation.resource_id} for update")
            elif op_type == OperationType.DELETE:
                page_id = params.get("id") or self._lookup_page_id(client, operation)
                if page_id:
                    return client.delete_page(page_id)
                raise ValueError(f"Cannot find page {operation.resource_id} for delete")
            else:
                raise ValueError(f"Unsupported operation {op_type} for CONFLUENCE_PAGE")

        elif resource == ResourceType.CONFLUENCE_TEMPLATE:
            if op_type == OperationType.CREATE:
                return client.create_template(**params)
            elif op_type == OperationType.DELETE:
                return client.delete_template(operation.resource_id)
            else:
                raise ValueError(
                    f"Unsupported operation {op_type} for CONFLUENCE_TEMPLATE"
                )

        else:
            raise ValueError(f"Unsupported resource type: {resource}")

    def _lookup_page_id(
        self, client: ConfluenceClient, operation: Operation
    ) -> Optional[str]:
        """Look up page ID by title and space key."""
        params = operation.params
        space_key = params.get("space_key")
        title = operation.resource_id
        if space_key and title:
            page = client.get_page_by_title(space_key, title)
            if page:
                return page.get("id")
        return None

    def run(self, operations: List[Operation]) -> Report:
        """Execute a list of operations and generate a report."""
        logger.info(f"Starting execution of {len(operations)} operations")
        logger.info(f"Dry run: {self.dry_run}")

        report = Report(total=len(operations), successful=0, failed=0)

        for i, operation in enumerate(operations, 1):
            logger.info(
                f"Executing operation {i}/{len(operations)}: {operation.description}"
            )

            result = self.execute_operation(operation)

            report.add_result(
                operation=operation,
                success=result.get("success", False),
                error=result.get("error") if not result.get("success") else None,
            )

            # Log to audit
            self.reporter.log_operation(
                operation_name=f"{operation.op_type.value}:{operation.resource_type.value}",
                details={
                    "description": operation.description,
                    "params": operation.params,
                    "result": result,
                },
            )

        # Generate report files
        report_file = self.reporter.generate_report(report, dry_run=self.dry_run)
        logger.info(f"Report generated: {report_file}")

        logger.info(f"Execution complete. Success: {report.successful}/{report.total}")
        return report

    def close(self):
        """Close all client connections."""
        if self._jira_client:
            self._jira_client.close()
        if self._confluence_client:
            self._confluence_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
