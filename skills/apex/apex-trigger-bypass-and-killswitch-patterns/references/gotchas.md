# Gotchas — Apex Trigger Bypass And Killswitch Patterns

Non-obvious Salesforce platform behaviours that bite real production rollouts
of bypass and kill-switch patterns.

## Gotcha 1: Custom Metadata cache lag after deploy

**What happens:** You deploy a `Trigger_Setting__mdt` record with
`Is_Active__c = false` to disable a handler. The next user transaction still
sees `Is_Active__c = true` and the trigger fires.

**When it occurs:** Immediately after a CMDT deployment. The platform caches
Custom Metadata at the application server tier; propagation across servers
can take a few seconds.

**How to avoid:**
- After deploying a kill-switch flip, wait ~10–30s before declaring
  the handler disabled.
- For incident response, prefer the Custom Permission lever (Permission Set
  assignment is effective immediately for new transactions).
- Verify the bypass took effect by issuing a test DML and checking the
  audit log entry — do not assume the deploy is enough.

---

## Gotcha 2: TriggerControl static state does not survive transaction boundaries

**What happens:** Code calls `TriggerControl.bypass('Account',
'AccountTriggerHandler')`, then enqueues a Queueable that updates Accounts.
The Queueable's Account update fires `AccountTriggerHandler` — the bypass
"didn't take".

**When it occurs:** Any time bypass state lives in a static variable and
work is offloaded to Queueable, `@future`, Batch, Schedulable, Platform Event
trigger, or Change Data Capture trigger — each starts a new transaction with
fresh static state.

**How to avoid:**
- Re-call `TriggerControl.bypass(...)` at the top of `Queueable.execute(...)`
  if the bypass should continue.
- Or pass the bypass intent through the Queueable's constructor and have
  the Queueable apply it explicitly.
- For org-wide bypass during a long-running batch, use the CMDT lever, not
  static state.

---

## Gotcha 3: FeatureManagement.checkPermission is the canonical Custom Permission API

**What happens:** Practitioners write SOQL against `SetupEntityAccess` /
`PermissionSet` to check if the running user has a Custom Permission. The
query consumes a SOQL governor row, often misses Permission Set Groups, and
is slow.

**When it occurs:** Code reviews catch this — but unreviewed handler code
sometimes ships with the SOQL pattern.

**How to avoid:** Use `System.FeatureManagement.checkPermission('Api_Name')`.
It is documented, governor-free, and respects Permission Set Groups.
Reference:
https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm

---

## Gotcha 4: Hierarchy Custom Setting lookup order is User → Profile → Org Default

**What happens:** Admin sets the org-default Hierarchy CS to "bypass = true"
intending to disable a handler temporarily. They forget to set it back to
false. A week later all users are silently bypassing the trigger.

**When it occurs:** Hierarchy CS reads return the most-specific match: the
running user's row, then the user's profile row, then the org default row.
If only org default is set, every user gets the bypass.

**How to avoid:**
- Prefer CMDT for org-wide kill switches (auditable in deployment history).
- Prefer Custom Permission + Permission Set for per-user bypass (auditable
  in Setup Audit Trail).
- Reserve Hierarchy CS bypass for short-lived per-profile overrides, and
  document the revert step in a runbook.

---

## Gotcha 5: Test.isRunningTest() guards mask real coverage gaps

**What happens:** Trigger code wraps logic in
`if (!Test.isRunningTest()) { ... }`. Tests pass green but never exercise
the production path.

**When it occurs:** Most often around outbound callouts that the developer
"didn't want to mock". The bypass becomes permanent.

**How to avoid:** Never gate business logic on `Test.isRunningTest()`. Mock
the callout via `HttpCalloutMock`. Use `TriggerControl.overrideForTest(...)`
only inside test methods that explicitly verify the bypass path.
