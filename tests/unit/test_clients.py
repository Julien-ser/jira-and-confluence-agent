"""Tests for Jira and Confluence clients."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.jira_client import JiraClient
from src.confluence_client import ConfluenceClient


# JiraClient tests
def test_jira_client_initialization():
    """Test JiraClient initialization."""
    client = JiraClient(
        base_url="https://test.atlassian.net",
        username="user@example.com",
        password="token123",
        verify_ssl=True,
    )
    assert client.base_url == "https://test.atlassian.net"
    assert client.auth == ("user@example.com", "token123")
    assert client.verify_ssl is True
    assert client.session is None


def test_jira_client_get_session():
    """Test JiraClient creates session on first call."""
    client = JiraClient(
        base_url="https://test.atlassian.net",
        username="user@example.com",
        password="token123",
    )
    session = client._get_session()
    assert session is not None
    assert client.session is session
    # Second call should return same session
    session2 = client._get_session()
    assert session is session2
    client.close()


def test_jira_client_create_project(mocker):
    """Test JiraClient.create_project."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001", "key": "TEST"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = JiraClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.create_project(
            key="TEST",
            name="Test Project",
            project_type_key="business",
            description="Test",
        )

        assert result["key"] == "TEST"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/rest/api/3/project" in call_args[0][0]
        assert call_args[1]["json"]["key"] == "TEST"
        client.close()


def test_jira_client_get_project(mocker):
    """Test JiraClient.get_project."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001", "key": "TEST"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = JiraClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.get_project("TEST")

        assert result["key"] == "TEST"
        mock_client.get.assert_called_once()
        client.close()


def test_jira_client_get_project_not_found(mocker):
    """Test JiraClient.get_project returns None when 404."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = JiraClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.get_project("NONEXISTENT")
        assert result is None
        client.close()


def test_jira_client_create_custom_field(mocker):
    """Test JiraClient.create_custom_field."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "customfield_10001", "name": "Test Field"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = JiraClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.create_custom_field(
            name="Test Field", field_type="text", description="Test field"
        )

        assert result["name"] == "Test Field"
        mock_client.post.assert_called_once()
        client.close()


def test_jira_client_context_manager():
    """Test JiraClient as context manager."""
    client = JiraClient(
        base_url="https://test.atlassian.net",
        username="user@example.com",
        password="token123",
    )
    with client as c:
        assert c is client
        assert client.session is not None
    # After exiting context, close should have been called
    assert client.session is None or client.session.close


# ConfluenceClient tests
def test_confluence_client_initialization():
    """Test ConfluenceClient initialization."""
    client = ConfluenceClient(
        base_url="https://test.atlassian.net",
        username="user@example.com",
        password="token123",
        verify_ssl=True,
    )
    assert client.base_url == "https://test.atlassian.net"
    assert client.auth == ("user@example.com", "token123")
    assert client.verify_ssl is True
    assert client.session is None


def test_confluence_client_create_space(mocker):
    """Test ConfluenceClient.create_space."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001", "key": "DOC"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = ConfluenceClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.create_space(
            key="DOC", name="Documentation", description="Docs space"
        )

        assert result["key"] == "DOC"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/rest/api/2/space" in call_args[0][0]
        assert call_args[1]["json"]["key"] == "DOC"
        client.close()


def test_confluence_client_create_page(mocker):
    """Test ConfluenceClient.create_page."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "10001", "title": "Home"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = ConfluenceClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.create_page(
            space_key="DOC",
            title="Home",
            content="<h1>Welcome</h1>",
        )

        assert result["title"] == "Home"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/rest/api/2/content" in call_args[0][0]
        assert call_args[1]["json"]["type"] == "page"
        client.close()


def test_confluence_client_get_page_by_title(mocker):
    """Test ConfluenceClient.get_page_by_title."""
    mock_response = Mock()
    mock_response.json.return_value = {"results": [{"id": "10001", "title": "Home"}]}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = ConfluenceClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.get_page_by_title("DOC", "Home")

        assert result is not None
        assert result["title"] == "Home"
        mock_client.get.assert_called_once()
        client.close()


def test_confluence_client_get_page_by_title_not_found(mocker):
    """Test ConfluenceClient.get_page_by_title returns None when not found."""
    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = ConfluenceClient(
            base_url="https://test.atlassian.net",
            username="user@example.com",
            password="token123",
        )
        result = client.get_page_by_title("DOC", "Nonexistent")
        assert result is None
        client.close()
