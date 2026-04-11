# Gotchas — FSC Apex Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: FSC Rollup Recalculation Is Silent After Bulk DML

**What happens:** When Financial Account or Financial Account Transaction records are inserted or updated via Bulk API, Data Loader, or any batch process that bypasses the normal transactional Apex trigger chain at volume, FSC rollup fields (household net worth, total assets, liability totals) are not updated. The fields silently retain their prior values. No exception is thrown and no log entry indicates the rollup was skipped.

**When it occurs:** Any DML that routes through Bulk API 2.0, legacy Bulk API, or a custom Apex `Database.executeBatch` that does not explicitly invoke rollup recalculation afterward. This is most commonly encountered during initial data migrations, nightly data feeds from core banking systems, or integration jobs that use chunked inserts to stay under governor limits.

**How to avoid:** After any bulk load of `FinServ__FinancialAccount__c`, `FinServ__FinancialAccountTransaction__c`, or `FinServ__FinancialGoal__c` records, explicitly invoke `Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200)`. Chain this as a post-load step in your migration runbook or integration pipeline. Do not assume the scheduled nightly batch is sufficient — it introduces a window of stale data that is unacceptable in production financial environments.

---

## Gotcha 2: Compliant Data Sharing Silently Deletes Manually Inserted Share Records

**What happens:** An Apex class inserts an `AccountShare` or `FinancialAccountShare` record to grant a user access to a CDS-governed record. The insert succeeds and SOQL confirms the share record exists. Hours or days later, the user loses access. Querying the share table shows the record is gone. No DML error, no exception, no workflow action — the record was simply deleted by the CDS recalculation job.

**When it occurs:** Any time manual Apex sharing DML is used on an object governed by Compliant Data Sharing. CDS recalculation runs on a schedule (by default, nightly) and also runs immediately when participant model changes occur. On its run, it evaluates all share records on governed objects. Share records whose `RowCause` is not `CompliantDataSharing` are outside the CDS model and are removed as orphans.

**How to avoid:** Never insert share records directly on CDS-governed objects. Instead, insert `FinServ__ShareParticipant__c` records with the appropriate `FinServ__ShareRole__c` to register the user in the CDS participant model. The CDS engine will generate and maintain the share records. To verify that an object is CDS-governed, check `Setup > Compliant Data Sharing > Object Settings` or query `FinServ__CdsObjectConfig__mdt`.

---

## Gotcha 3: Managed Package API Version Lock Causes Runtime TypeException

**What happens:** Custom Apex at the org's current API version calls a method on an FSC managed package class, passing an argument whose type was introduced in a Salesforce API version newer than the package's compiled version. The code deploys and passes compilation. At runtime, the managed package method cannot resolve the type and throws a `System.TypeException` or a method-not-found error that looks like a generic internal error.

**When it occurs:** This most commonly surfaces after a Salesforce release upgrades the org's maximum API version but the FSC package has not yet released an updated version compiled against the new API. The gap can persist for one to two Salesforce release cycles. It also occurs when custom code uses newer platform Apex types — newer `Schema` methods, `FlexQueue` APIs, or new sObject subtypes — and passes those to FSC managed methods.

**How to avoid:** Test all FSC Apex extension changes in a full-copy or partial-copy sandbox that mirrors the production FSC package version exactly. Developer Edition orgs often have different package versions than production. Before using a newer platform type in code that calls FSC managed classes, check the FSC package's compiled API version in `Setup > Installed Packages > Financial Services Cloud > View Components` and compare it against the API version of the type you are using.

---

## Gotcha 4: FinServ__TriggerSettings__c Default Values Are Not Set in Test Context

**What happens:** A trigger handler reads `FinServ__TriggerSettings__c.getInstance()` to check whether an FSC trigger should be skipped. In the production org, the setting has a record with all relevant flags set to `true`. In test execution, `getInstance()` returns an empty object with all Boolean fields defaulting to `false`. Code that checks `if (ts.FinServ__AccountTrigger__c == true)` skips trigger logic that should run, causing test assertions to fail or tests to pass for the wrong reason.

**When it occurs:** Any test class that exercises code paths reading `FinServ__TriggerSettings__c` without explicitly inserting a test record for that setting. This is particularly insidious in integration tests that call trigger handlers indirectly, because the setting's absence does not throw an exception — it silently changes the code path.

**How to avoid:** In `@TestSetup`, always insert a `FinServ__TriggerSettings__c` record explicitly with the flags your code depends on set to their expected production values. Example: `insert new FinServ__TriggerSettings__c(SetupOwnerId = UserInfo.getOrganizationId(), FinServ__AccountTrigger__c = true);`

---

## Gotcha 5: RollupRecalculationBatchable Batch Size Above 200 Causes CPU Limit Errors on Complex Household Graphs

**What happens:** A developer invokes `FinServ.RollupRecalculationBatchable` with a batch size of 2000 (a common default for generic batch jobs). For orgs with complex household graphs — households with many members, joint accounts across multiple households, trust relationships, and professional group memberships — the batch hits the 10-second CPU time limit and the batch chunks fail with `System.LimitException: Apex CPU time limit exceeded`.

**When it occurs:** Specifically with FSC rollup recalculation on orgs where household graphs have more than ~20 related FinancialAccount records per household, or where a single account participates in multiple group rollup relationships. Standard batch default sizes (1000–2000) are too large for this query-heavy rollup logic.

**How to avoid:** Always invoke `FinServ.RollupRecalculationBatchable` with an explicit batch size of 200 or lower: `Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200)`. If CPU limit errors persist at 200, reduce to 50 and profile which household graph structures are causing the overhead. The FSC Admin Guide documents 200 as the recommended batch size for rollup recalculation.
