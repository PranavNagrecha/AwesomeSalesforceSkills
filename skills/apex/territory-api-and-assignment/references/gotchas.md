# Gotchas — Territory API and Assignment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex Triggers Do Not Fire on ObjectTerritory2Association

**What happens:** An Apex trigger declared on `ObjectTerritory2Association` (for any DML event: `before insert`, `after insert`, `before delete`, `after delete`) deploys successfully without any compile-time or deploy-time warning, but the trigger body is **never executed** — not when inserted via Apex DML, not when inserted via the Setup UI, and not when inserted by assignment rule evaluation.

**When it occurs:** Any time a practitioner creates a trigger on `ObjectTerritory2Association` expecting it to fire on insert, update, or delete of territory-account association records.

**How to avoid:** Do not write triggers on `ObjectTerritory2Association`. To react to territory-account associations, dispatch a Platform Event from the Apex code that performs the `ObjectTerritory2Association` DML, then subscribe to that event in a trigger or flow to perform downstream processing.

---

## Gotcha 2: UserInfo.getSessionId() Returns Null in Async Apex

**What happens:** Any code that calls `UserInfo.getSessionId()` and uses the result as an Authorization header for a SOAP callout (required for ETM assignment rule evaluation) receives a `null` value in asynchronous Apex contexts. The subsequent callout fails with a `CalloutException` (if null is passed as a header value) or produces an authentication error from the Salesforce SOAP endpoint.

**When it occurs:** Inside Batch Apex `execute` or `start`, inside a `@future` method, inside a Queueable `execute`, and inside Scheduled Apex `execute`. This includes calls made from these contexts even through helper methods that internally use `getSessionId()`.

**How to avoid:** Only invoke SOAP-based rule evaluation from synchronous request contexts where a session is genuinely available: synchronous Apex controller methods, REST API endpoint handlers (`@RestResource` classes called via HTTP), or Visualforce action methods. For batch-triggered rule evaluation, use a Platform Event published in the batch `finish` method to signal a synchronous subscriber (trigger or flow) to perform the callout.

---

## Gotcha 3: Assignment Rules Do Not Re-Evaluate Automatically on Account Field Updates or ObjectTerritory2Association DML

**What happens:** When an Account's `BillingState`, `Industry`, or any other field referenced in an ETM assignment rule is updated, the account's territory assignments are **not recalculated automatically**. Similarly, inserting or deleting `ObjectTerritory2Association` records does not trigger rule re-evaluation. Accounts silently remain in their previous territory assignments until a rule evaluation is explicitly requested.

**When it occurs:** Any time Account fields that drive territory rules are updated via DML (trigger, batch, integration), and any time an `ObjectTerritory2Association` record is manually inserted or deleted. Both operations complete silently without rule recalculation.

**How to avoid:** After updating Account fields that affect rule criteria, explicitly call the SOAP-based rule evaluation endpoint (chunked to ≤200 IDs per call, from a synchronous context). Do not assume the platform will self-correct territory assignments over time — there is no background re-evaluation mechanism.

---

## Gotcha 4: ObjectTerritory2Association DML with AssociationCause = 'Territory2RuleAssociation' Throws a Runtime Error

**What happens:** Attempting to insert an `ObjectTerritory2Association` record with `AssociationCause = 'Territory2RuleAssociation'` throws a runtime `DmlException: FIELD_INTEGRITY_EXCEPTION`. The `Territory2RuleAssociation` cause value is reserved for the platform and can only be set by the rule evaluation engine — it cannot be set via Apex DML.

**When it occurs:** When a practitioner queries an existing rule-based association (which has `AssociationCause = 'Territory2RuleAssociation'`), clones the sObject, and attempts to re-insert it — for example, in a migration that copies associations between territory models.

**How to avoid:** Always set `AssociationCause = 'Territory'` explicitly when inserting `ObjectTerritory2Association` records from Apex. Never copy the `AssociationCause` from a queried record without checking its value. If rule-based associations need to be replicated, trigger rule re-evaluation via SOAP rather than copying the association records directly.

---

## Gotcha 5: ETM DML Fails When No Territory2Model Is in Active State

**What happens:** DML on `UserTerritory2Association` and `ObjectTerritory2Association` results in a runtime error when no `Territory2Model` is in `Active` state. This is most commonly encountered in sandbox refreshes (where the active model may not be re-activated automatically), during ETM model transitions (when the current active model is archived before a new one is activated), or in developer orgs where ETM is enabled but no model has ever been activated.

**When it occurs:** During sandbox refresh, during ETM model version upgrades, or in any org where ETM is technically enabled but no model is currently Active.

**How to avoid:** Guard automation and migration scripts with a pre-check that queries `Territory2Model WHERE State = 'Active' LIMIT 1` and exits gracefully (with a log message rather than a hard exception) if no active model is found. Include this check in test setup and deployment runbooks.

---

## Gotcha 6: SOAP Rule Evaluation Is Capped at 200 Account IDs Per Request

**What happens:** Passing more than 200 Account IDs in a single SOAP call to the ETM rule evaluation endpoint returns a SOAP fault. The operation does not partially succeed — all IDs in the oversized request are rejected.

**When it occurs:** During migrations or realignments where rule evaluation must be triggered for thousands of accounts in a single operation.

**How to avoid:** Always chunk the account ID list into groups of at most 200 before making SOAP calls: `for (Integer i = 0; i < accountIds.size(); i += 200) { List<Id> chunk = accountIds.subList(i, Math.min(i + 200, accountIds.size())); ... }`. Be aware that each SOAP call also counts against the per-transaction callout limit (100 callouts per transaction), so very large batches must be spread across multiple transactions.
