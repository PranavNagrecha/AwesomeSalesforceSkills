"""RELEASES.yaml schema: the release plan the orchestrator reads must stay well-formed."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

DATA = yaml.safe_load((Path(__file__).resolve().parents[1] / "RELEASES.yaml").read_text(encoding="utf-8"))
RELEASES = DATA["releases"]
ITEMS = [(r["version"], i) for r in RELEASES for i in r["items"]]


def test_top_level_keys():
    assert {"version", "baseline", "releases", "inbox"} <= set(DATA)
    assert RELEASES


@pytest.mark.parametrize("rel", RELEASES, ids=lambda r: str(r["version"]))
def test_release_shape(rel):
    for key in ("version", "mcp_version", "branch", "ships", "freeze", "items"):
        assert rel.get(key) not in (None, "", []), f"{rel.get('version')}: missing {key}"
    assert rel["branch"] == f"release/{rel['version']}"
    assert isinstance(rel["ships"], date) and isinstance(rel["freeze"], date)
    assert rel["freeze"] < rel["ships"]


def test_ships_at_least_14_days_apart():
    ships = [r["ships"] for r in RELEASES]
    for a, b in zip(ships, ships[1:]):
        assert (b - a).days >= 14, f"{a} -> {b}"


def test_item_ids_unique():
    ids = [i["id"] for _, i in ITEMS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("ver,item", ITEMS, ids=lambda x: x if isinstance(x, str) else x["id"])
def test_item_shape(ver, item):
    assert item.get("id") and item.get("title")
    assert item.get("size") in {"S", "M", "L"}
    assert item.get("owner_model") in {"opus", "sonnet", "fable"}
    assert item.get("status") in {"todo", "running", "done", "dropped"}
    if item["status"] == "done":
        assert str(item.get("evidence") or "").strip(), f"{item['id']} is done without evidence"


@pytest.mark.parametrize("entry", DATA["inbox"] or [])
def test_inbox_entry_shape(entry):
    for key in ("date", "ask", "size", "slotted_into"):
        assert entry.get(key), f"inbox entry missing {key}: {entry}"
    assert entry["size"] in {"S", "M", "L"}
