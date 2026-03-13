"""Parse configuration files into executable operations."""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import Operation, OperationType, ResourceType


class OperationParser:
    """Parses configuration into operations to be executed."""

    def __init__(self):
        self.operations: List[Operation] = []

    def _clean_and_map_params(
        self,
        params: Dict[str, Any],
        key_mappings: Optional[Dict[str, str]] = None,
        remove_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Clean and map configuration parameters to match client method signatures.

        Args:
            params: Original parameters dict from config
            key_mappings: Mapping of config keys to client keys (e.g., {'projectTypeKey': 'project_type_key'})
            remove_keys: List of keys to remove (e.g., ['create'])

        Returns:
            Cleaned and mapped parameter dict
        """
        cleaned = params.copy()
        # Remove specified keys
        if remove_keys:
            for key in remove_keys:
                cleaned.pop(key, None)
        # Rename keys according to mappings
        if key_mappings:
            for old_key, new_key in key_mappings.items():
                if old_key in cleaned:
                    cleaned[new_key] = cleaned.pop(old_key)
        return cleaned

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
            # Map configuration keys to client parameter names
            params = self._clean_and_map_params(
                project,
                key_mappings={"projectTypeKey": "project_type_key"},
                remove_keys=["create"],
            )
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.JIRA_PROJECT,
                resource_id=project.get("key", ""),
                params=params,
                description=f"Create Jira project {project.get('key')}",
            )
            ops.append(op)

        # Issue Types
        for issue_type in config.get("issue_types", []):
            params = self._clean_and_map_params(
                issue_type,
                remove_keys=["create"],
            )
            op = Operation(
                op_type=OperationType.CREATE
                if issue_type.get("create", True)
                else OperationType.UPDATE,
                resource_type=ResourceType.JIRA_ISSUE_TYPE,
                resource_id=issue_type.get("name", ""),
                params=params,
                description=f"Manage issue type {issue_type.get('name')}",
            )
            ops.append(op)

        # Workflows
        for workflow in config.get("workflows", []):
            params = self._clean_and_map_params(
                workflow,
                remove_keys=["create"],
            )
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.JIRA_WORKFLOW,
                resource_id=workflow.get("name", ""),
                params=params,
                description=f"Create workflow {workflow.get('name')}",
            )
            ops.append(op)

        # Custom Fields
        for field in config.get("custom_fields", []):
            params = self._clean_and_map_params(
                field,
                key_mappings={"type": "field_type"},
                remove_keys=["create"],
            )
            op = Operation(
                op_type=OperationType.CREATE,
                resource_type=ResourceType.JIRA_CUSTOM_FIELD,
                resource_id=field.get("name", ""),
                params=params,
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
