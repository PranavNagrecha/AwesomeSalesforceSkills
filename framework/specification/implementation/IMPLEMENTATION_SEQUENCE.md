# Full V2 implementation sequence

## Operating model

Use one local integration branch with reviewable local commits and milestone tags. Do not push or publish. Cursor may proceed through milestones without waiting for routine confirmation only when all deterministic gates pass. It must stop on a P0 safety ambiguity, destructive target uncertainty, unrecoverable baseline, credential uncertainty, or specification contradiction.

Recommended branch:

```text
product/sfskills-v2-local
```

## M0 — Preserve, baseline, and adopt the specification

Deliver:

- working-tree and branch inventory;
- backup patch/archive of pre-existing uncommitted work;
- exact baseline test logs;
- specification imported under a stable path;
- reference kernel tests running from the repository;
- requirement traceability generation;
- current partial Phase 1/2 work mapped to the specification, not overwritten blindly.

Tag: `sfskills-v2-m0-spec-adopted`

## M1 — Deterministic core and evidence broker

Deliver:

- schemas and definition loaders;
- run state and output envelope v2 compatibility;
- context compiler/checkpoints;
- evidence/claim graph and deterministic lint;
- policy/authority/target identity controls;
- redacted run bundle and replay validation;
- restricted broker interface over existing SfSkills and official Salesforce tools;
- explicit `index_missing` and doctor capability report.

Tag: `sfskills-v2-m1-core`

## M2 — Native Cursor and first two products

Deliver:

- native local Cursor plugin, deterministic build/check, install/uninstall;
- bounded product/domain skill discovery;
- proven focused subagents;
- P01 Deployment Failure Triage;
- P02 Apex Test Failure Triage;
- actual Cursor fixture smoke runs and independent review;
- existing-result read-only live verification where available.

Tag: `sfskills-v2-m2-triage`

## M3 — Access product and behavioral QA lab

Deliver:

- P03 Access Path Explainer;
- protected scratch-org setup/capture/grade/cleanup framework;
- six deployment, seven Apex, and six access scenarios where technically stable;
- baseline comparison against vanilla host/model;
- secret scan and deletion proof.

Tag: `sfskills-v2-m3-behavioral-qa`

## M4 — Remaining flagship products

Deliver P04–P06:

- Change Impact Planner;
- Automation Transaction Profiler;
- Release Readiness Review.

Each must have actual Cursor fixture execution, typed evidence, context limits, independent review, and no copied orchestration.

Tag: `sfskills-v2-m4-flagship`

## M5 — Beta portfolio

Deliver P07–P12 as beta:

- Security Posture Review;
- Integration Incident Triage;
- Data Migration Reconciliation;
- Org Health Assessment;
- Agentforce Quality Engineer;
- Multi-Org Drift Analysis.

Each needs an end-to-end fixture path, product/agent/command/tool contract, evidence lint, host smoke, and limitations. Do not fake scratch qualification.

Tag: `sfskills-v2-m5-beta-portfolio`

## M6 — Portability and release candidate

Deliver:

- Cursor release package;
- Claude compatibility/regression verification;
- one VS Code/Copilot or Vibes proof-of-concept adapter;
- portable Agent Plugin feasibility package if licensing allows;
- current quality and compatibility report;
- generated docs/manifests/counts from canonical definitions;
- final local aggregate review package.

Tag: `sfskills-v2-rc1-local`

## Milestone gate rule

A milestone commit may include only work required for that milestone and prerequisites. Later product work found on the current branch must be preserved in later commits or a backup branch, not hidden inside an earlier review range.
