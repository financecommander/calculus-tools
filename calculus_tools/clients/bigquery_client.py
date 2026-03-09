"""Cloud data warehouse client — BigQuery, Snowflake, Redshift adapters.

Usage::

    client = BigQueryClient(provider="bigquery", project_id="my-project", credentials_json="...")
    result = await client.query("SELECT * FROM dataset.table LIMIT 10")
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Async cloud data warehouse client supporting BigQuery, Snowflake, Redshift."""

    def __init__(
        self,
        provider: str = "bigquery",
        project_id: str = "",
        credentials_json: str = "",
        account: str = "",
        warehouse: str = "",
        database: str = "",
        schema: str = "public",
        host: str = "",
        api_key: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        self.provider = provider.lower()
        self.project_id = project_id
        self.database = database
        self.schema = schema
        if self.provider == "bigquery":
            self._client = httpx.AsyncClient(
                base_url="https://bigquery.googleapis.com/bigquery/v2",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=120.0,
            )
        elif self.provider == "snowflake":
            base = host or f"https://{account}.snowflakecomputing.com"
            self._client = httpx.AsyncClient(
                base_url=base,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                timeout=120.0,
            )
            self._warehouse = warehouse
        elif self.provider == "redshift":
            self._client = httpx.AsyncClient(
                base_url=host or "https://redshift-data.us-east-1.amazonaws.com",
                timeout=120.0,
            )
            self._cluster_id = account
        else:
            raise ValueError(f"Unsupported warehouse provider: {provider}")

    async def close(self) -> None:
        await self._client.aclose()

    async def query(self, sql: str, params: list[Any] | None = None, max_results: int = 10000) -> dict[str, Any]:
        """Execute a SQL query and return results."""
        logger.info("Executing query on %s: %.80s...", self.provider, sql)
        if self.provider == "bigquery":
            return await self._bq_query(sql, max_results)
        elif self.provider == "snowflake":
            return await self._sf_query(sql)
        elif self.provider == "redshift":
            return await self._rs_query(sql)
        return {"rows": [], "schema": []}

    async def list_datasets(self) -> list[dict[str, Any]]:
        """List datasets/databases."""
        if self.provider == "bigquery":
            resp = await self._client.get(f"/projects/{self.project_id}/datasets")
            resp.raise_for_status()
            return resp.json().get("datasets", [])
        elif self.provider == "snowflake":
            return (await self._sf_query("SHOW DATABASES")).get("rows", [])
        return []

    async def list_tables(self, dataset: str = "") -> list[dict[str, Any]]:
        """List tables in a dataset/schema."""
        if self.provider == "bigquery":
            ds = dataset or "default"
            resp = await self._client.get(f"/projects/{self.project_id}/datasets/{ds}/tables")
            resp.raise_for_status()
            return resp.json().get("tables", [])
        elif self.provider == "snowflake":
            db_schema = f"{self.database}.{self.schema}" if self.database else dataset
            return (await self._sf_query(f"SHOW TABLES IN {db_schema}")).get("rows", [])
        return []

    async def get_table_schema(self, dataset: str, table: str) -> dict[str, Any]:
        """Get table schema/metadata."""
        if self.provider == "bigquery":
            resp = await self._client.get(f"/projects/{self.project_id}/datasets/{dataset}/tables/{table}")
            resp.raise_for_status()
            return resp.json().get("schema", {})
        elif self.provider == "snowflake":
            return await self._sf_query(f"DESCRIBE TABLE {dataset}.{table}")
        return {}

    async def create_table(self, dataset: str, table: str, schema: list[dict[str, str]]) -> dict[str, Any]:
        """Create a table with schema definition."""
        if self.provider == "bigquery":
            bq_schema = [{"name": f["name"], "type": f.get("type", "STRING"), "mode": f.get("mode", "NULLABLE")} for f in schema]
            resp = await self._client.post(
                f"/projects/{self.project_id}/datasets/{dataset}/tables",
                json={"tableReference": {"projectId": self.project_id, "datasetId": dataset, "tableId": table}, "schema": {"fields": bq_schema}}
            )
            resp.raise_for_status()
            return resp.json()
        elif self.provider == "snowflake":
            cols = ", ".join(f'{f["name"]} {f.get("type", "VARCHAR")}' for f in schema)
            return await self._sf_query(f"CREATE TABLE {dataset}.{table} ({cols})")
        return {}

    async def insert_rows(self, dataset: str, table: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Insert rows into a table."""
        if self.provider == "bigquery":
            bq_rows = [{"json": row} for row in rows]
            resp = await self._client.post(
                f"/projects/{self.project_id}/datasets/{dataset}/tables/{table}/insertAll",
                json={"rows": bq_rows}
            )
            resp.raise_for_status()
            logger.info("Inserted %d rows into %s.%s", len(rows), dataset, table)
            return resp.json()
        elif self.provider == "snowflake":
            # Use SQL INSERT
            if rows:
                cols = ", ".join(rows[0].keys())
                values_list = []
                for row in rows:
                    vals = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in row.values())
                    values_list.append(f"({vals})")
                sql = f"INSERT INTO {dataset}.{table} ({cols}) VALUES {', '.join(values_list)}"
                return await self._sf_query(sql)
        return {}

    # ── Provider Implementations ───────────────────────────────

    async def _bq_query(self, sql: str, max_results: int = 10000) -> dict[str, Any]:
        resp = await self._client.post(
            f"/projects/{self.project_id}/queries",
            json={"query": sql, "useLegacySql": False, "maxResults": max_results}
        )
        resp.raise_for_status()
        data = resp.json()
        schema = [{"name": f["name"], "type": f["type"]} for f in data.get("schema", {}).get("fields", [])]
        rows = []
        for row in data.get("rows", []):
            rows.append({schema[i]["name"]: cell.get("v") for i, cell in enumerate(row.get("f", []))})
        return {"rows": rows, "schema": schema, "total_rows": int(data.get("totalRows", 0)), "job_complete": data.get("jobComplete", True)}

    async def _sf_query(self, sql: str) -> dict[str, Any]:
        payload: dict[str, Any] = {"statement": sql, "timeout": 120}
        if self._warehouse:
            payload["warehouse"] = self._warehouse
        if self.database:
            payload["database"] = self.database
        if self.schema:
            payload["schema"] = self.schema
        resp = await self._client.post("/api/v2/statements", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {"rows": data.get("data", []), "schema": data.get("resultSetMetaData", {}).get("rowType", []), "statement_handle": data.get("statementHandle", "")}

    async def _rs_query(self, sql: str) -> dict[str, Any]:
        resp = await self._client.post("/", headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "RedshiftData.ExecuteStatement",
        }, json={"ClusterIdentifier": self._cluster_id, "Database": self.database, "Sql": sql})
        resp.raise_for_status()
        return resp.json()
