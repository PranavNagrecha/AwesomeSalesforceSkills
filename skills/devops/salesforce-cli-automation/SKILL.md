---
name: salesforce-cli-automation
description: "Use this skill when automating Salesforce work with the unified Salesforce CLI (`sf`, v2): shell scripts, Make/npm tasks, cron jobs, and CI steps that need stable flags, `--json` output, org aliases, bulk/data commands, plugins, and non-interactive auth patterns. Trigger keywords: sf CLI automation, sfdx migration, JSON output CI, sf project deploy script, sf data bulk, CLI plugins, target-org alias, machine-readable CLI. NOT for choosing or wiring a specific CI platform (GitHub Actions, GitLab, Jenkins, Bitbucket, Azure DevOps—use those devops skills), VS Code Salesforce extensions, or Copado/Gearset release management UIs."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how do I script Salesforce CLI commands so my deploy pipeline gets parseable JSON back"
  - "we still have sfdx force commands in shell scripts and need to migrate everything to sf v2"
  - "sf apex run test or sf project deploy start hangs in automation because we are not waiting or parsing async IDs correctly"
  - "how do I run sf data bulk or tree export import between orgs from a script without clicking in the UI"
  - "what flags should I always set when running sf in GitLab or Jenkins for repeatable non-interactive runs"
tags:
  - salesforce-cli
  - sf-cli-v2
  - cli-automation
  - json-output
  - shell-scripting
  - devops
inputs:
  - "Automation context: local developer script, shared build script, or CI runner image constraints"
  - "Target org alias or username and whether login is interactive, JWT, or existing SFDX auth file"
  - "Operation: deploy, retrieve, test, data import/export, org creation, or query"
  - "Whether downstream tooling expects JSON, JUnit XML, or human logs"
outputs:
  - "Concrete `sf` command sequences with flags suited for automation"
  - "Notes on `--json`, `--wait`, `--async`, and exit-code behavior for reliable gates"
  - "Migration mapping away from legacy `sfdx force:*` where relevant"
dependencies:
  - apex/sf-cli-and-sfdx-essentials
  - devops/continuous-integration-testing
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Salesforce CLI Automation

This skill activates when the task is to design, refactor, or troubleshoot **automation that drives Salesforce through the CLI**—not when the primary question is “which CI YAML product to use,” but when the core problem is **how `sf` behaves under scripts**, how to get **stable machine-readable output**, and how to avoid the sharp edges of **async commands, org selection, and deprecated `sfdx` syntax**. Official behavior, flags, and command families are defined in the [Salesforce CLI Reference](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm); project and auth models are covered in the [Salesforce DX Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm); metadata semantics that the CLI ultimately invokes belong in the [Metadata API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm).

The Salesforce CLI **v2** exposes capabilities under the `sf` executable. Legacy `sfdx force:*` style commands remain for compatibility in many environments, but **new investment and features ship in `sf`**, and automation should standardize on `sf` so scripts do not break when legacy paths narrow. Treat the CLI as a **contract with stdout/stderr and exit codes**: in CI, prefer **`--json`** on commands that support it when you parse results, and pair long-running operations with **`--wait`** or explicit **async job polling** (`--async` plus follow-up commands) so pipelines do not finish “green” while work is still running server-side.

**Org targeting** should always be explicit in shared automation: use **`--target-org <alias>`** (or the supported environment variables your runner sets) so a developer laptop default alias cannot silently change production. **Plugins** extend `sf`; pin versions when a script depends on a plugin command, because plugin updates can change flags or output shape. For **data** at scale, favor the families documented under data commands (`sf data` tree vs bulk paths per the CLI reference) instead of ad-hoc REST scripts that duplicate CLI-tested flows.

This skill complements **platform-specific CI skills** (which show where to store secrets and how to structure jobs) and **interactive CLI essentials** (day-to-day auth and scratch org creation). Here the focus stays on **portable CLI automation patterns** any environment can reuse.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Executable and version:** Is the runner using global `sf` from the [Salesforce CLI installers](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm) or a pinned npm `@salesforce/cli`? Mismatched versions explain flag drift between laptop and CI.
- **Auth model:** Interactive `sf org login web` cannot complete in headless automation—CI needs JWT or a pre-provisioned auth file on the runner. Know which org alias each step must target.
- **Output contract:** Does a downstream step parse JSON with `jq`, archive JUnit, or only need a pass/fail exit code? That determines `--json`, `--result-format`, and whether you must scrape job IDs from async responses.
- **Most common wrong assumption:** That a zero exit code always means “deploy/tests fully succeeded” without `--wait` or without reading JSON status fields—many flows enqueue work and return before completion unless configured otherwise.
- **Limits:** Platform test timeouts, concurrent deployment limits, and data API bulk thresholds still apply; the CLI surfaces errors, but automation must retry and backoff responsibly.

---

## Core Concepts

### Stable, parseable CLI output

