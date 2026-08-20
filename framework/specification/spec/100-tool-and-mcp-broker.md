# SFAEF-100 — Tool and MCP evidence broker

## Purpose

The broker exposes a small, stable, product-oriented evidence surface while upstream Salesforce CLI, official Salesforce DX MCP, SfSkills MCP, static analyzers, and local parsers evolve independently.

## Requirements

SFAEF-100-001. Every product tool MUST have a typed specification, input/output validation, permission class, timeout, result bound, and tests.

SFAEF-100-002. Unknown tools MUST be denied by default in product mode.

SFAEF-100-003. Tool annotations MAY inform UX but MUST NOT be treated as enforcement.

SFAEF-100-004. The broker MUST pin an explicit org identity for a run. `ALLOW_ALL_ORGS` and silent most-recent/default-job behavior are prohibited in product mode.

SFAEF-100-005. Dynamic default-org tokens MAY be used only after the resolved identity is shown and recorded; fixed aliases/usernames are preferred for consequential runs.

SFAEF-100-006. Upstream toolsets MUST be minimized. Enabling `all` is prohibited for the default product configuration.

SFAEF-100-007. Results MUST be normalized, redacted, bounded, assigned stable evidence IDs, and linked to the upstream tool/version.

SFAEF-100-008. Long operations MUST use explicit continuation/resume objects; agents MUST not poll without bounded policy.

SFAEF-100-009. Tool errors MUST be classified as input, auth, target mismatch, unavailable, timeout, rate, malformed upstream, policy, or unexpected.

## Read-only definition

A read-only product tool may retrieve, describe, list, query, compare captured data, or report existing job/test state. It may not deploy, cancel, retry, quick deploy, run anonymous Apex, perform DML, assign permissions, alter users, install packages, create/delete orgs, or change remote state.

SFAEF-100-020. A tool that triggers a test or validation job is not observational and requires a separate authority profile. V2 flagship user products SHOULD retrieve existing results; controlled QA setup may initiate tests in disposable orgs outside the product broker.

## Upstream strategy

SFAEF-100-030. Prefer official Salesforce DX MCP or CLI for canonical Salesforce operations.

SFAEF-100-031. Add SfSkills-specific wrappers only when they provide stable normalization, evidence semantics, bounded output, policy enforcement, or product-level aggregation.

SFAEF-100-032. Deterministic local analysis SHOULD use the underlying CLI/library directly when MCP adds no user or host value.
