"""Secrets manager client — HashiCorp Vault, AWS Secrets Manager unified adapter.

Usage::

    client = VaultClient(provider="vault", address="https://vault.example.com", token="hvs....")
    secret = await client.get_secret("database/creds/mydb")
    await client.put_secret("app/config", {"api_key": "xxx"})
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class VaultClient:
    """Async secrets manager client supporting Vault and AWS Secrets Manager."""

    def __init__(
        self,
        provider: str = "vault",
        address: str = "",
        token: str = "",
        region: str = "us-east-1",
        aws_access_key: str = "",
        aws_secret_key: str = "",
    ) -> None:
        self.provider = provider.lower()
        self.address = address or "http://127.0.0.1:8200"
        self.token = token
        self.region = region
        if self.provider == "vault":
            self._client = httpx.AsyncClient(
                base_url=self.address,
                headers={"X-Vault-Token": token, "Content-Type": "application/json"},
                timeout=15.0,
            )
        elif self.provider == "aws":
            self._client = httpx.AsyncClient(
                base_url=f"https://secretsmanager.{region}.amazonaws.com",
                timeout=15.0,
            )
            self._aws_access_key = aws_access_key
            self._aws_secret_key = aws_secret_key
        else:
            raise ValueError(f"Unsupported secrets provider: {provider}")

    async def close(self) -> None:
        await self._client.aclose()

    # ── Vault (HashiCorp) ──────────────────────────────────────

    async def get_secret(self, path: str, mount: str = "secret") -> dict[str, Any]:
        """Retrieve a secret by path."""
        if self.provider == "vault":
            resp = await self._client.get(f"/v1/{mount}/data/{path}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("data", {})
        elif self.provider == "aws":
            return await self._aws_get_secret(path)
        return {}

    async def put_secret(self, path: str, data: dict[str, Any], mount: str = "secret") -> dict[str, Any]:
        """Write a secret."""
        if self.provider == "vault":
            resp = await self._client.post(f"/v1/{mount}/data/{path}", json={"data": data})
            resp.raise_for_status()
            logger.info("Wrote secret to vault: %s/%s", mount, path)
            return resp.json()
        elif self.provider == "aws":
            return await self._aws_put_secret(path, data)
        return {}

    async def delete_secret(self, path: str, mount: str = "secret") -> int:
        """Delete a secret. Returns status code."""
        if self.provider == "vault":
            resp = await self._client.delete(f"/v1/{mount}/data/{path}")
            resp.raise_for_status()
            logger.info("Deleted secret from vault: %s/%s", mount, path)
            return resp.status_code
        elif self.provider == "aws":
            return await self._aws_delete_secret(path)
        return 404

    async def list_secrets(self, path: str = "", mount: str = "secret") -> list[str]:
        """List secret keys at a path."""
        if self.provider == "vault":
            resp = await self._client.request("LIST", f"/v1/{mount}/metadata/{path}")
            resp.raise_for_status()
            return resp.json().get("data", {}).get("keys", [])
        elif self.provider == "aws":
            return await self._aws_list_secrets()
        return []

    async def get_secret_metadata(self, path: str, mount: str = "secret") -> dict[str, Any]:
        """Get metadata for a secret (versions, creation time, etc.)."""
        if self.provider == "vault":
            resp = await self._client.get(f"/v1/{mount}/metadata/{path}")
            resp.raise_for_status()
            return resp.json().get("data", {})
        return {}

    async def enable_engine(self, path: str, engine_type: str = "kv", options: dict[str, Any] | None = None) -> int:
        """Enable a new secrets engine (Vault only)."""
        if self.provider != "vault":
            raise NotImplementedError("enable_engine is Vault-only")
        payload: dict[str, Any] = {"type": engine_type}
        if options:
            payload["options"] = options
        resp = await self._client.post(f"/v1/sys/mounts/{path}", json=payload)
        resp.raise_for_status()
        logger.info("Enabled secrets engine '%s' at %s", engine_type, path)
        return resp.status_code

    async def health(self) -> dict[str, Any]:
        """Check Vault health status."""
        if self.provider == "vault":
            resp = await self._client.get("/v1/sys/health")
            return resp.json()
        return {"status": "unknown", "provider": self.provider}

    # ── AWS Secrets Manager ─────────────────────────────────────

    async def _aws_get_secret(self, secret_id: str) -> dict[str, Any]:
        import json as json_mod
        headers = self._aws_sign_headers("GetSecretValue", {"SecretId": secret_id})
        resp = await self._client.post("/", headers=headers, json={"SecretId": secret_id})
        resp.raise_for_status()
        data = resp.json()
        secret_string = data.get("SecretString", "{}")
        try:
            return json_mod.loads(secret_string)
        except (json_mod.JSONDecodeError, TypeError):
            return {"value": secret_string}

    async def _aws_put_secret(self, secret_id: str, data: dict[str, Any]) -> dict[str, Any]:
        import json as json_mod
        payload = {"SecretId": secret_id, "SecretString": json_mod.dumps(data)}
        headers = self._aws_sign_headers("PutSecretValue", payload)
        resp = await self._client.post("/", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def _aws_delete_secret(self, secret_id: str) -> int:
        headers = self._aws_sign_headers("DeleteSecret", {"SecretId": secret_id})
        resp = await self._client.post("/", headers=headers, json={"SecretId": secret_id})
        resp.raise_for_status()
        return resp.status_code

    async def _aws_list_secrets(self) -> list[str]:
        headers = self._aws_sign_headers("ListSecrets", {})
        resp = await self._client.post("/", headers=headers, json={})
        resp.raise_for_status()
        return [s["Name"] for s in resp.json().get("SecretList", [])]

    def _aws_sign_headers(self, action: str, payload: dict) -> dict[str, str]:
        """Generate AWS SigV4 headers (simplified — use boto3 for production)."""
        import datetime
        now = datetime.datetime.utcnow()
        amzdate = now.strftime("%Y%m%dT%H%M%SZ")
        return {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": f"secretsmanager.{action}",
            "X-Amz-Date": amzdate,
            "Host": f"secretsmanager.{self.region}.amazonaws.com",
        }
