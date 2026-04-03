# Code Review Checklist

Use this as the master checklist for all Salesforce code reviews. The `/review` agent works through these in order.

Critical and High items are blockers. Medium items should be fixed before merge. Low items are tech-debt tracking.

---

## Security — Check First, Always

- [ ] **FLS on all SOQL reads** — `WITH SECURITY_ENFORCED` or `WITH USER_MODE` on every SOQL query in user-facing context
- [ ] **FLS on all DML writes** — `Security.stripInaccessible(AccessType.UPSERTABLE, ...)` before insert/update, or `Schema.sObjectType.[Object].fields.[Field].isUpdateable()` checks
- [ ] **No SOQL injection** — no string concatenation in dynamic SOQL; use bind variables or `String.escapeSingleQuotes()`
- [ ] **Sharing model respected** — class declared `with sharing` for user-context operations; `without sharing` only where documented and justified; if sub-operation needs elevation, use a `private inner class without sharing`, not the entire outer class
- [ ] **No hardcoded credentials** — no usernames, passwords, API keys, or tokens in code; use Named Credentials or Custom Metadata
- [ ] **No hardcoded org-specific IDs** — no RecordType IDs, Profile IDs, Queue IDs, User IDs; use `Schema.SObjectType.[Object].getRecordTypeInfosByDeveloperName()` for RecordType lookups
- [ ] **Sensitive data not logged** — no PII, financial data, or credentials in `System.debug` or custom logging
- [ ] **No `System.debug` in production code** — remove all debug statements before deployment; use a structured logging utility (custom object) for production logging
- [ ] **Unused `@AuraEnabled` methods removed** — every `@AuraEnabled` method is callable from the client and expands attack surface; remove or secure any no longer in use

### Permission Set / Profile Security (when reviewing metadata)
- [ ] **`viewAllRecords` / `modifyAllRecords` flagged on every object** — these bypass all OWD and sharing rules; every occurrence is a Must Fix unless explicitly documented
- [ ] **Dangerous system permissions flagged** — every instance of the following requires explicit justification:
  - `ViewAllData` — bypasses all sharing; sees every record in the org
  - `ModifyAllData` — bypasses all sharing; can edit/delete every record
  - `ManageUsers` — can create/deactivate users and assign profiles
  - `AuthorApex` — can write and deploy Apex code
  - `CustomizeApplication` — can change app configuration
  - `ManageAuthProviders` / `SingleSignOn` — can change identity/SSO config
- [ ] **API Enabled only where genuinely needed** — do not grant to community/portal profiles; integration users only
- [ ] **Community profiles have zero object CRUD permissions** — all object access goes on Permission Sets, not Profiles

---

## Governor Limits — Check Every Apex Component

