# SFAEF-220 — Roadmap and exit criteria

## Milestone 0 — Adopt the specification and repair the current V2 branch

Exit:

- clean local baseline and backup tag;
- specification imported without becoming generated drift;
- missing Phase 1 files/tests restored;
- Phase 1 and Phase 2 commit boundaries truthful;
- review pack reproducible.

## Milestone 1 — Core framework and Cursor foundation

Exit:

- schemas/reference kernel integrated;
- native Cursor plugin installs locally;
- doctor, host capability report, policy broker, run bundle, context/evidence core work;
- no regression in existing repository tests/exports.

## Milestone 2 — P01 and P02 behaviorally ready

Exit:

- deployment and Apex test triage work from fixtures and existing live results;
- structured subagents and independent review verified in actual Cursor;
- context-rot suite passes;
- product tools remain read-only.

## Milestone 3 — P03 access path and scratch-org benchmark

Exit:

- access path product supports user/object/field/record/action scopes;
- at least six known-truth access scenarios;
- disposable scratch workflow with cleanup proof;
- first three products compared against vanilla host/model.

## Milestone 4 — P04–P06 flagship expansion

Exit:

- change impact, automation profiler, and release readiness are host-ready, fixture-qualified, and use shared core without copied orchestration.

## Milestone 5 — P07–P12 beta portfolio

Exit:

- typed product/agent/command/tool contracts;
- fixture-qualified end-to-end paths;
- clear beta labels and no unsupported stable claims.

## Milestone 6 — Multi-host and release candidate

Exit:

- Cursor stable adapter;
- Claude compatibility verified;
- at least one Copilot/VS Code or Vibes proof-of-concept adapter;
- requirement traceability complete;
- review bundle passes offline reconstruction;
- current quality report and release notes.

SFAEF-220-001. A milestone may continue autonomously only when its deterministic gates pass and no P0 safety ambiguity exists.

SFAEF-220-002. A P0 failure, credential ambiguity, non-disposable org uncertainty, or specification contradiction MUST stop execution and produce a failure review package.

SFAEF-220-003. Local commits and milestone tags MUST isolate review ranges even when one branch carries the full build.
