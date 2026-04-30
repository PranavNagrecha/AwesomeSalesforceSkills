# Gotchas — Code Coverage Orphan Class Cleanup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ApexCodeCoverageAggregate is a snapshot, not a history

**What happens:** A class shows 0% coverage in the table even though tests covered it last week.

**When it occurs:** The latest test run was incomplete or skipped the class because a compile failure elsewhere blocked it.

**How to avoid:** Run `sf apex run test --test-level RunLocalTests --code-coverage` to refresh the snapshot before treating zero-coverage as orphan evidence.

---

## Gotcha 2: REST endpoint classes look orphan

**What happens:** A class annotated `@RestResource(urlMapping='/api/things')` has no Apex callers; static grep returns nothing. It is not orphan — it is an external entry point.

**When it occurs:** Any custom REST endpoint, especially older `@HttpGet` / `@HttpPost` patterns.

**How to avoid:** Pre-filter candidates: drop any class containing `@RestResource`, `@HttpGet`, `@HttpPost`, `@HttpPut`, `@HttpPatch`, or `@HttpDelete` before destructive deploy.

---

## Gotcha 3: Flow-invoked Apex actions don't show in source grep on `.cls`

**What happens:** A class has zero Apex callers. It is referenced from a Flow as `<actionName>OldDiscountEngine</actionName>`. Destructive deploy fails on Flow-dependency check.

**When it occurs:** Any Apex class invocable from Flow / Process Builder.

**How to avoid:** Search Flow XML and Process Builder XML in addition to Apex source. `grep -rln "<actionName>${CLASS}</actionName>" force-app/main/default/flows`.

---

## Gotcha 4: Scheduled jobs reference classes only in Setup, not in source

**What happens:** Setup → Apex Jobs → Scheduled Jobs lists `OldDiscountEngine` running every Sunday at 3am. Source has no `System.schedule(...)` call.

**When it occurs:** Whenever the schedule was created via Anonymous Apex, Setup UI, or a now-deleted bootstrap class.

**How to avoid:** Query `CronTrigger` (Tooling/SOAP API) and check if any active schedule references your candidate class. `SELECT Id, CronJobDetail.Name FROM CronTrigger WHERE State = 'WAITING'`.

---

## Gotcha 5: Managed-package code with namespace shows in queries but is excluded from coverage

**What happens:** A query against `ApexCodeCoverageAggregate` returns managed-package classes you can't delete and aren't in the org-wide coverage denominator anyway.

**When it occurs:** Any installed managed package.

**How to avoid:** Filter `WHERE ApexClassOrTrigger.NamespacePrefix = NULL` in your orphan query. Managed code coverage is the package vendor's problem.
