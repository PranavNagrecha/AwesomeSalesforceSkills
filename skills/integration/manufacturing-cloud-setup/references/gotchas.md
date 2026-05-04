# Gotchas — Manufacturing Cloud Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ABF Recalc DPE Is Not Automatic

**What happens:** Net-new Manufacturing Cloud orgs go live with no Account-Based Forecasting recalc job running. `AccountProductForecast` records never populate, and the executive forecast dashboard shows empty.

**When it occurs:** Every Manufacturing Cloud go-live where the activation step was skipped.

**How to handle:** As part of the go-live checklist, locate the **Account-Based Forecasting recalculation** definition under Setup → Data Processing Engine, activate it, and schedule it (nightly is typical). Run it manually once after activation to backfill any history accumulated during the gap.

---

## Gotcha 2: `OrderItem.SalesAgreementId` Is Not Auto-Populated

**What happens:** Orders flow into the org against an account that has an active Sales Agreement, but the actuals never reconcile to the agreement. Variance dashboards show zero actuals.

**When it occurs:** Order ingestion paths (Apex triggers, Flows, integrations) that don't explicitly populate the `SalesAgreementId` lookup on OrderItem.

**How to handle:** In every Order ingest path, populate `OrderItem.SalesAgreementId` by looking up the active `SalesAgreement` for the account+product+date combination. Add a trigger / Flow rule to fail orders where an active agreement exists but `SalesAgreementId` is null (or warn loudly).

---

## Gotcha 3: Schedule Frequency Cannot Be Changed Without Pain

**What happens:** A Sales Agreement was activated with a Monthly schedule, then the team realizes Quarterly is what the customer wanted. Changing the schedule frequency requires destructive steps.

**When it occurs:** Insufficient design upfront, or customer change-of-mind after activation.

**How to handle:** Decide schedule frequency before activation. If a change is unavoidable, deactivate the agreement, delete `SalesAgreementProductSchedule` rows, change the frequency, reactivate. Plan for actuals reconciliation churn during the transition.

---

## Gotcha 4: Rebate Tiers Are Cumulative, Not Marginal

**What happens:** A finance team designs a tier structure assuming marginal application (e.g., 0–10K @ 0%, next 40K @ 2%, units beyond @ 4%) but the native Rebate engine applies the highest qualifying tier to the entire volume.

**When it occurs:** Designing rebate programs without testing the calc with a worked example before go-live.

**How to handle:** Always run a worked example through the native engine before publishing the rebate program to members. If marginal-tier behavior is required, it must be implemented as custom Apex (and accepts the edge-case maintenance burden that brings).

---

## Gotcha 5: `SalesAgreementProductSchedule` Permissions Don't Cascade

**What happens:** End users can see `SalesAgreement` and `SalesAgreementProduct` but the schedule rows appear empty. The agreement looks broken.

**When it occurs:** Permission set design that grants Read on the parent objects but forgets the schedule child object.

**How to handle:** Grant explicit Read on `SalesAgreementProductSchedule` in the same permission set as the parent objects. Manufacturing Cloud's child-object permissions do not cascade from parent.

---

## Gotcha 6: Channel Revenue Management Enabled Unnecessarily

**What happens:** A team enables Channel Revenue Management to "be safe" even though the OEM sells direct-to-customer. The CRM module objects clutter Object Manager, the Setup pages add complexity, and rebate programs become harder to navigate.

**When it occurs:** Over-cautious provisioning during license enablement.

**How to handle:** Enable Channel Revenue Management only when there is a true two-step distribution model (OEM → distributor → consumer) with partner inventory tracking. For direct sales with rebates, base Manufacturing Cloud Rebate Management is sufficient.
