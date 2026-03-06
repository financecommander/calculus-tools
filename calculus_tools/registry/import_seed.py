#!/usr/bin/env python3
"""Bulk-import seed APIs into the registry.

Usage::

    # Import the bundled JSON seed file (in-memory, no DB required):
    python -m calculus_tools.registry.import_seed

    # Import from a custom file:
    python -m calculus_tools.registry.import_seed --file /path/to/apis.json
    python -m calculus_tools.registry.import_seed --file /path/to/apis.csv

Set ``DATABASE_URL`` to persist to PostgreSQL; otherwise data is loaded
into memory and printed for verification.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from calculus_tools.registry.store import RegistryStore

SEED_DIR = Path(__file__).parent


def _resolve_file(path: str | None) -> Path:
    if path:
        p = Path(path)
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)
        return p
    # default: bundled JSON seed
    return SEED_DIR / "seed_apis.json"


async def main(filepath: Path) -> None:
    store = RegistryStore()
    await store.connect()

    suffix = filepath.suffix.lower()
    if suffix == ".json":
        count = await store.import_json(filepath)
    elif suffix == ".csv":
        count = await store.import_csv(filepath)
    else:
        print(f"ERROR: unsupported file type: {suffix}", file=sys.stderr)
        sys.exit(1)

    print(f"Imported {count} APIs from {filepath.name}")

    apis = await store.list_apis()
    print(f"\nRegistry now contains {len(apis)} enabled API(s):\n")
    for api in apis:
        print(f"  [{api.api_id:>3}] {api.name:<25} {api.category.value:<15} {api.base_url}")

    await store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import APIs into the registry")
    parser.add_argument("--file", "-f", help="Path to JSON or CSV file")
    args = parser.parse_args()
    asyncio.run(main(_resolve_file(args.file)))
