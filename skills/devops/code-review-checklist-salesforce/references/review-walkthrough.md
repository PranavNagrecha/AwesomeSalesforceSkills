# Worked Review — one PR from checker run to findings table

A PR adds `OpportunityStamping` (a service called from an `Opportunity` trigger) and raises an existing helper class, `AccountLookup`, from API 62.0 to 67.0 "to use the newer Assert class in its test". The diff touches four files under `force-app/main/default/`.

## Step 1 — run the checker on the changed package directory

```bash
python3 skills/devops/code-review-checklist-salesforce/scripts/check_code_review_checklist_salesforce.py \
  --manifest-dir force-app/main/default
```

```text
ERROR: force-app/main/default/classes/AccountLookup.cls: WITH SECURITY_ENFORCED on an API 67.0 file; not allowed from 67.0, use WITH USER_MODE
WARN: force-app/main/default/classes/OpportunityStamping.cls: database operations but no sharing keyword; default is with sharing at 67.0+, caller-dependent before (API 67.0)
WARN: force-app/main/default/classes/OpportunityStamping.cls:14: SOQL or DML inside a for-loop body; collect ids and query/DML once
WARN: force-app/main/default/triggers/OpportunityTrigger.trigger: SOQL/DML in the trigger body; move logic to a handler class
Scanned 4 file(s): 1 error(s), 3 warning(s).
```

The ERROR is the version bump: `AccountLookup` compiled at 62.0 with `WITH SECURITY_ENFORCED`, and the same source does not compile at 67.0. The author did not change a single line of Apex in that file, which is exactly why a diff-only read misses it.

## Step 2 — the hand review the checker cannot do

| Area | What the reviewer read | Finding |
|---|---|---|
| Version defaults | `AccountLookup.cls-meta.xml` 62.0 → 67.0 | Beyond the compile error, its unqualified `Database.query` now runs in user mode; the integration user's permission set lacks read on `Account.Rating`. Blocking. |
| Bulk | `OpportunityStamping.stamp()` line 14 | One `Account` query per opportunity on top of the trigger's own query; crosses the 100-query synchronous limit partway through a 200-row chunk. Blocking. |
| Sharing | `OpportunityStamping` | No keyword; at 67.0 that means `with sharing`, which is the intended behaviour — ask the author to write `with sharing` so the intent survives a copy into an older class. Advisory. |
| Trigger | `OpportunityTrigger` | Inline `[SELECT ...]` before the handler call; move into the handler so ordering is explicit. Advisory (team practice). |
| Tests | `OpportunityStamping_Test` | Single-row insert, `Assert.areEqual` present, runs as the test-context user only. Ask for a 200-row method and a `System.runAs` as the Sales User persona. Blocking for the bulk method. |
| Deploy | `OpportunityStamping` is not `Schedulable`; no batch references | No job pause needed. |

## Step 3 — record the outcome

Copy the table into `templates/code-review-checklist-salesforce-template.md` under **Checklist**, mark three items blocking, and request changes. The second review round re-runs the checker; it must exit 0 with `--strict` off before the reviewer re-reads the hand-review rows.
