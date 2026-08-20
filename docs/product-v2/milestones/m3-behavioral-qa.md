# M3 — Behavioral QA (stub)

## Purpose

Stand up the **scratch-org behavioral QA lab skeleton** and record that live scratch runs are **not_run** until Dev Hub allowlisting, scenario fixtures, and host harnesses exist.

## Status

| Track | Result |
| --- | --- |
| Fixture product tests (P03–P12) | in-repo unit tests; no org required |
| Scratch-org lab | **not_run** — see `qa/scratch/NOT_RUN.json` |
| Dev Hub | **not required** for this stub |

## Scratch lab

Layout and guard sequence: `qa/scratch/README.md` and `framework/specification/qa/scratch-org-lab.md`.

Create/setup/destroy scripts are **not** MCP tools. `qa/scratch/scripts/create.py` refuses unless `SFSKILLS_SCRATCH_OPT_IN=1` and still returns `not_implemented` in M3.

## Gates expected later

- Protected CI or explicit local opt-in
- Dev Hub allowlist
- Capture then product-read-only authority
- Unconditional destroy + deletion proof

Until those exist, graders must treat scratch behavioral QA as `not_run`, not as a pass.
