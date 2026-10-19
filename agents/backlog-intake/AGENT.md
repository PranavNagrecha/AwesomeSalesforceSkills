---
id: backlog-intake
class: build
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-10-19
updated: 2026-10-19
dependencies:
  shared:
    - AGENT_RULES.md
---
# Backlog Intake Agent

## What This Agent Does

Takes one ask in the owner's words, sizes it S, M, or L, adds it to the release plan in `RELEASES.yaml` through `scripts/release_plan.py add` (which slots it into the right release), checks the plan still passes its tests, commits `RELEASES.yaml` alone, and replies in three lines.

**Scope:** one ask per invocation. It touches no file except `RELEASES.yaml`, never re-sequences existing items, and never starts the work.

---

## Invocation

- **Direct read** — "Follow `agents/backlog-intake/AGENT.md` for this ask: <text>."
- **Slash command** — [`/add-to-backlog`](../../commands/add-to-backlog.md) `<ask text>`
- **MCP** — `get_agent("backlog-intake")`

Args: the ask text. If it is empty, ask for it; do not guess.

---

## Mandatory Reads Before Starting

1. `AGENT_RULES.md` — repo-wide rules every agent follows.
2. `RELEASES.yaml` — the header comment only: the size vocabulary and the slotting rule. Do not parse the item list; `release_plan.py` does that.

---

## Plan

### Step 1 — Restate

Write the ask as one line, in the imperative. This becomes `--title`.

### Step 2 — Size

Use the size vocabulary in the `RELEASES.yaml` header:

| Size | Meaning | Examples |
|---|---|---|
| S | under 1 agent-hour | a trigger, a checker rule, a doc line |
| M | up to 1 agent-day | a tooling script plus tests, a 10-skill wave, one agent playbook |
| L | multi-day | a new layer, a corpus-wide pass |

If the ask spans two sizes, take the larger. `release_plan.py add` prefixes L items with `[split before scheduling]`; do not split them yourself.

### Step 3 — Add

```bash
git status --short RELEASES.yaml
python3 scripts/release_plan.py add "<ask text>" --size <S|M|L> --title "<imperative title>"
```

The command prints `<id> -> release <version>`. Use `--owner-model {opus,sonnet,fable}` only when the ask names a model; the default is sonnet for S and opus otherwise.

### Step 4 — Check

```bash
python3 -m pytest tests/test_releases.py -q
```

If it fails, report the failure and do not commit.

### Step 5 — Commit

If `git status --short RELEASES.yaml` printed nothing before Step 3, commit that file alone:

```bash
git commit RELEASES.yaml -m "plan: <id> <title> (<size> → <release>)"
```

If `RELEASES.yaml` already had uncommitted changes before Step 3, do not commit: the orchestrator owns that file and its next commit carries the new item. Say so in the reply.

### Step 6 — Reply

At most 3 lines: the id, the release, its `ships` date (`grep -A6 "version: <release>" RELEASES.yaml | grep ships`), and one clause on why that size.

---

## Output Contract

The 3-line reply from Step 6, plus a **Process Observations** line: one of *healthy / concerning / ambiguous / suggested follow-up* when you noticed something while reading the plan (cite the item id or command output), for example a near-duplicate of an existing item's title, or an ask that is really two asks. If nothing is notable, write "nothing notable outside the direct finding."

---

## Escalation / Refusal Rules

| Situation | Action |
|---|---|
| Empty ask | Ask for it. |
| `release_plan.py add` exits non-zero (no open release to slot into) | Print its message. Change nothing. |
| `tests/test_releases.py` fails after the add | Report the failure. Do not commit. |
| The ask contains two or more unrelated asks | Add the first, name the rest in the reply, and ask for them one per invocation. |
| The ask is "do X now" | Add it anyway and say `/start-building` runs it; this agent never starts work. |

---

## What This Agent Does NOT Do

- Edit any file other than `RELEASES.yaml`, and edit that only through `release_plan.py`.
- Re-sequence, re-size, or re-slot existing items.
- Start, scaffold, or research the work.
- Run `git push`, `git tag`, or any deploy.
- Process more than one ask per invocation.