- [ ] **No SOQL in loops** — zero queries inside `for` loops, including nested loops; queries belong before loops
- [ ] **No DML in loops** — all DML is on collections, not individual records
- [ ] **Bulkified for 200 records** — every trigger handler, batch, and service method works correctly at 200 records (Salesforce's bulk API batch size)
- [ ] **Async for heavy operations** — operations risking heap/CPU limits are async (Batch, Queueable, Future)
- [ ] **SOQL query count checked** — complex transactions shouldn't consume more than ~50 of the 100 query limit; leave headroom for callouts
- [ ] **Callout limits** — max 100 callouts per transaction; Batch uses `Database.AllowsCallouts` if needed

---

## Trigger Architecture

- [ ] **One trigger per object** — never two triggers on the same SObject
- [ ] **No logic in trigger body** — trigger body delegates to a handler class immediately
- [ ] **Trigger handler is stateless** — no instance variables that persist between calls
- [ ] **All trigger contexts handled explicitly** — handler has methods for each context used; unused contexts are not silently ignored
- [ ] **No SOQL or DML in trigger body** — always in the handler
- [ ] **Recursion guard in place** — static boolean or set-based guard prevents infinite re-entry; tested explicitly
- [ ] **Trigger activation is configurable** — trigger can be disabled via Custom Metadata or Custom Setting without a deployment (essential for data migrations)

---

## Test Classes

- [ ] **`@isTest` annotation present** — on both the class and each test method
- [ ] **`@isTest(SeeAllData=false)`** — never `SeeAllData=true` unless there's a documented reason
- [ ] **Test data created in test** — no reliance on org data; use a TestDataFactory
- [ ] **Meaningful assertions** — `System.assertEquals(expected, actual, 'message')` for every outcome; no `System.assert(true)`
- [ ] **Bulk test present** — at least one test method tests with 200+ records
- [ ] **Negative test present** — at least one test confirms the error/exception path
- [ ] **Coverage ≥ 85%** — org minimum is 75%, but 85% is the standard here
- [ ] **No test logic in production code** — no `if (Test.isRunningTest())` in non-test classes
- [ ] **Sharing tests use `System.runAs()`** — tests validating `with sharing` behaviour must run as a user with restricted permissions; running as admin does not validate sharing
- [ ] **Static variable isolation** — static variables (e.g. recursion guards) can persist across test methods; reset in `@TestSetup` or at the start of each test to prevent order-dependent failures

---

## LWC

- [ ] **`@api` properties are primitive types or plain objects** — no complex classes as `@api` inputs; never mutate `@api` properties (read-only from parent — clone before modifying)
- [ ] **Event listeners cleaned up** — `addEventListener` in `connectedCallback` has matching `removeEventListener` in `disconnectedCallback`
- [ ] **`renderedCallback` guarded** — one-time DOM setup uses a boolean guard (`if (!this._hasRendered)`) to prevent duplicate execution on every re-render
- [ ] **Wire adapter errors handled** — every `@wire` result checks `error` and `data` branches
- [ ] **No direct DOM manipulation** — use reactive properties and templates; no `document.getElementById`
- [ ] **Accessible** — interactive elements have `aria-label` or visible label; no color-only information conveying; images have alt text
- [ ] **Navigation uses `NavigationMixin`** — never `window.location.href` or `window.location.assign()` (breaks in Salesforce mobile and community)
- [ ] **User feedback uses `ShowToastEvent`** — never `alert()` (blocked in Lightning Experience)
- [ ] **No cross-component DOM access** — `this.template.querySelector()` only within this component's own template; accessing another component's shadow DOM breaks under Lightning Locker Service
- [ ] **External scripts via Static Resources** — no inline `<script>` or `<link>` tags in templates (blocked by Content Security Policy)
- [ ] **No `console.log` in production** — remove before deployment

---

## Flow

- [ ] **Fault connectors on all DML and callout elements** — every Get Records, Create, Update, Delete, Apex action, and HTTP callout has a fault path
- [ ] **Bulkified** — Record-Triggered Flows use bulk-safe patterns; no per-record SOQL in loops
- [ ] **Get Records has selective filters** — no "get all records" without WHERE conditions; unconstrained queries cause heap/row limit failures
- [ ] **Every Flow element has a Description** — label alone is not enough; description explains what the element does and why
- [ ] **Variables named descriptively** — no `variable1`, `tempCollection`; follow naming conventions
- [ ] **Formulas use `AND`/`OR`** — not `&&`/`||` (Flow formula syntax differs from Apex)
- [ ] **No duplicate automation** — verify no trigger or other flow on the same object/event does the same work; double-processing causes data inconsistency
- [ ] **Subflows for reusable logic** — logic repeated in multiple flows is extracted to a subflow
- [ ] **Screen Flows have error messages** — validation errors show human-readable messages, not raw Salesforce errors
- [ ] **Screen Flows have a reachable Finish/Cancel** — every screen has a navigable path out; no dead-end screens
- [ ] **No active old versions** — deploying a new version deactivates the previous; two active versions of the same flow is a bug

---

## Code Quality

- [ ] **Single responsibility** — each class/method does one thing
- [ ] **Cyclomatic complexity** — flag methods with high branch count; PMD CyclomaticComplexity > 10 is a refactor signal; break into private helper methods
- [ ] **No dead code** — commented-out code, unused variables, unreachable branches removed
- [ ] **Consistent naming** — follows `standards/naming-conventions.md`
- [ ] **No magic numbers** — hardcoded numeric values use named constants; prefer Custom Metadata over Custom Settings for config values
- [ ] **All picklists are Restricted Picklists** — prevents uncontrolled values entering the org through API or import
- [ ] **Error messages are human-readable** — catch blocks have meaningful messages; stack traces are logged but not exposed to users
- [ ] **Logging is structured** — log entries are queryable; avoid freeform `System.debug` as the only logging mechanism in production
- [ ] **`@SuppressWarnings` has inline justification** — any PMD suppression must have a comment explaining why it's acceptable; unjustified suppressions are a finding
- [ ] **API version is current** — Apex, LWC, and Flow metadata `apiVersion` within 3 major versions of org default; very old versions have different governor limits and deprecated APIs

---

## Integration

- [ ] **Named Credentials used** — no hardcoded endpoints or auth tokens
- [ ] **Callout errors handled** — `HttpResponse.getStatusCode() != 200` paths have explicit handling
- [ ] **Retry logic exists for transient failures** — or retry is documented as out of scope with reasoning
- [ ] **Timeout configured** — `HttpRequest.setTimeout()` set explicitly; default is 10s which may be insufficient
- [ ] **Callout in async context** — callouts not blocking synchronous user-facing transactions where avoidable
- [ ] **`@future` methods take primitives only** — never pass SObjects to `@future`; they are serialized by reference and may be stale; pass IDs and re-query inside the method
- [ ] **Partial DML results inspected** — when using `Database.insert/update/delete` with `allOrNone=false`, iterate `SaveResult[]`/`DeleteResult[]`, check `isSuccess()`, and handle failures; silent partial failures are data corruption
- [ ] **IP restrictions on integration profiles** — API/integration-only user profiles should have Login IP Ranges configured; unbound accounts accessible from any IP

## OmniStudio (when reviewing OmniStudio components)

- [ ] **Integration Procedure root config** — `rollbackOnError: true`, `chainableQueriesLimit: 50`, `chainableCpuLimit: 2000` in `propertySetConfig`
- [ ] **No placeholder error messages** — no "Business approved verbiage" or "TBD" in `failureResponse`; real messages only
- [ ] **HTTP actions have timeout** — `restOptions` includes explicit timeout (e.g. 30 seconds)
- [ ] **`failOnStepError` configured** — no silent step failures; error state propagates to the calling FlexCard or OmniScript
- [ ] **All callouts use Named Credentials** — no hardcoded URLs, secrets, or tokens in Integration Procedures
- [ ] **Every component has a meaningful description** — not just the component name; explains purpose, owner, what it does

---

## Finding Severity Reference

| Severity | Definition | Action |
|----------|-----------|--------|
| 🔴 Critical | Data exposure, data loss, or guaranteed production failure | Block merge. Fix before any further review. |
| 🟠 High | Likely failure under real-world conditions (bulk load, concurrent users) | Block merge. Fix in this PR. |
| 🟡 Medium | Degrades quality, maintainability, or future scalability | Fix in this sprint. Can merge with documented plan. |
| 🔵 Low | Cosmetic, style, or minor tech debt | Log as tech debt. Fix opportunistically. |
