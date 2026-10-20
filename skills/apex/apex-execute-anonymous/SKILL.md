---
name: apex-execute-anonymous
description: "Execute Anonymous Apex: Developer Console, VS Code SFDX, `sf apex run`, variable scope, transaction semantics, governor limits, debugging output, common errors. NOT for trace flags or reading the log output — use apex/debug-logs-and-developer-console. NOT for async job design — use apex/async-apex."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - apex
  - execute-anonymous
  - sfdx
  - developer-console
  - debugging
triggers:
  - "execute anonymous apex vscode sf apex run"
  - "anonymous apex script transaction commit rollback"
  - "execute anonymous variable scope system.debug"
  - "sf apex run file script.apex cli"
  - "execute anonymous governor limits per run"
  - "anonymous apex cannot call test methods"
  - "anonymous apex production dry run safeguard transaction"
inputs:
  - Script purpose (one-off data fix, investigation, etc.)
  - Target org
  - Data scope (records affected)
outputs:
  - Anonymous Apex script (.apex file)
  - CLI invocation command
  - Rollback plan (if DML)
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Execute Anonymous

Activate when running ad-hoc Apex — investigation, data fixes, one-off operations. Execute Anonymous commits DML on success (unlike tests), runs as the authenticated user, and surfaces errors via debug logs. Misunderstand any of these and you'll destroy data or corrupt a production org.

## Before Starting

- **Confirm org and user.** `sf org display` — especially before running against production.
- **Plan rollback.** Anonymous Apex commits by default. Add `Database.setSavepoint`/`Database.rollback` for reversibility.
- **Estimate record volume.** Anonymous runs the full governor budget once; bulk work past ~10k records must be Batch-ified.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which org, and which user will run the script? | The block runs with that user's sharing, CRUD and FLS, so an admin-tested script can fail or return zero rows for someone else (gotcha 1). | A rehearsal in a sandbox as the same user or permission set. |
| How many records will it read and write? | Per-transaction limits apply in full: 150 DML statements, 10,000 DML rows, 50,000 query rows (gotcha 3). | The anonymous-vs-Batch decision before the script is written. |
| How large are the collections it holds? | Heap is 10 MB synchronous from Winter '27, but during Winter '27 a nonproduction org with `enableEnforceSummer26ApexHeapLimit` set still enforces the Summer '26 6 MB limit (gotcha 3). | A heap estimate checked in an org with the same heap setting as the target. |
| Must the change be reversible, and how? | It commits on success, and a savepoint does not survive a governor-limit fault (gotcha 3). | A dry-run toggle or savepoint plus a pre-state export. |
| How much debug output will it write, at what log level? | A log over 20 MB loses older lines, from anywhere in the log, and can lose the summary you need (gotcha 2). | Explicit debug levels and one summary line per run. |
| Is this one script, or several runs that share state? | Nothing persists between `executeAnonymous` calls (gotcha 4). | One self-contained script, or state persisted to a record between runs. |
| Does it start Batch or Queueable work, and who confirms it finished? | The script returns before async jobs run (gotcha 5). | The captured job ID and an `AsyncApexJob` check in the runbook. |

Answering these first turns a one-off script into a rehearsed, bounded and reversible change, where running it ad hoc risks committing partial data under the wrong user.

## Core Concepts

### Script structure

```
// my-fix.apex
List<Account> accs = [SELECT Id, Rating FROM Account WHERE Rating = null LIMIT 200];
for (Account a : accs) a.Rating = 'Warm';
update accs;
System.debug('Updated ' + accs.size());
```

### CLI invocation

```
sf apex run --target-org prod --file scripts/my-fix.apex
```

Output streams the debug log. Errors appear inline.

### Transaction semantics

- **Auto-commits on success.** No implicit savepoint.
- **Rolls back on uncaught exception.** Partial DML is reverted.
- **Can wrap manually** with `Database.setSavepoint()` + `Database.rollback(sp)`.

### Variable scope

Variables declared at the top live for the whole anonymous script. No `class` wrapper; the whole script runs inside an implicit `System.runUpdate`-like anonymous block.

### What you CAN'T do

