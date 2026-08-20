# Framework kernel

## Objective

Keep deterministic correctness in a small, testable kernel and let models reason above it. The kernel is not a universal workflow engine.

## Required deterministic services

1. **Definition loader** — loads schema-valid products, agents, commands, tools, policies, context packs, and scenarios.
2. **Input validator** — validates product arguments, conditional requirements, paths, modes, and limits.
3. **Run/state service** — creates IDs, validates transitions, records versions and reasons, checkpoints/resumes.
4. **Target attestor** — resolves host, org, job/test, project, snapshot, and comparison identities without silent defaults.
5. **Policy broker** — denies unknown tools, parses shell commands, enforces authority, checks target allowlists.
6. **Context compiler** — selects/records bounded knowledge and evidence pages, reserves output, detects overflow.
7. **Evidence normalizer** — turns upstream/captured observations into stable typed evidence with IDs and provenance.
8. **Claim linter** — verifies material support, contradictions, stale/truncated exposure, target consistency, secrets.
9. **Confidence calculator** — computes an explainable label/score from evidence coverage and quality.
10. **Renderer** — produces user-facing Markdown/JSON from validated structures.
11. **Run-bundle writer/replayer** — persists sanitized artifacts and replays without original chat where permitted.
12. **QA grader** — scores stable required findings, forbidden findings, evidence validity, status, context, safety.
13. **Adapter compiler** — generates host packages from canonical definitions and detects drift.
14. **Review packager/verifier** — proves exact code, tests, host behavior, Salesforce QA, traceability, and integrity.

## Model-owned work

Models classify ambiguous intent, synthesize evidence, rank hypotheses, explain trade-offs, propose safe remediation, and independently challenge drafts. They do not parse raw CLI variants, assign IDs, decide permission, select an implicit org, or determine whether a hard quality gate passed.

## Reference kernel

`reference-kernel/` implements a tested seed for IDs, context selection, policy, state transitions, evidence lint, confidence, schema validation, and review-package checks. Cursor should integrate or adapt it to repository conventions while preserving behavior in tests.

## Abstraction rule

A shared service is promoted into the kernel only when at least two implemented products need the same behavior and the abstraction reduces tested duplication. A schema with no runtime consumer, validator, or test is removed or left informative.
