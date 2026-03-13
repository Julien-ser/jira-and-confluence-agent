"""Jira REST API client."""

import logging
from typing import Dict, Any, Optional, List
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
        contexts: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a custom field."""
        url = f"{self.base_url}/rest/api/3/field"
        data: Dict[str, Any] = {
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

    def create_issue_type(
        self,
        name: str,
        description: str = "",
        issue_type: str = "standard",
        project_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an issue type."""
        url = f"{self.base_url}/rest/api/3/issuetype"
        data: Dict[str, Any] = {
            "name": name,
            "description": description,
            "type": issue_type,
        }
        if project_keys:
            data["projectKeys"] = project_keys

        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        logger.info(f"Created issue type {name}")
        return response.json()

    def create_workflow(
        self,
        name: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a workflow with optional status steps."""
        # Create initial workflow draft
        url = f"{self.base_url}/rest/api/3/workflow"
        data: Dict[str, Any] = {"name": name, "description": description}
        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        workflow = response.json()
        workflow_id = workflow.get("id")
        logger.info(f"Created workflow draft {name} (ID: {workflow_id})")

        # Add statuses if steps provided
        if steps and workflow_id:
            for step in steps:
                step_name = step.get("name", "")
                status = step.get("status", "")
                if step_name and status:
                    status_url = (
                        f"{self.base_url}/rest/api/3/workflow/{workflow_id}/status"
                    )
                    status_data: Dict[str, Any] = {"name": status}
                    # Add additional properties if provided
                    if "properties" in step:
                        status_data["properties"] = step["properties"]

                    status_response = self._get_session().post(
                        status_url, json=status_data
                    )
                    if status_response.status_code < 300:
                        logger.info(f"Added status '{status}' to workflow {name}")
                    else:
                        logger.warning(
                            f"Failed to add status '{status}': {status_response.text}"
                        )

            # Publish the workflow
            publish_url = f"{self.base_url}/rest/api/3/workflow/{workflow_id}/publish"
            publish_response = self._get_session().post(publish_url, json={})
            if publish_response.status_code < 300:
                logger.info(f"Published workflow {name}")
                workflow = publish_response.json()
            else:
                logger.warning(
                    f"Failed to publish workflow {name}: {publish_response.text}"
                )

        return workflow

    def close(self):
        """Close the client session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
