"""Core models and data structures for Jira and Confluence operations."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    GET = "get"


class ResourceType(Enum):
    JIRA_PROJECT = "jira_project"
    JIRA_ISSUE_TYPE = "jira_issue_type"
    JIRA_WORKFLOW = "jira_workflow"
    JIRA_CUSTOM_FIELD = "jira_custom_field"
    JIRA_FIELD = "jira_field"
    JIRA_SCREEN = "jira_screen"
    CONFLUENCE_SPACE = "confluence_space"
    CONFLUENCE_PAGE = "confluence_page"
    CONFLUENCE_TEMPLATE = "confluence_template"


@dataclass
class Operation:
    """Represents a single administrative operation."""

    op_type: OperationType
    resource_type: ResourceType
    resource_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.op_type.value,
            "resource": self.resource_type.value,
            "id": self.resource_id,
            "params": self.params,
            "description": self.description,
        }


@dataclass
class ConnectionConfig:
    """Configuration for connecting to Jira/Confluence."""

    url: str
    username: str
    password: str  # or API token
    verify_ssl: bool = True
    timeout: int = 30


@dataclass
class Report:
    """Results of an operation batch."""

    total: int
    successful: int
    failed: int
    operations: List[Dict[str, Any]] = field(default_factory=list)

    def add_result(
        self, operation: Operation, success: bool, error: Optional[str] = None
    ):
        result = {"operation": operation.to_dict(), "success": success, "error": error}
        self.operations.append(result)
        if success:
            self.successful += 1
        else:
            self.failed += 1

    @property
    def success_rate(self) -> float:
        return (self.successful / self.total * 100) if self.total > 0 else 0.0
