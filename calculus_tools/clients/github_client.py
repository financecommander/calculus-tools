"""GitHub client — issues, PRs, repos, and actions via GitHub REST API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.github.com"


class GitHubClient:
    """Async GitHub REST API client.

    Usage::

        async with GitHubClient(token="ghp_...") as gh:
            repos = await gh.list_repos("financecommander")
            issue = await gh.create_issue("financecommander/super-duper-spork",
                                          "Bug: widget broken", body="Details...")
    """

    def __init__(self, token: str, *, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def list_repos(self, owner: str, *, per_page: int = 30) -> List[Dict[str, Any]]:
        """List repositories for a user or org."""
        resp = await self._client.get(f"/users/{owner}/repos", params={"per_page": per_page, "sort": "updated"})
        resp.raise_for_status()
        return resp.json()

    async def create_issue(self, repo: str, title: str, *, body: str = "",
                           labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create an issue. repo format: 'owner/repo'."""
        payload: Dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        resp = await self._client.post(f"/repos/{repo}/issues", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def create_pr(self, repo: str, title: str, head: str, base: str = "main",
                        *, body: str = "", draft: bool = False) -> Dict[str, Any]:
        """Create a pull request."""
        payload = {"title": title, "head": head, "base": base, "body": body, "draft": draft}
        resp = await self._client.post(f"/repos/{repo}/pulls", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_repo(self, repo: str) -> Dict[str, Any]:
        """Get repository info."""
        resp = await self._client.get(f"/repos/{repo}")
        resp.raise_for_status()
        return resp.json()

    async def list_issues(self, repo: str, *, state: str = "open", per_page: int = 20) -> List[Dict[str, Any]]:
        """List issues on a repository."""
        resp = await self._client.get(f"/repos/{repo}/issues", params={"state": state, "per_page": per_page})
        resp.raise_for_status()
        return resp.json()

    async def list_prs(self, repo: str, *, state: str = "open") -> List[Dict[str, Any]]:
        """List pull requests."""
        resp = await self._client.get(f"/repos/{repo}/pulls", params={"state": state})
        resp.raise_for_status()
        return resp.json()

    async def get_commit(self, repo: str, sha: str) -> Dict[str, Any]:
        """Get a specific commit."""
        resp = await self._client.get(f"/repos/{repo}/commits/{sha}")
        resp.raise_for_status()
        return resp.json()

    async def dispatch_workflow(self, repo: str, workflow_id: str, ref: str = "main",
                                inputs: Optional[Dict[str, str]] = None) -> None:
        """Trigger a GitHub Actions workflow dispatch."""
        payload: Dict[str, Any] = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs
        resp = await self._client.post(f"/repos/{repo}/actions/workflows/{workflow_id}/dispatches", json=payload)
        resp.raise_for_status()

    async def create_comment(self, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        """Add a comment to an issue or PR."""
        resp = await self._client.post(f"/repos/{repo}/issues/{issue_number}/comments", json={"body": body})
        resp.raise_for_status()
        return resp.json()
