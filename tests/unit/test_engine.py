"""Tests for engine module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.engine import Engine
from src.models import Operation, OperationType, ResourceType, Report
from src.jira_client import JiraClient
from src.confluence_client import ConfluenceClient


def test_engine_initialization():
    """Test Engine initialization with connections."""
    connections = {
        "jira": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        },
        "confluence": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        },
    }
    engine = Engine(connections=connections, dry_run=False)
    assert engine.connections == connections
    assert engine.dry_run is False


def test_engine_dry_run_mode():
    """Test Engine dry run mode."""
    connections = {
        "jira": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        }
    }
    engine = Engine(connections=connections, dry_run=True)
    assert engine.dry_run is True


def test_engine_jira_client_property():
    """Test Engine creates JiraClient on demand."""
    connections = {
        "jira": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        }
    }
    engine = Engine(connections=connections)
    assert engine._jira_client is None
    client = engine.jira_client
    assert isinstance(client, JiraClient)
    assert client.base_url == "https://test.atlassian.net"
    # Should return same instance on subsequent access
    client2 = engine.jira_client
    assert client is client2


def test_engine_confluence_client_property():
    """Test Engine creates ConfluenceClient on demand."""
    connections = {
        "confluence": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        }
    }
    engine = Engine(connections=connections)
    assert engine._confluence_client is None
    client = engine.confluence_client
    assert isinstance(client, ConfluenceClient)
    assert client.base_url == "https://test.atlassian.net"


def test_engine_client_property_missing_connection():
    """Test Engine returns None for missing connection."""
    engine = Engine(connections={})
    assert engine.jira_client is None
    assert engine.confluence_client is None


def test_execute_operation_dry_run():
    """Test execute_operation in dry-run mode."""
    connections = {
        "jira": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        }
    }
    engine = Engine(connections=connections, dry_run=True)
    op = Operation(
        op_type=OperationType.CREATE,
        resource_type=ResourceType.JIRA_PROJECT,
        resource_id="TEST",
        params={"key": "TEST", "name": "Test"},
        description="Create test project",
    )
    result = engine.execute_operation(op)
    assert result["success"] is True
    assert result["dry_run"] is True
    assert "not executed" in result["message"]


def test_execute_operation_unknown_resource_type():
    """Test execute_operation with unknown resource type."""

    # Create a custom resource type that's not handled using a simple object
    class FakeResourceType:
        value = "unknown_test_type"

    fake_rt = FakeResourceType()
    connections = {
        "jira": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        }
    }
    engine = Engine(connections=connections)
    op = Operation(
        op_type=OperationType.CREATE,
        resource_type=fake_rt,
        resource_id="TEST",
        params={},
        description="Unknown operation",
    )
    result = engine.execute_operation(op)
    assert result["success"] is False
    assert "No client available" in result["error"]


def test_run_executes_all_operations(mocker):
    """Test run method executes all operations and generates report."""
    connections = {
        "jira": {
            "url": "https://test.atlassian.net",
            "username": "user",
            "password": "pass",
        }
    }
    engine = Engine(connections=connections, dry_run=True)

    operations = [
        Operation(
            op_type=OperationType.CREATE,
            resource_type=ResourceType.JIRA_PROJECT,
            resource_id="PROJ1",
            params={"key": "PROJ1", "name": "Project 1"},
            description="Create project 1",
        ),
        Operation(
            op_type=OperationType.CREATE,
            resource_type=ResourceType.CONFLUENCE_SPACE,
            resource_id="SPACE1",
            params={"key": "SPACE1", "name": "Space 1"},
            description="Create space 1",
        ),
    ]

    report = engine.run(operations)

    assert report.total == 2
    assert report.successful == 2
    assert report.failed == 0
    assert len(report.operations) == 2
    assert report.success_rate == 100.0
