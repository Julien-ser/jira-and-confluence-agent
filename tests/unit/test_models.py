"""Tests for models module."""

from datetime import datetime
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.models import (
    OperationType,
    ResourceType,
    Operation,
    ConnectionConfig,
    Report,
)


def test_operation_type_enum():
    """Test OperationType enum values."""
    assert OperationType.CREATE.value == "create"
    assert OperationType.UPDATE.value == "update"
    assert OperationType.DELETE.value == "delete"
    assert OperationType.GET.value == "get"


def test_resource_type_enum():
    """Test ResourceType enum values."""
    assert ResourceType.JIRA_PROJECT.value == "jira_project"
    assert ResourceType.JIRA_ISSUE_TYPE.value == "jira_issue_type"
    assert ResourceType.JIRA_WORKFLOW.value == "jira_workflow"
    assert ResourceType.JIRA_CUSTOM_FIELD.value == "jira_custom_field"
    assert ResourceType.CONFLUENCE_SPACE.value == "confluence_space"
    assert ResourceType.CONFLUENCE_PAGE.value == "confluence_page"
    assert ResourceType.CONFLUENCE_TEMPLATE.value == "confluence_template"


def test_operation_to_dict():
    """Test Operation.to_dict method."""
    op = Operation(
        op_type=OperationType.CREATE,
        resource_type=ResourceType.JIRA_PROJECT,
        resource_id="TEST",
        params={"key": "TEST", "name": "Test Project"},
        description="Create test project",
    )
    d = op.to_dict()
    assert d["operation"] == "create"
    assert d["resource"] == "jira_project"
    assert d["id"] == "TEST"
    assert d["params"]["key"] == "TEST"
    assert d["description"] == "Create test project"


def test_report_initialization():
    """Test Report object initialization."""
    report = Report(total=5, successful=0, failed=0)
    assert report.total == 5
    assert report.successful == 0
    assert report.failed == 0
    assert report.success_rate == 0.0


def test_report_add_result():
    """Test Report.add_result method."""
    report = Report(total=2, successful=0, failed=0)
    op = Operation(
        op_type=OperationType.CREATE,
        resource_type=ResourceType.JIRA_PROJECT,
        resource_id="TEST",
        params={},
    )

    # Add successful result
    report.add_result(op, True)
    assert report.successful == 1
    assert report.failed == 0

    # Add failed result
    report.add_result(op, False, error="Test error")
    assert report.successful == 1
    assert report.failed == 1
    assert not report.operations[-1]["success"]
    assert report.operations[-1]["error"] == "Test error"


def test_report_success_rate():
    """Test Report.success_rate property."""
    report = Report(total=10, successful=7, failed=3)
    assert report.success_rate == 70.0

    report = Report(total=0, successful=0, failed=0)
    assert report.success_rate == 0.0


def test_connection_config():
    """Test ConnectionConfig dataclass."""
    config = ConnectionConfig(
        url="https://test.atlassian.net",
        username="test@example.com",
        password="token123",
        verify_ssl=True,
        timeout=30,
    )
    assert config.url == "https://test.atlassian.net"
    assert config.username == "test@example.com"
    assert config.password == "token123"
    assert config.verify_ssl is True
    assert config.timeout == 30
