# LLM Anti-Patterns — SCIM Provisioning

## Anti-Pattern 1: Treating Deactivation As Complete Deprovisioning

**What the LLM generates:** "On termination, IdP sends SCIM `active=false`."

**Why it happens:** SCIM spec treats deactivation as the final act.

**Correct pattern:** Deactivation is necessary but not sufficient. The runbook must also freeze first (for instant block), revoke OAuth tokens, and reassign record ownership.

## Anti-Pattern 2: Mapping Groups To Profiles

**What the LLM generates:** Okta group `sf-sales` → Salesforce Profile `Sales User`.

**Why it happens:** Profiles feel like the entitlement primitive.

**Correct pattern:** Use a stable default profile; layer entitlements via Permission Sets or Permission Set Groups. Profile churn is expensive and fragile.

## Anti-Pattern 3: Ignoring Permission Set Licenses

**What the LLM generates:** SCIM mapping assigns a PS that requires a PSL, without assigning the PSL.

**Why it happens:** Not all PSs require PSLs; the difference is easy to overlook.

**Correct pattern:** Enumerate PSs that require PSLs; ensure SCIM mapping assigns both atomically.

## Anti-Pattern 4: Single-IdP Assumption For Mixed Workforce

**What the LLM generates:** Architecture that funnels employees, contractors, and partners through one IdP.

**Why it happens:** One source of truth is "cleaner."

**Correct pattern:** Separate tenants or SCIM connections per workforce class. Each has different policies, SLAs, and audit needs.

## Anti-Pattern 5: No Monitoring On Provisioning Lag

**What the LLM generates:** Runbook with no observability.

**Why it happens:** Success is quiet.

**Correct pattern:** Monitor provisioning lag, failed SCIM events, license count, and deactivation SLA adherence. Alert on failure — do not trust silence.
