"""GitHub REST API client for repos, issues, PRs, and workflows.

Usage::

    client = GitHubClient(token="ghp_...")
    repos = await client.list_repos()
    issue = await client.create_issue("owner/repo", "Bug title", body="Details")
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.github.com"


class GitHubClient:
    """Async GitHub REST API client."""

    def __init__(self, token: str) -> None:
        self.token = token
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def list_repos(
        self, *, sort: str = "updated", per_page: int = 30, page: int = 1
    ) -> list[dict[str, Any]]:
        """List repositories for the authenticated user."""
        logger.debug("Listing repos (page=%d)", page)
        resp = await self._client.get(
            "/user/repos", params={"sort": sort, "per_page": per_page, "page": page}
        )
        resp.raise_for_status()
        return resp.json()

    async def get_repo(self, full_name: str) -> dict[str, Any]:
        """Get a single repository by owner/name."""
        logger.debug("Fetching repo %s", full_name)
        resp = await self._client.get(f"/repos/{full_name}")
        resp.raise_for_status()
        return resp.json()

    async def create_issue(
        self, repo: str, title: str, *, body: str = "", labels: list[str] | None = None
    ) -> dict[str, Any]:
        """Create an issue on a repository (owner/repo)."""
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        logger.info("Creating issue '%s' on %s", title, repo)
        resp = await self._client.post(f"/repos/{repo}/issues", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def list_issues(
        self, repo: str, *, state: str = "open", per_page: int = 30, page: int = 1
    ) -> list[dict[str, Any]]:
        """List issues for a repository."""
        logger.debug("Listing issues for %s (state=%s)", repo, state)
        resp = await self._client.get(
            f"/repos/{repo}/issues",
            params={"state": state, "per_page": per_page, "page": page},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_pr(
        self,
        repo: str,
        title: str,
        head: str,
        base: str,
        *,
        body: str = "",
        draft: bool = False,
    ) -> dict[str, Any]:
        """Create a pull request."""
        logger.info("Creating PR '%s' on %s (%s -> %s)", title, repo, head, base)
        resp = await self._client.post(
            f"/repos/{repo}/pulls",
            json={"title": title, "head": head, "base": base, "body": body, "draft": draft},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_comment(
        self, repo: str, issue_number: int, body: str
    ) -> dict[str, Any]:
        """Add a comment to an issue or PR."""
        logger.info("Commenting on %s#%d", repo, issue_number)
        resp = await self._client.post(
            f"/repos/{repo}/issues/{issue_number}/comments", json={"body": body}
        )
        resp.raise_for_status()
        return resp.json()

    async def list_workflows(self, repo: str) -> list[dict[str, Any]]:
        """List GitHub Actions workflows for a repository."""
        logger.debug("Listing workflows for %s", repo)
        resp = await self._client.get(f"/repos/{repo}/actions/workflows")
        resp.raise_for_status()
        return resp.json().get("workflows", [])

    async def trigger_workflow(
        self, repo: str, workflow_id: str | int, ref: str = "main",
        *, inputs: dict[str, str] | None = None,
    ) -> int:
        """Trigger a workflow_dispatch event. Returns HTTP status code."""
        payload: dict[str, Any] = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs
        logger.info("Triggering workflow %s on %s (ref=%s)", workflow_id, repo, ref)
        resp = await self._client.post(
            f"/repos/{repo}/actions/workflows/{workflow_id}/dispatches",
            json=payload,
        )
        resp.raise_for_status()
        return resp.status_code

    async def search_code(
        self, query: str, *, per_page: int = 30, page: int = 1
    ) -> dict[str, Any]:
        """Search code across GitHub repositories."""
        logger.debug("Searching code: %s", query)
        resp = await self._client.get(
            "/search/code", params={"q": query, "per_page": per_page, "page": page}
        )
        resp.raise_for_status()
        return resp.json()
