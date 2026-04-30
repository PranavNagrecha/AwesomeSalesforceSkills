---
name: code-coverage-orphan-class-cleanup
description: "Use when an org's overall Apex coverage is sliding toward 75% because of orphaned (uncovered, unreferenced) classes inflating the denominator. Triggers: 'production deploy blocked at 74% coverage', 'find apex classes with 0% coverage', 'orphan apex class report', 'org coverage dropping despite green test runs'. NOT for writing tests on actively used classes (use apex/test-class-standards) or for raising coverage on partially-covered classes."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "production deploy blocked at 74 percent code coverage"
  - "find apex classes with zero coverage"
  - "orphan apex classes that no test exercises"
  - "old apex classes from a deprecated package still reducing org coverage"
  - "reduce coverage denominator before next release"
tags:
  - apex
  - coverage
  - tech-debt
  - cleanup
  - deployment
inputs:
  - "ApexCodeCoverage / ApexCodeCoverageAggregate snapshot from the org"
  - "list of installed packages (managed code coverage rules differ)"
  - "git history for last-modified dates"
outputs:
  - "ranked list of orphan classes (zero coverage + zero references)"
  - "destructive-changes manifest for safe-to-delete classes"
  - "test-required list for classes that must stay"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Code Coverage Orphan Class Cleanup

Activate when an org's overall Apex coverage has crept toward the 75% deploy threshold and the source of the drag is *uncovered, unreferenced* classes accumulated over years of half-finished features. The skill produces a ranked list of orphan classes, separates "delete-safe" from "test-required-to-keep," and emits a destructive-changes manifest.

---

## Before Starting

Gather this context before working on anything in this domain:

- Current org-wide coverage and the gap to 75%. The Tooling API query against `ApexOrgWideCoverage` gives a single number; per-class data lives in `ApexCodeCoverageAggregate`.
- Whether managed-package classes are inflating the denominator. Salesforce excludes managed-package code from the org-wide calculation, but unmanaged code from a previously-installed-then-uninstalled package may still be present.
- Any classes flagged as `@deprecated` already, since those telegraph the team's intent.
- Whether any of the candidate classes are referenced from non-Apex artifacts: Flow Apex action invocations, LWC `@AuraEnabled` callers, REST endpoints (URL mappings), Process Builder Apex actions, scheduled jobs, custom buttons. Coverage-only signals miss these references.

---

## Core Concepts

### Coverage denominator

The 75% threshold is computed across **all unmanaged Apex** in the org (classes + triggers, excluding test classes). Removing a 200-line class with 0% coverage subtracts 200 from both the numerator and the denominator's "uncovered" portion — net positive on the percentage.

### "Orphan" definition

A class is an *orphan* candidate when **all** of the following hold:

