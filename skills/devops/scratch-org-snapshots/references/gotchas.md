# Gotchas — Scratch Org Snapshots

## Gotcha 1: Stale snapshot

**What happens:** CI builds pass but production deploy fails.

**When it occurs:** Snapshot older than 7 days.

**How to avoid:** Nightly refresh + last-modified monitoring.


---

## Gotcha 2: Snapshot with seed data

**What happens:** Tests pass only against seed data; real-world bug missed.

**When it occurs:** Heavy seed for demo.

**How to avoid:** Keep seed minimal or per-test.


---

## Gotcha 3: Region mismatch

**What happens:** Snapshot in one Dev Hub region, scratch org created elsewhere.

**When it occurs:** Multi-region Dev Hubs.

**How to avoid:** Pin Dev Hub per CI job.

