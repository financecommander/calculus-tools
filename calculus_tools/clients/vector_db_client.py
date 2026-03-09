"""Unified vector database client — Pinecone, ChromaDB, Qdrant, Weaviate adapters.

Usage::

    client = VectorDBClient(provider="pinecone", api_key="...", environment="us-east-1")
    await client.upsert("my-index", vectors=[{"id": "1", "values": [...], "metadata": {...}}])
    results = await client.query("my-index", vector=[...], top_k=10)
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class VectorDBClient:
    """Async unified vector database client."""

    def __init__(
        self,
        provider: str = "pinecone",
        api_key: str = "",
        environment: str = "",
        host: str = "",
    ) -> None:
        self.provider = provider.lower()
        self.api_key = api_key
        self.environment = environment
        self.host = host
        self._client: httpx.AsyncClient | None = None
        self._setup_client()

    def _setup_client(self):
        if self.provider == "pinecone":
            base_url = self.host or f"https://controller.{self.environment}.pinecone.io"
            headers = {"Api-Key": self.api_key, "Content-Type": "application/json"}
        elif self.provider == "qdrant":
            base_url = self.host or "http://localhost:6333"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["api-key"] = self.api_key
        elif self.provider == "weaviate":
            base_url = self.host or "http://localhost:8080"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "chromadb":
            base_url = self.host or "http://localhost:8000"
            headers = {"Content-Type": "application/json"}
        else:
            base_url = self.host or "http://localhost:8000"
            headers = {"Content-Type": "application/json"}
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    # ── Index / Collection Management ──────────────────────────

    async def create_index(self, name: str, dimension: int, metric: str = "cosine", **kwargs: Any) -> dict[str, Any]:
        """Create a vector index/collection."""
        if self.provider == "pinecone":
            resp = await self._client.post("/databases", json={"name": name, "dimension": dimension, "metric": metric, **kwargs})
        elif self.provider == "qdrant":
            resp = await self._client.put(f"/collections/{name}", json={"vectors": {"size": dimension, "distance": {"cosine": "Cosine", "euclidean": "Euclid", "dot": "Dot"}.get(metric, "Cosine")}})
        elif self.provider == "weaviate":
            resp = await self._client.post("/v1/schema", json={"class": name, "vectorizer": "none", **kwargs})
        elif self.provider == "chromadb":
            resp = await self._client.post("/api/v1/collections", json={"name": name, "metadata": {"hnsw:space": metric}})
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        resp.raise_for_status()
        logger.info("Created index '%s' (dim=%d, metric=%s) on %s", name, dimension, metric, self.provider)
        return resp.json()

    async def delete_index(self, name: str) -> int:
        """Delete a vector index/collection. Returns status code."""
        if self.provider == "pinecone":
            resp = await self._client.delete(f"/databases/{name}")
        elif self.provider == "qdrant":
            resp = await self._client.delete(f"/collections/{name}")
        elif self.provider == "weaviate":
            resp = await self._client.delete(f"/v1/schema/{name}")
        elif self.provider == "chromadb":
            resp = await self._client.delete(f"/api/v1/collections/{name}")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        resp.raise_for_status()
        logger.info("Deleted index '%s' on %s", name, self.provider)
        return resp.status_code

    async def list_indexes(self) -> list[dict[str, Any]]:
        """List all indexes/collections."""
        if self.provider == "pinecone":
            resp = await self._client.get("/databases")
        elif self.provider == "qdrant":
            resp = await self._client.get("/collections")
        elif self.provider == "weaviate":
            resp = await self._client.get("/v1/schema")
        elif self.provider == "chromadb":
            resp = await self._client.get("/api/v1/collections")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("result", data.get("collections", data.get("classes", [])))

    # ── Vector Operations ──────────────────────────────────────

    async def upsert(self, index: str, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        """Upsert vectors. Each vector: {"id": str, "values": list[float], "metadata": dict}."""
        if self.provider == "pinecone":
            resp = await self._client.post("/vectors/upsert", json={"vectors": vectors, "namespace": ""})
        elif self.provider == "qdrant":
            points = [{"id": v.get("id", str(i)), "vector": v["values"], "payload": v.get("metadata", {})} for i, v in enumerate(vectors)]
            resp = await self._client.put(f"/collections/{index}/points", json={"points": points})
        elif self.provider == "weaviate":
            objects = [{"class": index, "vector": v["values"], "properties": v.get("metadata", {}), "id": v.get("id")} for v in vectors]
            resp = await self._client.post("/v1/batch/objects", json={"objects": objects})
        elif self.provider == "chromadb":
            ids = [v.get("id", str(i)) for i, v in enumerate(vectors)]
            embeddings = [v["values"] for v in vectors]
            metadatas = [v.get("metadata", {}) for v in vectors]
            resp = await self._client.post(f"/api/v1/collections/{index}/upsert", json={"ids": ids, "embeddings": embeddings, "metadatas": metadatas})
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        resp.raise_for_status()
        logger.debug("Upserted %d vectors to %s/%s", len(vectors), self.provider, index)
        return resp.json()

    async def query(self, index: str, vector: list[float], top_k: int = 10, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Query nearest neighbors. Returns list of {id, score, metadata}."""
        if self.provider == "pinecone":
            payload: dict[str, Any] = {"vector": vector, "topK": top_k, "includeMetadata": True}
            if filter:
                payload["filter"] = filter
            resp = await self._client.post("/query", json=payload)
            resp.raise_for_status()
            return resp.json().get("matches", [])
        elif self.provider == "qdrant":
            payload = {"vector": vector, "limit": top_k, "with_payload": True}
            if filter:
                payload["filter"] = filter
            resp = await self._client.post(f"/collections/{index}/points/search", json=payload)
            resp.raise_for_status()
            return [{"id": r["id"], "score": r["score"], "metadata": r.get("payload", {})} for r in resp.json().get("result", [])]
        elif self.provider == "weaviate":
            # GraphQL query
            gql = {"query": f'{{ Get {{ {index}(nearVector: {{vector: {vector}, certainty: 0.7}} limit: {top_k}) {{ _additional {{ id distance }} }} }} }}'}
            resp = await self._client.post("/v1/graphql", json=gql)
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("Get", {}).get(index, [])
            return [{"id": r.get("_additional", {}).get("id"), "score": 1.0 - r.get("_additional", {}).get("distance", 0), "metadata": {k: v for k, v in r.items() if k != "_additional"}} for r in data]
        elif self.provider == "chromadb":
            payload = {"query_embeddings": [vector], "n_results": top_k}
            if filter:
                payload["where"] = filter
            resp = await self._client.post(f"/api/v1/collections/{index}/query", json=payload)
            resp.raise_for_status()
            result = resp.json()
            ids = result.get("ids", [[]])[0]
            distances = result.get("distances", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            return [{"id": ids[i], "score": 1.0 / (1.0 + distances[i]), "metadata": metadatas[i] if i < len(metadatas) else {}} for i in range(len(ids))]
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def delete_vectors(self, index: str, ids: list[str]) -> int:
        """Delete vectors by ID. Returns status code."""
        if self.provider == "pinecone":
            resp = await self._client.post("/vectors/delete", json={"ids": ids})
        elif self.provider == "qdrant":
            resp = await self._client.post(f"/collections/{index}/points/delete", json={"points": ids})
        elif self.provider == "weaviate":
            for vid in ids:
                resp = await self._client.delete(f"/v1/objects/{index}/{vid}")
            return 200
        elif self.provider == "chromadb":
            resp = await self._client.post(f"/api/v1/collections/{index}/delete", json={"ids": ids})
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        resp.raise_for_status()
        logger.debug("Deleted %d vectors from %s/%s", len(ids), self.provider, index)
        return resp.status_code

    async def get_index_stats(self, index: str) -> dict[str, Any]:
        """Get index statistics (vector count, dimension, etc.)."""
        if self.provider == "pinecone":
            resp = await self._client.post("/describe_index_stats", json={})
        elif self.provider == "qdrant":
            resp = await self._client.get(f"/collections/{index}")
        elif self.provider == "weaviate":
            resp = await self._client.get(f"/v1/schema/{index}")
        elif self.provider == "chromadb":
            resp = await self._client.get(f"/api/v1/collections/{index}")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        resp.raise_for_status()
        return resp.json()
