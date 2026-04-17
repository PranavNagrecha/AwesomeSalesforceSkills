# MASTER_QUEUE format — current state + proposed migration

## Today (authoritative)

- `MASTER_QUEUE.md` holds the canonical queue. ~847 rows across multiple tables
  (core platform, role × cloud, domain sweeps, etc.).
- Each table has slightly different columns. Common ones are `#`, `Status`,
  `Skill` (or `Skill Name` / `Name`), `Domain`, `Notes`.
- Previously the orchestrator read/updated this file with `grep` and `sed`,
  which is fragile.

## What changed in this round

`scripts/queue_reader.py` is the structured reader. It:

- parses every table in `MASTER_QUEUE.md`, remembering each row's column map,
- exposes `--summary`, `--list`, `--next` (with `--status` filter), and
  `--set-status` (atomic, in-place) commands,
- always outputs JSON, so callers don't have to parse markdown themselves.

The orchestrator and any `run_next_skill` harness should use this reader going
forward. `MASTER_QUEUE.md` remains the source of truth — no YAML mirror is
needed yet.

### Example

```bash
# See distribution
python3 scripts/queue_reader.py --summary

# Get the next eligible row
python3 scripts/queue_reader.py --next --status TODO,RESEARCHED

# Claim a row
python3 scripts/queue_reader.py --set-status IN_PROGRESS \
  --id industries-public-sector-setup \
  --actor "claude-sonnet-4.5@$HOSTNAME"

# Release it (or mark DONE)
python3 scripts/queue_reader.py --set-status DONE \
  --id industries-public-sector-setup \
  --actor "claude-sonnet-4.5@$HOSTNAME"
```

## Proposed future migration (deferred)

Eventually the queue should move to a structured file + generator:

```
registry/queue/
  queue.yaml          # source of truth
  sections.yaml       # metadata for each table section
scripts/
  queue_reader.py     # read/update API (already exists)
  queue_render.py     # yaml -> MASTER_QUEUE.md
```

Proposed `queue.yaml` entry shape:

```yaml
- id: industries-public-sector-setup
  section: domain-sweeps
  status: TODO
  skill: industries-public-sector-setup
  domain: industries
  summary: >-
    Public Sector Solutions setup: licensing, permits, inspections,
    case management for government, citizen portal.
  not_for: standard case management
  notes: []
  history:
    - actor: claude-sonnet-4.5
      status: IN_PROGRESS
      at: 2026-04-16T18:00:00Z
```

### Why defer the migration

- The markdown is human-skimmable; several humans read it weekly. Losing that
  until a renderer exists is a regression.
- 847 rows across 10+ table shapes is a non-trivial migration. The benefit is
  marginal once `queue_reader.py` gives us a clean programmatic interface.
- Status history is the real motivator. We can add that today by growing the
  `Notes` column (the reader already prepends `actor @ ISO-timestamp`).

### Triggering the migration

Cut over to `queue.yaml` once any of these happens:

1. We want per-row structured metadata (e.g. dependencies, blockers, owner)
   that doesn't fit the markdown table.
2. We want the queue to be consumed by a non-markdown UI.
3. The `(unparsed)` count from `queue_reader.py --summary` climbs because rows
   can't be encoded in a flat table anymore.

Until then, `MASTER_QUEUE.md` + `scripts/queue_reader.py` is the contract.
