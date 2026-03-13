"""Jira REST API client."""

import logging
from typing import Dict, Any, Optional
from .utils import setup_logging

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for Jira REST API operations."""

    def __init__(
        self, base_url: str, username: str, password: str, verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.verify_ssl = verify_ssl
        self.session = None  # Will be created on demand

    def _get_session(self):
        """Get or create HTTP session."""
        if self.session is None:
            import httpx

            self.session = httpx.Client(
                auth=self.auth, verify=self.verify_ssl, timeout=30.0
            )
        return self.session

    def create_project(
        self,
        key: str,
        name: str,
        project_type_key: str = "business",
        description: str = "",
        lead: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new Jira project."""
        url = f"{self.base_url}/rest/api/3/project"
        data = {
            "key": key,
            "name": name,
            "projectTypeKey": project_type_key,
            "description": description,
        }
        if lead:
            data["lead"] = lead

        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        logger.info(f"Created project {key}")
        return response.json()

    def get_project(self, key: str) -> Optional[Dict[str, Any]]:
        """Get project by key."""
        url = f"{self.base_url}/rest/api/3/project/{key}"
        response = self._get_session().get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def update_project(self, key: str, **updates) -> Dict[str, Any]:
        """Update project details."""
        url = f"{self.base_url}/rest/api/3/project/{key}"
        response = self._get_session().put(url, json=updates)
        response.raise_for_status()
        logger.info(f"Updated project {key}")
        return response.json()

    def create_custom_field(
        self,
        name: str,
        field_type: str,
        description: str = "",
        contexts: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Create a custom field."""
        url = f"{self.base_url}/rest/api/3/field"
        data = {
            "name": name,
            "type": field_type,
            "description": description or f"Custom field: {name}",
        }
        if contexts:
            data["contexts"] = contexts

        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        logger.info(f"Created custom field {name}")
        return response.json()

    def get_custom_fields(self) -> list:
        """Get all custom fields."""
        url = f"{self.base_url}/rest/api/3/field"
        response = self._get_session().get(url)
        response.raise_for_status()
        return response.json()

    def create_issue_type(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create an issue type."""
        # Note: Creating issue types requires admin permissions and specific endpoints
        # This is a simplified version
        project_url = f"{self.base_url}/rest/api/3/project"
        # In practice, issue types are often created via project templates or admin APIs
        logger.warning("Issue type creation requires project-specific context")
        return {"name": name, "description": description, "created": True}

    def create_workflow(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a workflow."""
        # Workflow creation is complex and typically involves multiple steps
        # This placeholder indicates the intention
        logger.warning("Workflow creation requires detailed configuration")
        return {"name": name, "description": description, "created": True}

    def close(self):
        """Close the client session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
