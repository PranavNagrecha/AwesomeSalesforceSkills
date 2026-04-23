# Flow Deployment — Examples

## Example 1: Deploy-As-Inactive For A Risky Flow

**Context:** high-risk approval flow with paused interviews in flight.

**Procedure:**
1. Pre-deploy: query `FlowDefinitionView` — note active VersionNumber = 7.
2. Deploy new version 8 as inactive (`status="Obsolete"` in `Flow` source
   OR activate-separately pattern).
3. Smoke test version 8 by running directly from Setup.
4. Activate version 8 via `FlowDefinition` update — now version 8 is
   Active.
5. Monitor paused-interview resume for 24h.

Rollback: flip `FlowDefinition.ActiveVersion` back to 7.

---

## Example 2: Subflow Before Caller

**Context:** Screen Flow "OnboardingMain" calls subflow "AddressCapture".
Both change.

**Procedure:**
1. Deploy AddressCapture v3 as active first.
2. Deploy OnboardingMain v5 second. It now references AddressCapture v3
   by name (latest active).
3. Smoke test the main flow.

If you deploy caller first, it may briefly call the old subflow version.

---

## Example 3: Rollback Without Redeploy

**Post-deploy issue:** version 12 activated but throws at runtime.

**Wrong:** redeploy source of version 11. This creates version 13 and
leaves version 12 as latest.

**Right:** update `FlowDefinition.ActiveVersion = 11` via Metadata API.
Version 11 is active again; version 12 is preserved for triage.

---

## Anti-Pattern: Mass-Delete Old Versions As "Cleanup"

A team deleted all versions older than 30 days of all flows. Paused
interviews from three months prior failed at resume. Fix: retention must
match paused-interview lifetimes, not a calendar rule.
