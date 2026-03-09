"""Full-text search client — Elasticsearch, OpenSearch, Meilisearch adapters.

Usage::

    client = SearchClient(provider="elasticsearch", hosts=["http://localhost:9200"])
    await client.index("products", "1", {"title": "Widget", "price": 9.99})
    results = await client.search("products", "widget")
    await client.close()
"""
from __future__ import annotations

import json as json_mod
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SearchClient:
    """Async unified full-text search client."""

    def __init__(
        self,
        provider: str = "elasticsearch",
        hosts: list[str] | None = None,
        api_key: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        self.provider = provider.lower()
        host = (hosts or ["http://localhost:9200"])[0]
        headers: dict[str, str] = {"Content-Type": "application/json"}
        auth = None
        if api_key:
            if self.provider == "meilisearch":
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                headers["Authorization"] = f"ApiKey {api_key}"
        elif username and password:
            auth = (username, password)
        self._client = httpx.AsyncClient(base_url=host, headers=headers, auth=auth, timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def create_index(self, index: str, mappings: dict[str, Any] | None = None, settings: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a search index."""
        if self.provider in ("elasticsearch", "opensearch"):
            body: dict[str, Any] = {}
            if mappings:
                body["mappings"] = mappings
            if settings:
                body["settings"] = settings
            resp = await self._client.put(f"/{index}", json=body)
        elif self.provider == "meilisearch":
            resp = await self._client.post("/indexes", json={"uid": index, "primaryKey": "id"})
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
        resp.raise_for_status()
        logger.info("Created search index '%s' on %s", index, self.provider)
        return resp.json()

    async def delete_index(self, index: str) -> int:
        """Delete a search index."""
        if self.provider in ("elasticsearch", "opensearch"):
            resp = await self._client.delete(f"/{index}")
        elif self.provider == "meilisearch":
            resp = await self._client.delete(f"/indexes/{index}")
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
        resp.raise_for_status()
        return resp.status_code

    async def index_document(self, index: str, doc_id: str, document: dict[str, Any]) -> dict[str, Any]:
        """Index a single document."""
        if self.provider in ("elasticsearch", "opensearch"):
            resp = await self._client.put(f"/{index}/_doc/{doc_id}", json=document)
        elif self.provider == "meilisearch":
            document["id"] = doc_id
            resp = await self._client.post(f"/indexes/{index}/documents", json=[document])
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
        resp.raise_for_status()
        logger.debug("Indexed document %s in %s/%s", doc_id, self.provider, index)
        return resp.json()

    async def bulk_index(self, index: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Bulk index documents."""
        if self.provider in ("elasticsearch", "opensearch"):
            lines = []
            for doc in documents:
                doc_copy = dict(doc)
                doc_id = doc_copy.pop("id", None) or doc_copy.pop("_id", None)
                action: dict[str, Any] = {"index": {"_index": index}}
                if doc_id:
                    action["index"]["_id"] = doc_id
                lines.append(json_mod.dumps(action))
                lines.append(json_mod.dumps(doc_copy))
            body = "\n".join(lines) + "\n"
            resp = await self._client.post("/_bulk", content=body, headers={"Content-Type": "application/x-ndjson"})
        elif self.provider == "meilisearch":
            resp = await self._client.post(f"/indexes/{index}/documents", json=documents)
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
        resp.raise_for_status()
        logger.info("Bulk indexed %d documents in %s/%s", len(documents), self.provider, index)
        return resp.json()

    async def search(self, index: str, query: str, *, size: int = 10, filters: dict[str, Any] | None = None, fields: list[str] | None = None) -> dict[str, Any]:
        """Full-text search across an index."""
        if self.provider in ("elasticsearch", "opensearch"):
            body: dict[str, Any] = {"query": {"bool": {"must": [{"multi_match": {"query": query, "fields": fields or ["*"]}}]}}, "size": size}
            if filters:
                body["query"]["bool"]["filter"] = [{"term": {k: v}} for k, v in filters.items()]
            resp = await self._client.post(f"/{index}/_search", json=body)
            resp.raise_for_status()
            data = resp.json()
            return {"total": data.get("hits", {}).get("total", {}).get("value", 0), "hits": [{"id": h["_id"], "score": h["_score"], "source": h["_source"]} for h in data.get("hits", {}).get("hits", [])]}
        elif self.provider == "meilisearch":
            body = {"q": query, "limit": size}
            if filters:
                filter_strs = [f"{k} = '{v}'" for k, v in filters.items()]
                body["filter"] = " AND ".join(filter_strs)
            if fields:
                body["attributesToRetrieve"] = fields
            resp = await self._client.post(f"/indexes/{index}/search", json=body)
            resp.raise_for_status()
            data = resp.json()
            return {"total": data.get("estimatedTotalHits", 0), "hits": [{"id": h.get("id"), "score": 1.0, "source": h} for h in data.get("hits", [])]}
        raise ValueError(f"Unsupported search provider: {self.provider}")

    async def get_document(self, index: str, doc_id: str) -> dict[str, Any]:
        """Get a document by ID."""
        if self.provider in ("elasticsearch", "opensearch"):
            resp = await self._client.get(f"/{index}/_doc/{doc_id}")
        elif self.provider == "meilisearch":
            resp = await self._client.get(f"/indexes/{index}/documents/{doc_id}")
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
        resp.raise_for_status()
        return resp.json()

    async def delete_document(self, index: str, doc_id: str) -> int:
        """Delete a document by ID."""
        if self.provider in ("elasticsearch", "opensearch"):
            resp = await self._client.delete(f"/{index}/_doc/{doc_id}")
        elif self.provider == "meilisearch":
            resp = await self._client.delete(f"/indexes/{index}/documents/{doc_id}")
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
        resp.raise_for_status()
        return resp.status_code

    async def count(self, index: str) -> int:
        """Count documents in an index."""
        if self.provider in ("elasticsearch", "opensearch"):
            resp = await self._client.get(f"/{index}/_count")
            resp.raise_for_status()
            return resp.json().get("count", 0)
        elif self.provider == "meilisearch":
            resp = await self._client.get(f"/indexes/{index}/stats")
            resp.raise_for_status()
            return resp.json().get("numberOfDocuments", 0)
        return 0