- 0% coverage in `ApexCodeCoverageAggregate` over the last full test run.
- No source-code reference: no `extends`, `implements`, `new <Class>`, static call, or type usage in any other Apex.
- No metadata reference: not invoked from a Flow, Process Builder, scheduled job, REST mapping, custom button/link, validation rule formula (`$Apex`), or LWC's `@AuraEnabled` calls.
- Not annotated `@RestResource`, `@HttpGet/Post/...` (otherwise it's an external entry point even if no Apex calls it).

If all four hold, the class is delete-safe. If only the first three hold and the class has, e.g., a custom button reference, it must keep its test.

### Coverage queries that lie

`ApexCodeCoverage` (per-test) and `ApexCodeCoverageAggregate` (latest-run) only reflect the **last test run**. If the run was incomplete or skipped a class because a dependency failed, coverage shows zero for that class for reasons other than missing tests. Always run a clean `--test-level RunLocalTests` before treating coverage as authoritative.

---

## Common Patterns

### Pattern: pre-deploy coverage rescue

**When to use:** Friday's deploy fails at 74.3%. You need to ship by Monday.

**How it works:** Query `ApexCodeCoverageAggregate` for 0%-coverage classes ordered by NumLinesCovered DESC + NumLinesUncovered DESC. Static-reference-check the top 20. Of those that pass all four orphan criteria, build a destructive-changes manifest and deploy with `--purge-on-delete=true` (sandbox first).

**Why not the alternative:** Writing 4,000 lines of stub tests under deadline pressure produces brittle tests that obscure real coverage signal.

### Pattern: scheduled tech-debt cleanup

**When to use:** Quarterly engineering tax.

**How it works:** Same query, but instead of destructive deploy, file a per-class issue with the orphan evidence. Engineers triage: delete, test, or document why kept.

### Pattern: package-deprecation cleanup

**When to use:** A managed package was uninstalled but unmanaged "ghost" classes remain (e.g., from an early-stage 1GP install).

**How it works:** Filter classes by namespace prefix in name, age, and zero-reference. Most are bulk-deletable.

---

## Decision Guidance

| Class state | Action | Reason |
|---|---|---|
| 0% coverage, 0 source refs, 0 metadata refs, no `@RestResource` | Delete | Pure dead weight on the denominator |
| 0% coverage, used by a Flow/button/REST mapping | Write test or document waiver | Active code; test debt is real debt |
| Low (<75%) coverage, actively referenced | Out of scope — see apex/test-class-standards | Different problem (improve tests) |
| 0% coverage, looks unused, but team uncertain | Mark `@deprecated`, deploy, watch one cycle | Cheap reversibility before destructive change |

---

## Recommended Workflow

1. Run a clean `sf apex run test --test-level RunLocalTests --code-coverage --result-format json` to refresh `ApexCodeCoverageAggregate`. Without a clean run, coverage data is unreliable.
2. Query orphan candidates: `SELECT ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered FROM ApexCodeCoverageAggregate WHERE NumLinesCovered = 0`.
3. For each candidate, search the source tree for references: name token in `.cls`, `.trigger`, `.flow-meta.xml`, `.weblink-meta.xml`, `.flexipage-meta.xml`, REST URL mappings.
4. Check metadata-only references: `aura:component`, LWC `@AuraEnabled` callers via `connectedCallback` patterns, Process Builder bindings.
5. Categorize each candidate: delete-safe, needs-test-to-stay, deprecated-but-kept-for-back-compat.
6. Build destructive-changes manifest for delete-safe classes. Deploy in sandbox first; verify no tests start failing because of compile-time references the search missed.
7. Promote to higher environments. Track org-wide coverage delta — should jump cleanly upward.

---

## Review Checklist

- [ ] Coverage data refreshed via clean local-tests run, not a stale snapshot
- [ ] Each candidate verified against four orphan criteria (coverage, source ref, metadata ref, REST entry)
- [ ] Sandbox deploy of the destructive manifest passes all tests
- [ ] Org-wide coverage measured before and after; delta documented
- [ ] Classes kept-but-untested have a tracked issue or `@deprecated` annotation

---

## Salesforce-Specific Gotchas

1. **Coverage queries reflect only the last run** — Skipping the clean test run before querying produces phantom orphans (and phantom keeps).
2. **REST endpoint classes have no Apex callers but are not orphans** — `@RestResource(urlMapping='/api/v1/things')` is invoked by an HTTP request, never by Apex. Filter by annotation before declaring orphan.
3. **Scheduled-job classes can be invoked from `System.schedule` calls in *other* classes or from Setup-only schedule entries** — Setup → Apex Jobs → Scheduled Jobs lists schedules that have no Apex caller record. Check before deleting any `Schedulable` class.
4. **Deleting a class fails if it's referenced by a Flow** — The destructive deploy returns a clear error, but only after the apparently-clean static check. Flow XML must be searched for `<actionName>ClassName</actionName>`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| orphan-candidates.csv | Class name, lines, last-modified date, reference-search summary |
| delete-safe.xml | destructiveChanges.xml for verified-orphan classes |
| keep-with-test.md | Classes that must stay, with the test gap they need |
| coverage-before-after.txt | Org-wide coverage delta proof |

---

## Related Skills

- apex/test-class-standards — for the actively-referenced classes that need a real test, not a deletion
- devops/destructive-changes-deployment — for safely shipping the delete manifest
- architect/technical-debt-assessment — when the orphan list is large enough to be a strategic conversation, not a tactical sweep
