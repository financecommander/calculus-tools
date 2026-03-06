"""Registry store — PostgreSQL-backed API catalog.

Provides CRUD operations against the ``api_registry`` table.  Falls back
to an in-memory list when no ``DATABASE_URL`` is configured, so the
library remains usable without a running database (e.g. in tests or
local dev).

Usage::

    from calculus_tools.registry import RegistryStore

    store = RegistryStore()              # uses DATABASE_URL env var
    await store.connect()
    apis = await store.list_apis()
    await store.close()
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from calculus_tools.registry.models import ApiEntry, AuthType, ApiCategory

logger = logging.getLogger(__name__)

# ── SQL DDL ────────────────────────────────────────────────────

CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS api_registry (
    api_id       SERIAL PRIMARY KEY,
    name         VARCHAR(120) NOT NULL UNIQUE,
    base_url     TEXT NOT NULL,
    auth_type    VARCHAR(20) NOT NULL DEFAULT 'none',
    rate_limit   VARCHAR(100),
    cost_per_call NUMERIC(10, 6) NOT NULL DEFAULT 0,
    category     VARCHAR(40) NOT NULL DEFAULT 'other',
    notes        VARCHAR(500) DEFAULT '',
    enabled      BOOLEAN NOT NULL DEFAULT TRUE
);
"""

# ── Store ──────────────────────────────────────────────────────


class RegistryStore:
    """Async API registry backed by PostgreSQL (or in-memory fallback)."""

    def __init__(self, database_url: Optional[str] = None):
        self._dsn = database_url or os.getenv("DATABASE_URL")
        self._pool = None
        self._memory: list[ApiEntry] = []  # fallback

    # ── lifecycle ──────────────────────────────────────────

    async def connect(self) -> None:
        """Establish a connection pool and ensure the table exists."""
        if not self._dsn:
            logger.info("No DATABASE_URL — using in-memory registry")
            return
        try:
            import asyncpg  # optional dep

            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
            async with self._pool.acquire() as conn:
                await conn.execute(CREATE_TABLE_SQL)
            logger.info("Connected to registry DB")
        except Exception as exc:
            logger.warning("DB connect failed (%s) — falling back to memory", exc)
            self._pool = None

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    # ── CRUD ──────────────────────────────────────────────

    async def upsert(self, entry: ApiEntry) -> ApiEntry:
        """Insert or update (by name) a single API entry."""
        if self._pool:
            row = await self._pool.fetchrow(
                """
                INSERT INTO api_registry (name, base_url, auth_type, rate_limit,
                                          cost_per_call, category, notes, enabled)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (name) DO UPDATE SET
                    base_url      = EXCLUDED.base_url,
                    auth_type     = EXCLUDED.auth_type,
                    rate_limit    = EXCLUDED.rate_limit,
                    cost_per_call = EXCLUDED.cost_per_call,
                    category      = EXCLUDED.category,
                    notes         = EXCLUDED.notes,
                    enabled       = EXCLUDED.enabled
                RETURNING api_id
                """,
                entry.name,
                entry.base_url,
                entry.auth_type.value,
                entry.rate_limit,
                entry.cost_per_call,
                entry.category.value,
                entry.notes,
                entry.enabled,
            )
            entry.api_id = row["api_id"]
        else:
            existing = next((a for a in self._memory if a.name == entry.name), None)
            if existing:
                idx = self._memory.index(existing)
                entry.api_id = existing.api_id
                self._memory[idx] = entry
            else:
                entry.api_id = len(self._memory) + 1
                self._memory.append(entry)
        return entry

    async def bulk_upsert(self, entries: list[ApiEntry]) -> int:
        """Upsert many entries. Returns count of rows affected."""
        count = 0
        for e in entries:
            await self.upsert(e)
            count += 1
        return count

    async def get(self, name: str) -> Optional[ApiEntry]:
        if self._pool:
            row = await self._pool.fetchrow(
                "SELECT * FROM api_registry WHERE name = $1", name
            )
            return self._row_to_entry(row) if row else None
        return next((a for a in self._memory if a.name == name), None)

    async def list_apis(
        self,
        category: Optional[ApiCategory] = None,
        enabled_only: bool = True,
    ) -> list[ApiEntry]:
        """Return all APIs, optionally filtered."""
        if self._pool:
            clauses, params = ["1=1"], []
            if enabled_only:
                clauses.append("enabled = TRUE")
            if category:
                clauses.append(f"category = ${len(params) + 1}")
                params.append(category.value)
            sql = f"SELECT * FROM api_registry WHERE {' AND '.join(clauses)} ORDER BY api_id"
            rows = await self._pool.fetch(sql, *params)
            return [self._row_to_entry(r) for r in rows]
        out = self._memory
        if enabled_only:
            out = [a for a in out if a.enabled]
        if category:
            out = [a for a in out if a.category == category]
        return out

    async def delete(self, name: str) -> bool:
        if self._pool:
            tag = await self._pool.execute(
                "DELETE FROM api_registry WHERE name = $1", name
            )
            return tag.endswith("1")
        before = len(self._memory)
        self._memory = [a for a in self._memory if a.name != name]
        return len(self._memory) < before

    # ── import helpers ────────────────────────────────────

    async def import_json(self, path: str | Path) -> int:
        """Bulk-import from a JSON file (list of objects)."""
        data = json.loads(Path(path).read_text())
        entries = [ApiEntry(**item) for item in data]
        return await self.bulk_upsert(entries)

    async def import_csv(self, path: str | Path) -> int:
        """Bulk-import from a CSV file."""
        import csv

        rows: list[ApiEntry] = []
        with open(path, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append(
                    ApiEntry(
                        name=row["name"],
                        base_url=row["base_url"],
                        auth_type=AuthType(row.get("auth_type", "none")),
                        rate_limit=row.get("rate_limit") or None,
                        cost_per_call=float(row.get("cost_per_call", 0)),
                        category=ApiCategory(row.get("category", "other")),
                        notes=row.get("notes", ""),
                        enabled=row.get("enabled", "true").lower() in ("true", "1", "yes"),
                    )
                )
        return await self.bulk_upsert(rows)

    # ── internal ──────────────────────────────────────────

    @staticmethod
    def _row_to_entry(row) -> ApiEntry:
        return ApiEntry(
            api_id=row["api_id"],
            name=row["name"],
            base_url=row["base_url"],
            auth_type=AuthType(row["auth_type"]),
            rate_limit=row["rate_limit"],
            cost_per_call=float(row["cost_per_call"]),
            category=ApiCategory(row["category"]),
            notes=row["notes"] or "",
            enabled=row["enabled"],
        )
