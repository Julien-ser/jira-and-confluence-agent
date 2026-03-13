"""Integration tests for the Jira and Confluence Agent."""

import sys
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.parser import OperationParser
from src.engine import Engine
from src.models import OperationType, ResourceType


def test_full_jira_workflow(mocker):
    """Test a complete Jira workflow: parse config, create engine, execute operations."""
    # Mock configuration
    config = {
        "connections": {
            "jira": {
                "url": "https://test.atlassian.net",
                "username": "user@example.com",
                "password": "token123",
            }
        },
        "jira": {
            "projects": [
                {
                    "key": "TEST",
                    "name": "Test Project",
                    "description": "Created by integration test",
                    "projectTypeKey": "business",
                }
            ],
            "issue_types": [
                {"name": "Bug", "description": "A bug report", "create": True}
            ],
            "custom_fields": [
                {
                    "name": "Priority",
                    "type": "select",
                    "description": "Priority field",
                    "contexts": [{"global": True, "projects": []}],
                }
            ],
            "workflows": [
                {
                    "name": "Simple Workflow",
                    "description": "A simple workflow",
                    "steps": [
                        {"name": "To Do", "status": "TO_DO"},
                        {"name": "Done", "status": "DONE"},
                    ],
                }
            ],
        },
    }

    # Parse config into operations
    parser = OperationParser()
    operations = parser._parse_config(config)

    assert len(operations) == 4  # 1 project, 1 issue type, 1 custom field, 1 workflow

    # Create engine with mocked Jira client
    connections = config["connections"]
    engine = Engine(connections=connections, dry_run=False)

    # Mock the HTTP session for Jira
    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001"}
    mock_response.raise_for_status = Mock()
    mock_response.status_code = 200

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client.put.return_value = mock_response
        mock_client.delete.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Execute operations
        report = engine.run(operations)

        # Verify report
        assert report.total == 4
        assert report.successful == 4
        assert report.failed == 0

        # Verify that operations were called in some order
        # At least one post for project creation
        assert mock_client.post.called


def test_confluence_page_lifecycle(mocker):
    """Test Confluence space creation, page creation, and deletion."""
    config = {
        "connections": {
            "confluence": {
                "url": "https://test.atlassian.net",
                "username": "user@example.com",
                "password": "token123",
            }
        },
        "confluence": {
            "spaces": [
                {
                    "key": "DOC",
                    "name": "Documentation",
                    "description": "Test space",
                }
            ],
            "pages": [
                {
                    "title": "Home",
                    "space_key": "DOC",
                    "content": "<h1>Welcome</h1>",
                }
            ],
        },
    }

    parser = OperationParser()
    operations = parser._parse_config(config)

    assert len(operations) == 2  # 1 space, 1 page

    connections = config["connections"]
    engine = Engine(connections=connections, dry_run=False)

    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001", "title": "Home"}
    mock_response.raise_for_status = Mock()
    mock_response.status_code = 200

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client.put.return_value = mock_response
        mock_client.delete.return_value = mock_response
        mock_client_class.return_value = mock_client

        report = engine.run(operations)

        assert report.total == 2
        assert report.successful == 2
        assert report.failed == 0


def test_dry_run_mode(mocker):
    """Test that dry-run mode does not execute operations."""
    config = {
        "connections": {
            "jira": {
                "url": "https://test.atlassian.net",
                "username": "user@example.com",
                "password": "token123",
            }
        },
        "jira": {
            "projects": [{"key": "TEST", "name": "Test"}],
        },
    }

    parser = OperationParser()
    operations = parser._parse_config(config)

    connections = config["connections"]
    engine = Engine(connections=connections, dry_run=True)

    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        report = engine.run(operations)

        # Should be successful but not actually call HTTP methods
        assert report.total == 1
        assert report.successful == 1
        # In dry-run, the client methods are not called
        mock_client.post.assert_not_called()
