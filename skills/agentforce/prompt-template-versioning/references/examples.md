# Examples — Prompt Template Versioning

## Example 1: CMDT-backed template binding

**Context:** Sales email prompt updated weekly.

**Problem:** Direct reference in Flow means rollback = redeploy Flow = 30-minute change window.

**Solution:**

Flow reads `Prompt_Template_Binding__mdt` where Target_Slot__c='SalesEmail' AND Active__c=TRUE, then invokes that DeveloperName. Rollback is a single CMDT record edit.

**Why it works:** The CMDT is the atomic promotion unit — Flow code is stable, prompt version is data.


---

## Example 2: Canary rollout via user-hash bucketing

**Context:** Shipping `_v4` to 10% of reps before going full.

**Problem:** All-or-nothing promotion doesn't let you test in production.

**Solution:**

Invocable Apex resolves the template name: `hash(userId) % 10 == 0 ? 'SalesEmail_v4' : 'SalesEmail_v3'`. Metrics are logged per template name; expand the bucket when stable.

**Why it works:** Canary is a feature-flag pattern applied to prompt version — same operational discipline as code.

