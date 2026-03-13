"""Confluence REST API client."""

import logging
from typing import Dict, Any, Optional
from .utils import setup_logging

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for Confluence REST API operations."""

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

    def create_space(
        self,
        key: str,
        name: str,
        description: str = "",
        permissions: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Create a new Confluence space."""
        url = f"{self.base_url}/rest/api/2/space"
        data = {
            "key": key,
            "name": name,
            "description": {"plain": {"value": description}},
        }
        if permissions:
            data["permissions"] = permissions

        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        logger.info(f"Created space {key}")
        return response.json()

    def get_space(self, key: str) -> Optional[Dict[str, Any]]:
        """Get space by key."""
        url = f"{self.base_url}/rest/api/2/space/{key}"
        response = self._get_session().get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def update_space(self, key: str, **updates) -> Dict[str, Any]:
        """Update space details."""
        url = f"{self.base_url}/rest/api/2/space/{key}"
        response = self._get_session().put(url, json=updates)
        response.raise_for_status()
        logger.info(f"Updated space {key}")
        return response.json()

    def delete_space(self, key: str) -> Dict[str, Any]:
        """Delete a space."""
        url = f"{self.base_url}/rest/api/2/space/{key}"
        response = self._get_session().delete(url)
        response.raise_for_status()
        logger.info(f"Deleted space {key}")
        return response.json()

    def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new page in a space."""
        url = f"{self.base_url}/rest/api/2/content"
        data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {"storage": {"value": content, "representation": "storage"}},
        }
        if parent_id:
            data["ancestors"] = [{"id": parent_id}]

        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        logger.info(f"Created page '{title}' in space {space_key}")
        return response.json()

    def update_page(
        self, page_id: str, title: str, content: str, version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing page."""
        url = f"{self.base_url}/rest/api/2/content/{page_id}"
        data = {
            "id": page_id,
            "type": "page",
            "title": title,
            "body": {"storage": {"value": content, "representation": "storage"}},
        }
        if version is not None:
            data["version"] = {"number": version}

        response = self._get_session().put(url, json=data)
        response.raise_for_status()
        logger.info(f"Updated page {page_id}")
        return response.json()

    def delete_page(self, page_id: str) -> Dict[str, Any]:
        """Delete a page."""
        url = f"{self.base_url}/rest/api/2/content/{page_id}"
        response = self._get_session().delete(url)
        response.raise_for_status()
        logger.info(f"Deleted page {page_id}")
        return response.json()

    def get_page_by_title(self, space_key: str, title: str) -> Optional[Dict[str, Any]]:
        """Get page by title in a space."""
        url = f"{self.base_url}/rest/api/2/content"
        params = {
            "spaceKey": space_key,
            "title": title,
            "type": "page",
        }
        response = self._get_session().get(url, params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        results = response.json().get("results", [])
        return results[0] if results else None

    def create_template(
        self,
        name: str,
        space_key: str,
        content: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a page template."""
        url = f"{self.base_url}/rest/api/2/template"
        data = {
            "name": name,
            "space": {"key": space_key},
            "templateType": "page",
            "body": {"storage": {"value": content, "representation": "storage"}},
        }
        if description:
            data["description"] = description

        response = self._get_session().post(url, json=data)
        response.raise_for_status()
        logger.info(f"Created template {name}")
        return response.json()

    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """Delete a template."""
        url = f"{self.base_url}/rest/api/2/template/{template_id}"
        response = self._get_session().delete(url)
        response.raise_for_status()
        logger.info(f"Deleted template {template_id}")
        return response.json()

    def close(self):
        """Close the client session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        self._get_session()  # Create session on enter
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
