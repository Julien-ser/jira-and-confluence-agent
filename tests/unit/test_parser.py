"""Tests for parser module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.parser import OperationParser
from src.models import OperationType, ResourceType


def test_parse_jira_project():
    """Test parsing Jira project configuration."""
    config = {
        "jira": {
            "projects": [
                {
                    "key": "TEST",
                    "name": "Test Project",
                    "description": "A test project",
                    "projectTypeKey": "business",
                }
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_jira_operations(config["jira"])

    assert len(operations) == 1
    op = operations[0]
    assert op.op_type == OperationType.CREATE
    assert op.resource_type == ResourceType.JIRA_PROJECT
    assert op.resource_id == "TEST"
    assert op.params["key"] == "TEST"
    assert "Create Jira project TEST" in op.description


def test_parse_jira_issue_types():
    """Test parsing Jira issue types configuration."""
    config = {
        "jira": {
            "issue_types": [
                {"name": "Bug", "description": "A bug", "create": True},
                {"name": "Task", "description": "A task", "create": False},
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_jira_operations(config["jira"])

    assert len(operations) == 2
    assert operations[0].op_type == OperationType.CREATE
    assert operations[0].resource_type == ResourceType.JIRA_ISSUE_TYPE
    assert operations[0].resource_id == "Bug"
    assert operations[1].op_type == OperationType.UPDATE
    assert operations[1].resource_id == "Task"


def test_parse_jira_workflows():
    """Test parsing Jira workflows configuration."""
    config = {
        "jira": {
            "workflows": [
                {
                    "name": "Standard Workflow",
                    "description": "Basic workflow",
                    "steps": [
                        {"name": "To Do", "status": "TO_DO"},
                        {"name": "In Progress", "status": "IN_PROGRESS"},
                        {"name": "Done", "status": "DONE"},
                    ],
                }
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_jira_operations(config["jira"])

    assert len(operations) == 1
    op = operations[0]
    assert op.op_type == OperationType.CREATE
    assert op.resource_type == ResourceType.JIRA_WORKFLOW
    assert op.resource_id == "Standard Workflow"
    assert "steps" in op.params


def test_parse_jira_custom_fields():
    """Test parsing Jira custom fields configuration."""
    config = {
        "jira": {
            "custom_fields": [
                {
                    "name": "Customer Impact",
                    "type": "select",
                    "description": "Customer impact level",
                    "contexts": [{"global": True, "projects": []}],
                }
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_jira_operations(config["jira"])

    assert len(operations) == 1
    op = operations[0]
    assert op.op_type == OperationType.CREATE
    assert op.resource_type == ResourceType.JIRA_CUSTOM_FIELD
    assert op.resource_id == "Customer Impact"
    assert op.params["field_type"] == "select"


def test_parse_confluence_spaces():
    """Test parsing Confluence spaces configuration."""
    config = {
        "confluence": {
            "spaces": [
                {
                    "key": "DOC",
                    "name": "Documentation",
                    "description": "Docs space",
                    "create": True,
                }
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_confluence_operations(config["confluence"])

    assert len(operations) == 1
    op = operations[0]
    assert op.op_type == OperationType.CREATE
    assert op.resource_type == ResourceType.CONFLUENCE_SPACE
    assert op.resource_id == "DOC"


def test_parse_confluence_pages():
    """Test parsing Confluence pages configuration."""
    config = {
        "confluence": {
            "pages": [
                {
                    "title": "Home Page",
                    "space_key": "DOC",
                    "content": "<h1>Welcome</h1>",
                    "create": True,
                }
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_confluence_operations(config["confluence"])

    assert len(operations) == 1
    op = operations[0]
    assert op.op_type == OperationType.CREATE
    assert op.resource_type == ResourceType.CONFLUENCE_PAGE
    assert op.resource_id == "Home Page"
    assert op.params["space_key"] == "DOC"


def test_parse_confluence_templates():
    """Test parsing Confluence templates configuration."""
    config = {
        "confluence": {
            "templates": [
                {
                    "name": "Meeting Notes",
                    "space_key": "DOC",
                    "content": "<h1>Meeting</h1>",
                    "description": "Template for meetings",
                }
            ]
        }
    }
    parser = OperationParser()
    operations = parser._parse_confluence_operations(config["confluence"])

    assert len(operations) == 1
    op = operations[0]
    assert op.op_type == OperationType.CREATE
    assert op.resource_type == ResourceType.CONFLUENCE_TEMPLATE
    assert op.resource_id == "Meeting Notes"


def test_parse_full_config():
    """Test parsing a full configuration with both Jira and Confluence."""
    config = {
        "connections": {"jira": {}, "confluence": {}},
        "jira": {
            "projects": [{"key": "PROJ1", "name": "Project 1"}],
            "custom_fields": [{"name": "Field1", "type": "text"}],
        },
        "confluence": {
            "spaces": [{"key": "SPACE1", "name": "Space 1"}],
            "pages": [{"title": "Page1", "space_key": "SPACE1", "content": "Content"}],
        },
    }
    parser = OperationParser()
    operations = parser._parse_config(config)

    assert len(operations) == 4
    resources = [op.resource_type for op in operations]
    assert ResourceType.JIRA_PROJECT in resources
    assert ResourceType.JIRA_CUSTOM_FIELD in resources
    assert ResourceType.CONFLUENCE_SPACE in resources
    assert ResourceType.CONFLUENCE_PAGE in resources


def test_parser_empty_config():
    """Test parsing empty configuration."""
    config = {}
    parser = OperationParser()
    operations = parser._parse_config(config)
    assert len(operations) == 0


def test_parser_missing_project_key():
    """Test that project without key generates empty resource_id."""
    config = {"jira": {"projects": [{"name": "No Key Project"}]}}
    parser = OperationParser()
    operations = parser._parse_jira_operations(config["jira"])
    assert len(operations) == 1
    assert operations[0].resource_id == ""  # Empty key
