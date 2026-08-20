# SfSkills — Salesforce AI Engineering Framework

**Specification status:** Draft 0.9.0  
**Research freeze:** 2026-08-19  
**Implementation target:** SfSkills V2 release candidate  
**Primary host:** Cursor, with portable contracts for Claude Code, VS Code/GitHub Copilot, Agentforce Vibes, and future Agent Plugins/A2A adapters.

This package is the constitutional product specification for evolving the existing SfSkills repository from a large Salesforce skill library into an evidence-grounded AI engineering framework.

It contains the part of the product that should be designed before implementation:

- product vision, competitive position, adoption thesis, and measurable 40% early-adopter wedge;
- 23 normative specification chapters with 266 stable requirements;
- eight-plane reference architecture, trust boundaries, data/control flows, and deployment topologies;
- 12 typed product definitions and complete user-job narratives;
- 20 core/product agent contracts, including authority, evidence, context, failure, and evaluation rules;
- 18 typed command contracts and 18 read-only evidence-tool contracts;
- 12 conditional context packs and 19 JSON Schemas;
- 74 versioned known-truth scenarios across hermetic, live-read-only, scratch-org, and host lanes;
- context, evidence, confidence, security, privacy, replay, and run-state contracts;
- Cursor-first and portable host-adapter guidance;
- deterministic, adversarial, actual-host, and real-org QA designs;
- artifact-level V2 disposition ledgers for all 1,034 skills, 76 canonical agents, 67 commands, and 38 MCP tools in the uploaded snapshot;
- a tested Python reference kernel and project-inspector reference component;
- a product-owner review system and offline Cursor return-ZIP verifier;
- the complete local implementation sequence and exact Cursor return-package contract.


## Package inventory

| Contract surface | Count |
|---|---:|
| Normative requirements | 266 |
| Product definitions | 12 |
| Core and product agents | 20 |
| Typed commands | 18 |
| Read-only evidence tools | 18 |
| Product context packs | 12 |
| Known-truth QA scenarios | 74 |
| JSON Schemas | 19 |
| External research source records | 37 |
| Uploaded baseline skills covered by migration ledger | 1,034 |
| Uploaded baseline agents / commands / MCP tools covered | 76 / 67 / 38 |

The counts above are generated or validated. They are not product-success metrics.

## What this is

This is a **source-of-truth specification and integration kit**. Cursor should implement against numbered requirements and schemas rather than inventing architecture while coding.

The package intentionally includes executable reference logic for the most failure-prone controls: stable identifiers, context budgets, claim/evidence linting, policy decisions, run-state transitions, and review-package integrity. That reference code is not a complete SfSkills runtime; it is a tested behavioral oracle and implementation seed.

## What V2 becomes

SfSkills V2 is not merely a larger collection of prompts. It is a portable Salesforce engineering intelligence layer with eight planes:

1. **Experience plane** — commands and product workflows that solve real Salesforce jobs.
2. **Agent plane** — narrowly scoped execution roles with isolated contexts.
3. **Context plane** — progressive loading, budgets, checkpoints, and compaction recovery.
4. **Knowledge plane** — the existing curated skill corpus and source governance.
5. **Evidence plane** — normalized org, project, job, test, and source observations.
6. **Control plane** — typed inputs, run state, policy, permissions, and host capability negotiation.
7. **Quality plane** — deterministic validation, independent review, benchmarks, and scratch-org known truth.
8. **Adapter plane** — Cursor first, then other hosts and open standards.

## Start here

- `PACKAGE_REPORT.md` — scope, contents, product portfolio, validation, and truthful limitations.
- `START_HERE.md` — owner and implementer entrypoint.
- `SPEC_INDEX.md` — reading order and conformance map.
- `research/010-executive-product-thesis.md` — the market and product thesis.
- `strategy/README.md` — category, wedge, competition, adoption, packaging, and scorecard.
- `spec/020-design-principles.md` — binding product constitution.
- `spec/040-reference-architecture.md` — system shape and boundaries.
- `products/README.md` — product portfolio.
- `implementation/IMPLEMENTATION_SEQUENCE.md` — local milestone plan.
- `implementation/CURSOR_BUILD_SFSAEF_V2.md` — copy-ready Cursor implementation prompt.
- `implementation/REVIEW_RETURN_CONTRACT.md` — exact artifact required back from Cursor.
- `review/PRODUCT_OWNER_REVIEW_PROTOCOL.md` — how every returned implementation is accepted or rejected.
- `migration/catalogs/V2_DISPOSITION_LEDGER.md` — preserve/migrate posture for the complete uploaded baseline.

## Validate the package

From the extracted package root:

```bash
python3 -B scripts/run_all_checks.py --write-generated
python3 -B scripts/run_all_checks.py
```

The second command must pass without changing tracked/generated content. `tools/run_package_checks.sh` provides an additional independent validator/test path.

## Definition of “80% designed”

The package considers product architecture substantially designed when product behavior, trust boundaries, contracts, schemas, failure semantics, host capabilities, QA truth, and release gates are explicit. The remaining work is implementation, host integration, empirical tuning, and evidence from real users and real Salesforce scenarios.

## Naming

- **SfSkills** remains the repository and product brand.
- **Salesforce AI Engineering Framework** describes the product category.
- **SFAEF** is the specification namespace used in requirement IDs.
- **`sfskills`** is the proposed CLI/runtime namespace.

Salesforce is a trademark of Salesforce, Inc. This project is independent and is not represented as an official Salesforce product.


## Give this to Cursor

Provide Cursor with this complete directory and the single prompt:

```text
implementation/CURSOR_BUILD_SFSAEF_V2.md
```

Cursor works only on a local branch, adopts the specification under a stable repository path, implements milestones in order, makes local commits and annotated local tags, and stops on a P0 blocker or specification contradiction. It MUST NOT push, publish, open a pull request, modify a remote, or claim Marketplace availability.

Before implementation, validate this package:

```bash
python3 scripts/run_all_checks.py --write-generated
python3 scripts/run_all_checks.py
```

The first command refreshes deterministic catalogs, machine contracts, API references, and the package manifest. The second proves that no generated contract has drifted.

## What Cursor must return

Cursor returns exactly one self-contained archive named:

```text
sfskills-v2-cursor-return-YYYYMMDD-HHMMSS.zip
```

The archive contract is defined in `implementation/REVIEW_RETURN_CONTRACT.md`. It includes a reconstructable Git bundle, exact source, local commits/tags, every test command and real log, generated Cursor plugin, actual host-smoke evidence, representative run bundles, context telemetry, evidence/claim graphs, independent reviews, Salesforce QA evidence, security/adversarial results, requirement traceability, deviations, checksums, secret scan, and offline reconstruction proof.

A completed package cannot contain a failed required gate. A blocked package may preserve a real failure only when it says `blocked` or `failed`, includes the actual failing evidence, and makes no completion claim.

## Generated implementation references

- `commands/API_REFERENCE.md` — all typed command APIs.
- `mcp/TOOL_REFERENCE.md` — all normalized evidence-tool contracts.
- `agents/CONTRACT_REFERENCE.md` — all core and product agent authority contracts.
- `implementation/requirements.csv` — every numbered normative requirement and exact source line.
- `FRAMEWORK_MANIFEST.json` — deterministic file inventory and hashes.