Human tables and spinners are convenient locally but brittle in logs. For automation, prefer **`--json`** where the command supports it so your script inspects structured `status`, `result`, and error arrays instead of regexing prose. When a command offers **`--result-format`** (for example Apex tests), pick **`json` or `junit`** to match the consumer. Keep **`SF_USE_PROGRESS_BAR=false`** (or equivalent environment conventions your org standardizes) so progress rendering does not corrupt captured output in CI logs.

### Synchronous completion vs async job IDs

Deploy and test commands can return before server-side work completes unless you set **`--wait`** with an adequate timeout or deliberately run **`--async`** and poll with the companion “report” or “resume” style commands documented in the CLI reference for that command family. Scripts that omit waiting are a frequent source of flaky pipelines that merge broken metadata because validation had not finished.

### Org aliases, default orgs, and CI isolation

Automation must not rely on whatever `sf config get target-org` returns on a shared runner. Pass **`--target-org`** on every mutating command, derive dynamic values (instance URL, org id) with `sf org display --json` when needed, and avoid storing long-lived refresh tokens in repo files—use the secret mechanism of the hosting platform, surfaced to the process environment for `sf org login jwt` or similar non-interactive flows described in the Salesforce DX Developer Guide.

---

## Common Patterns

### JSON gate wrapper

**When to use:** A shell script must fail the build if a deploy or test command reports failure in JSON even when stderr looks clean.

**How it works:** Run `sf <command> ... --json`, capture stdout, parse with `python3 -c` or `jq` to check top-level `status` (and nested `result.success` where applicable), and exit non-zero on failure. Keep CLI stderr visible for supportability.

**Why not the alternative:** Grepping for the word `Error` in human output breaks on localized CLI messages and minor formatting changes.

### Replace legacy `sfdx force:*` in scripts

**When to use:** Maintenance on older bash or npm scripts still calling `sfdx force:source:deploy` or similar.

**How it works:** Map to `sf project deploy start`, `sf project retrieve start`, `sf apex run test`, and other unified topics listed in the CLI reference migration sections. Install only the modern CLI toolchain on runners to avoid conflicting executables.

**Why not the alternative:** Keeping `sfdx` indefinitely stores technical debt and duplicates auth/config behavior between two entry points.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need structured output for tooling | Add `--json` (and parse explicitly) | Stable schema-oriented integration per CLI reference |
| Long deploy or full test suite in CI | Use `--wait` with a timeout above peak runtime | Prevents returning before completion |
| Very large data movement between orgs | Use `sf data` bulk-related commands per docs | Designed for volume instead of record-by-record scripts |
| Developer-only convenience script | Human output acceptable; still pin `--target-org` | Reduces accidental cross-org execution |

---

## Recommended Workflow

1. Confirm the automation environment: `sf` version, plugins, headless vs interactive, and which org aliases exist on the runner.
2. Identify the operation family (project deploy, Apex test, data, org login) in the Salesforce CLI Reference and list required flags: `--target-org`, `--json` or `--result-format`, and wait/async behavior.
3. Rewrite or validate commands to avoid legacy `sfdx force:*` namespaces unless a documented exception applies.
4. Add explicit completion handling (`--wait` or async polling) and assert success using structured output, not log scraping.
5. Run the skill’s `check_salesforce_cli_automation.py` against the repository root to catch common automation footguns in CI and shell files.
6. Document the final command snippets and environment variables for operators who will extend the script later.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every automated command specifies `--target-org` (or equivalent explicit targeting).
- [ ] Machine-readable output format matches what parsers expect (`--json`, JUnit, etc.).
- [ ] Long-running commands either wait or implement async polling with timeouts.
- [ ] No interactive `sf org login web` steps remain in headless paths.
- [ ] Legacy `sfdx force:` usage is removed or tracked as debt with a migration issue.
- [ ] Secrets are injected via the host platform, not committed keys or tokens in scripts.

---

## Salesforce-Specific Gotchas

1. **Silent async returns** — Some commands enqueue work and can return before the org finishes processing unless `--wait` is set appropriately; pipelines may pass while deployments or tests are still running or failing afterward.
2. **Default org leakage** — Omitting `--target-org` on shared runners can apply metadata to whatever alias happens to be authorized last, which is a severe reliability and security risk.
3. **Output format drift** — Parsing human-formatted tables breaks across CLI versions; `--json` fields are the supported integration surface where available.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `sf` command snippets | Copy-pasteable commands with automation-oriented flags for scripts and jobs |
| JSON parsing notes | Which top-level keys to assert after `--json` for the command families in use |
| Migration notes | Legacy `sfdx` → `sf` mapping relevant to the scripts under review |

---

## Related Skills

- `apex/sf-cli-and-sfdx-essentials` — interactive CLI setup, scratch org basics, and everyday `sf` commands when automation is not the primary concern
- `devops/continuous-integration-testing` — Apex test levels, coverage gates, and CI-specific testing patterns
- `devops/github-actions-for-salesforce` (or GitLab / Bitbucket counterparts) — platform YAML, secrets, and runner configuration when the deliverable is a full pipeline file
