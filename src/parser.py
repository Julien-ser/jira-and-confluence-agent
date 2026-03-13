"""Parse configuration files into executable operations."""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from .models import Operation, OperationType, ResourceType


class OperationParser:
    """Parses configuration into operations to be executed."""

    def __init__(self):
        self.operations: List[Operation] = []

    def parse_file(self, config_path: str) -> List[Operation]:
        """Parse a configuration file into a list of operations."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            config = yaml.safe_load(f)

        return self._parse_config(config, source=path.name)

    def _parse_config(
        self, config: Dict[str, Any], source: str = ""
    ) -> List[Operation]:
        """Parse configuration dictionary."""
        operations = []

        # Global settings
        connections = config.get("connections", {})

        # Parse Jira operations
        jira_config = config.get("jira", {})
        if jira_config:
            operations.extend(self._parse_jira_operations(jira_config))

        # Parse Confluence operations
        confluence_config = config.get("confluence", {})
        if confluence_config:
            operations.extend(self._parse_confluence_operations(confluence_config))

        return operations

    def _parse_jira_operations(self, config: Dict[str, Any]) -> List[Operation]:
        """Parse Jira-specific operations."""
        ops = []

        # Projects
        for project in config.get("projects", []):
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.JIRA_PROJECT,
                resource_id=project.get("key", ""),
                params=project,
                description=f"Create Jira project {project.get('key')}",
            )
            ops.append(op)

        # Issue Types
        for issue_type in config.get("issue_types", []):
            op = Operation(
                op_type=OperationType.CREATE
                if issue_type.get("create", True)
                else OperationType.UPDATE,
                resource_type=ResourceType.JIRA_ISSUE_TYPE,
                resource_id=issue_type.get("name", ""),
                params=issue_type,
                description=f"Manage issue type {issue_type.get('name')}",
            )
            ops.append(op)

        # Workflows
        for workflow in config.get("workflows", []):
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.JIRA_WORKFLOW,
                resource_id=workflow.get("name", ""),
                params=workflow,
                description=f"Create workflow {workflow.get('name')}",
            )
            ops.append(op)

        # Custom Fields
        for field in config.get("custom_fields", []):
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.JIRA_CUSTOM_FIELD,
                resource_id=field.get("name", ""),
                params=field,
                description=f"Create custom field {field.get('name')}",
            )
            ops.append(op)

        return ops

    def _parse_confluence_operations(self, config: Dict[str, Any]) -> List[Operation]:
        """Parse Confluence-specific operations."""
        ops = []

        # Spaces
        for space in config.get("spaces", []):
            op = Operation(
                op_type=OperationType.CREATE
                if space.get("create", True)
                else OperationType.UPDATE,
                resource_type=ResourceType.CONFLUENCE_SPACE,
                resource_id=space.get("key", ""),
                params=space,
                description=f"Manage Confluence space {space.get('key')}",
            )
            ops.append(op)

        # Pages
        for page in config.get("pages", []):
            op = Operation(
                op_type=OperationType.CREATE
                if page.get("create", True)
                else OperationType.UPDATE,
                resource_type=ResourceType.CONFLUENCE_PAGE,
                resource_id=page.get("title", ""),
                params=page,
                description=f"{'Create' if page.get('create', True) else 'Update'} page '{page.get('title')}'",
            )
            ops.append(op)

        # Templates
        for template in config.get("templates", []):
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.CONFLUENCE_TEMPLATE,
                resource_id=template.get("name", ""),
                params=template,
                description=f"Create template {template.get('name')}",
            )
            ops.append(op)

        return ops
