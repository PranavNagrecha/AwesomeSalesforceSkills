# Gotchas — NPSP Trigger Framework Extension (TDTM)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: NPSP Upgrade Silently Deletes Custom Handler Records

**What happens:** After an NPSP package upgrade, custom `npsp__Trigger_Handler__c` records disappear with no error message, deploy warning, or post-install notification. The feature the handler implemented stops working silently.

**When it occurs:** When `npsp__Owned_by_Namespace__c` is blank or set to `npsp` on the custom handler record. The NPSP upgrade script treats records in that namespace as package-owned and deletes them as part of its standard post-install cleanup routine.

**How to avoid:** Always set `npsp__Owned_by_Namespace__c` to your org's namespace (e.g. `myorg`) or to any non-`npsp` sentinel string such as `custom`. Add a post-upgrade monitoring query to your deployment runbook:

```soql
SELECT Id, Name, npsp__Class__c, npsp__Active__c
FROM npsp__Trigger_Handler__c
WHERE npsp__Owned_by_Namespace__c != 'npsp'
ORDER BY npsp__Load_Order__c
```

Run this query after every NPSP upgrade to confirm custom handlers still exist.

---

## Gotcha 2: getTdtmConfig() Cache Bug Causes Custom Handler to Be Silently Skipped in Tests

**What happens:** In a test class, calling `npsp.TDTM_Global_API.getTdtmConfig()` before `setTdtmConfig()` causes the custom handler to never execute during the test — even though `setTdtmConfig()` was called with the correct handler list. The test passes, asserting no records were created (or not asserting at all), and the handler is never actually validated.

**When it occurs:** When a developer follows the pattern of "get the existing list, add the custom handler, set it back." The `getTdtmConfig()` call populates an internal static cache with the packaged handler configuration. The subsequent `setTdtmConfig()` call attempts to register the custom handler, but the cache entry for that class name is already bound to the packaged state. The dispatcher then uses the cached packaged list and ignores the custom handler.

**How to avoid:** Never call `getTdtmConfig()` in a test context before `setTdtmConfig()`. Build the handler list from scratch as a `List<npsp__Trigger_Handler__c>` and pass it directly:

```apex
// CORRECT
List<npsp__Trigger_Handler__c> handlers = new List<npsp__Trigger_Handler__c>{
    new npsp__Trigger_Handler__c(
        npsp__Class__c = 'MyCustomHandler',
        npsp__Object__c = 'Contact',
        npsp__Trigger_Action__c = 'AfterInsert',
        npsp__Load_Order__c = 100,
        npsp__Active__c = true
    )
};
npsp.TDTM_Global_API.setTdtmConfig(handlers);

// WRONG — do not call getTdtmConfig() first
// List<npsp__Trigger_Handler__c> handlers = npsp.TDTM_Global_API.getTdtmConfig();
// handlers.add(...);
// npsp.TDTM_Global_API.setTdtmConfig(handlers);
```

---

## Gotcha 3: Direct DML Inside run() Causes Recursive TDTM Dispatch

**What happens:** Any `insert`, `update`, or `delete` statement executed directly inside the `run()` method fires that object's Apex trigger pipeline, which includes the NPSP TDTM dispatcher. This re-enters the dispatcher mid-execution, can fire the same handlers a second time, and compounds governor limit usage — DML rows, CPU time, and SOQL queries all double for that object's handlers.

**When it occurs:** When a developer treats TDTM's `run()` like a standard trigger handler body and issues DML directly, unaware that NPSP's design contract requires all DML to be returned via `DmlWrapper`.

**How to avoid:** Return all records to create, update, or delete via the `DmlWrapper` return value. NPSP's dispatcher collects `DmlWrapper` objects from every handler in the chain and issues one batched DML after the chain completes. The DmlWrapper fields are:
- `wrapper.objectsToInsert` — `List<SObject>`
- `wrapper.objectsToUpdate` — `List<SObject>`
- `wrapper.objectsToDelete` — `List<SObject>`

---

## Gotcha 4: npsp__Trigger_Action__c Must Be Semicolon-Delimited With No Spaces

**What happens:** If multiple trigger actions are listed with spaces around the semicolons (e.g. `AfterInsert ; AfterUpdate`) or with a trailing semicolon, the TDTM dispatcher fails to parse the value correctly and the handler may fire on none of the intended actions, or only on the first.

**When it occurs:** When the handler registration record is created manually in Setup UI or via a data loader export/import that introduces whitespace.

**How to avoid:** Use exactly `AfterInsert;AfterUpdate` (no spaces, no trailing semicolon). Valid action names: `BeforeInsert`, `BeforeUpdate`, `BeforeDelete`, `AfterInsert`, `AfterUpdate`, `AfterDelete`, `AfterUndelete`.

---

## Gotcha 5: Load Order Collisions With Packaged Handlers Cause Unpredictable Execution

**What happens:** If a custom handler is assigned the same `npsp__Load_Order__c` value as a packaged NPSP handler on the same object, execution order between them is undefined. In some versions of NPSP, this results in the custom handler running before package handlers have established relationship state (e.g., payment records not yet created when the custom Opportunity handler checks for them).

**When it occurs:** When a developer sets `npsp__Load_Order__c` to a low number (1–50) without querying existing handler records first.

**How to avoid:** Always query `npsp__Trigger_Handler__c` for the target object before assigning load order:

```soql
SELECT npsp__Class__c, npsp__Load_Order__c
FROM npsp__Trigger_Handler__c
WHERE npsp__Object__c = 'Opportunity'
ORDER BY npsp__Load_Order__c ASC
```

Start custom handlers at 100 and increment by 10 for each additional custom handler on the same object.
