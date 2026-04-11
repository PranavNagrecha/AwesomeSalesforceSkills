# Well-Architected Notes — Health Cloud Apex Extensions

## Relevant Pillars

### Security

Health Cloud Apex extensions operate on clinical data that is PHI under HIPAA. Security considerations are non-negotiable:

- Debug log governance: Apex debug logs containing clinical object field values (`EhrPatientMedication`, `PatientHealthCondition`, `ClinicalEncounterCode`) constitute PHI exposure. Production logging must be disabled by default, time-limited when enabled, and purged after use.
- Consent enforcement: All care plan and referral operations must route through Health Cloud's invocable action layer, which evaluates `AuthorizationFormConsent`. Bypassing this layer with direct DML is a compliance failure, not just a functional bug.
- FLS and CRUD: Clinical Apex classes must enforce field-level security and CRUD via `WITH SECURITY_ENFORCED` SOQL or `Security.stripInaccessible()`. The Health Cloud managed package does not automatically enforce FLS for queries made in customer-authored extension classes.

### Performance Efficiency

- Callback methods (`CarePlanProcessorCallback`) execute within the managed-package transaction. Long-running operations in the callback will breach governor limits for the overall transaction. Heavy logic must be delegated to `@future` or Queueable Apex.
- Invocable action calls from Apex (`Invocable.Action`) count against DML and SOQL governor limits. Bulk care plan or referral operations must batch action invocations rather than calling them in a loop.
- Clinical SOQL queries should use selective filters (patient Id, date ranges) and avoid full-table scans on large objects like `EhrPatientMedication`.

### Reliability

- Callback registration in Health Cloud Setup is a manual post-deploy step. Without it, callbacks silently do nothing — there is no automatic rollback or error. Deployment runbooks must include this step.
- Invocable action results must be evaluated for errors. An action call that returns `isSuccess() == false` without throwing an exception will silently fail unless the code explicitly checks the result.
- Test coverage for callback implementations should use Health Cloud test data factories and mock action responses rather than relying on actual managed-package behavior in test context.

### Operational Excellence

- Establish a HIPAA debug log purge policy with automated enforcement (e.g., a scheduled Apex job that deletes debug log records via the Tooling API on a schedule).
- Maintain a deployment runbook that includes Setup registration steps for callback classes — these cannot be scripted through standard metadata deployments.
- Use Custom Metadata Type (`DebugSettings__mdt`) to control debug logging across environments without code deploys.

---

## Architectural Tradeoffs

**Callback vs. Trigger for Care Plan Lifecycle:** The `CarePlanProcessorCallback` interface fires within the managed-package lifecycle and is the correct extension point. An Apex trigger on `CarePlan` fires on raw DML but misses managed-package internal transitions. For lifecycle automation, always prefer the callback. Accept the tradeoff: the callback requires a manual Setup registration step that a trigger does not.

**Invocable Action vs. Direct DML:** Invocable actions enforce consent, lifecycle hooks, and business rules. Direct DML is faster and simpler to write. The tradeoff is correctness vs. simplicity — in a HIPAA-regulated Health Cloud org, there is no legitimate choice: correctness is mandatory.

**Synchronous vs. Async Callback Logic:** Callback logic runs in the managed-package transaction. Synchronous execution is simpler to debug but risks governor limit breaches on complex operations. Async delegation (Queueable) is more resilient but requires careful error surfacing. For any callback logic beyond a simple field update, delegate to async.

---

## Anti-Patterns

1. **Direct DML on Health Cloud clinical objects** — Inserting or updating `CarePlan`, `CarePlanGoal`, `ReferralRequest__c`, or related objects directly from Apex bypasses the Health Cloud automation layer, skips consent evaluation, and silently produces inconsistent data. Always route through Health Cloud invocable actions.

2. **Relying on Apex triggers for care plan lifecycle** — Using an `after update` trigger on `CarePlan` to intercept lifecycle transitions is unreliable because not all Health Cloud state changes surface as direct DML events. The `CarePlanProcessorCallback` interface is the correct and supported extension point.

3. **Unconditional System.debug in clinical Apex classes** — `System.debug()` calls that output clinical field values write PHI to debug logs, which are accessible to all system administrators and not protected by FLS. In HIPAA-covered orgs, this constitutes a data exposure event. All debug output in clinical classes must be gated by a Custom Metadata flag that defaults to off in production.

---

## Official Sources Used

- Salesforce Health Cloud Developer Guide — Apex Extension Points: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_developer.meta/health_cloud_developer/
- Salesforce Industries Common Components Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/
- Health Cloud Object Reference (EhrPatientMedication, PatientHealthCondition, CarePlan, ReferralRequest): https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/
- Apex Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