- Declare a `static` method. User-defined methods and exceptions are allowed in the block, but they can't use the keyword `static` (Apex Developer Guide 264, Anonymous Blocks, L14988-L14989).
- Run test classes (`Test.startTest` is legal but you can't `@IsTest`-annotate code).
- Get anything from access modifiers: `global` is legal but has no meaning, because the block has local scope (L14995-L14996).
- Access protected members of a class outside its namespace.

### Debug output

`System.debug()` goes to the user's debug log. For `sf apex run`, the log returns to stdout. Set `Apex Code` log level to `FINE` or `FINEST` for variable values.

## Common Patterns

### Pattern: Savepoint-guarded data fix

```
Savepoint sp = Database.setSavepoint();
try {
    List<Contact> cs = [SELECT Id, Email FROM Contact WHERE Email LIKE '%@old.com' LIMIT 200];
    for (Contact c : cs) c.Email = c.Email.replace('@old.com', '@new.com');
    update cs;
    System.debug('Updated ' + cs.size());
    // Flip commented lines to actually apply:
    Database.rollback(sp);
} catch (Exception e) {
    Database.rollback(sp);
    System.debug(e);
}
```

Pattern: run with rollback first to see effect; flip to commit after review.

### Pattern: Iteration-bounded cleanup

```
Integer MAX = 200;
List<Case> oldCases = [SELECT Id FROM Case WHERE Status = 'Closed' AND IsDeleted = false LIMIT :MAX];
if (oldCases.size() == MAX) {
    System.debug('Limit hit — run again or use Batch Apex');
}
delete oldCases;
```

### Pattern: Dry-run toggle

```
Boolean APPLY = false;
// ... build list of updates
System.debug('Would update ' + updates.size() + ' records');
if (APPLY) update updates;
```

## Decision Guidance

| Task | Approach |
|---|---|
| Fix <200 records one-off | Execute Anonymous with savepoint |
| Fix 200–10,000 records | Execute Anonymous with batching loop + savepoint per iteration |
| Fix >10,000 records | Batch Apex — anonymous hits governor limits |
| Investigation (no DML) | Execute Anonymous; no savepoint needed |
| Scheduled/repeated fix | Schedulable/Batch; not anonymous |
| Test a method | Test class, not anonymous |

## Recommended Workflow

1. Confirm org with `sf org display --target-org <alias>` — especially before prod.
2. Write script with dry-run toggle OR savepoint + rollback first.
3. Run via `sf apex run --file script.apex --target-org <alias>`.
4. Inspect debug log output for the counts/side-effects.
5. Flip apply flag OR comment out the rollback, re-run.
6. Archive the script in a `scripts/` directory committed to version control.
7. For production, require peer review before `--target-org prod`.

## Review Checklist

- [ ] Target org confirmed explicitly (never rely on default config for prod)
- [ ] Savepoint or dry-run toggle present for DML scripts
- [ ] Record count bounded via `LIMIT` clause
- [ ] Debug output includes before/after counts
- [ ] Script saved to repo for audit trail
- [ ] Peer review for any production anonymous script

## Salesforce-Specific Gotchas

1. **Anonymous Apex commits on success. There is no implicit savepoint.** A runaway loop will destroy data before you can interrupt.
2. **`sf apex run` without `--file` reads from stdin** — useful for piped commands but easy to confuse with execution against stdin-EOF.
3. **Governor limits are per-execution, not per-statement.** A 50k-record loop inside anonymous hits CPU/DML-row caps. Use Batch for volume.
4. **Declaring a `static` method fails:** user-defined methods are allowed in an anonymous block, but not with the keyword `static` (Apex Developer Guide 264, L14988-L14989). Drop `static`, or wrap reusable logic in an inner class and call `new MyInner().doThing()`.
5. **Debug log level affects output.** If you see `System.debug()` lines missing, raise `Apex Code` to `FINE`.

## Output Artifacts

| Artifact | Description |
|---|---|
| `scripts/*.apex` | Committed scripts under version control |
| CLI runbook | `sf apex run` invocation + expected output |
| Rollback playbook | How to revert if DML committed unintended changes |

## Related Skills

- `apex/apex-savepoint-and-rollback` — transactional control details
- `apex/batch-apex-patterns` — for volume fixes
- `apex/sf-cli-and-sfdx-essentials` — CLI fundamentals (org auth, `sf` basics)
- `devops/salesforce-cli-automation` — scripting `sf apex run` in CI with `--json` and aliases
