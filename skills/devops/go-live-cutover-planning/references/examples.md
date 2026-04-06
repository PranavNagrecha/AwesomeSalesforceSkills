# Examples — Go Live Cutover Planning

## Example 1: Weekend Cutover for a Sales Cloud Implementation

**Context:** A mid-market company is going live with Sales Cloud (Accounts, Contacts, Opportunities, custom objects, 12 Flows, 35 Apex classes) on a Saturday morning. The team uses Salesforce CLI with GitHub source control. Production has 200 active users.

**Problem:** Without a structured cutover plan, the team attempted a direct deploy on Saturday morning. The full deploy with RunLocalTests took 4 hours. Two test failures required debugging, pushing the window past the planned end time. Users logged in Monday morning to partially deployed features and broken page layouts.

**Solution:**

```text
Cutover Runbook — Sales Cloud Go-Live
======================================

T-7 days (Monday):
  - Code freeze enforced. Branch protection enabled on main.
  - Final UAT sign-off collected from business sponsor.

T-5 days (Wednesday):
  - Validation deploy executed against production:
    sf project deploy start --target-org prod --dry-run --test-level RunLocalTests
  - Validated deploy ID recorded: 0Af1234567890ABCDE
  - Expiration: 10 days from Wednesday = following Saturday (12 days of buffer)

T-2 days (Thursday):
  - Go/no-go meeting. Checklist reviewed:
    [x] Validation deploy passed — 92% coverage
    [x] UAT signed off by VP Sales
    [x] Data migration dry-run completed in Full sandbox
    [x] Rollback plan reviewed — redeploy previous package version
    [x] Hypercare team confirmed — 3 engineers on rotation
    [x] User communication sent — downtime notice for Saturday 6am-12pm
  - Decision: GO

T-0 (Saturday 6:00 AM):
  - Disable outbound integrations (Named Credentials deactivated)
  - Execute quick deploy:
    sf project deploy quick --job-id 0Af1234567890ABCDE --target-org prod
  - Quick deploy completed in 8 minutes
  - Activate 4 record-triggered Flows (verify version numbers)
  - Run smoke test checklist (15 items, 45 minutes)
  - Re-enable outbound integrations
  - Business sponsor confirms critical paths working

T-0 (Saturday 11:00 AM):
  - Go-live declared complete
  - Hypercare begins — Slack channel #salescloud-hypercare opened

T+1 through T+14:
  - Daily standup at 9 AM to review issues
  - On-call engineer responds to P1 within 30 minutes
  - Weekly hypercare report to business sponsor
```

**Why it works:** The validation deploy runs mid-week when there is time to debug failures without pressure. The quick deploy on Saturday takes minutes instead of hours, leaving ample time for smoke testing and rollback if needed. The 10-day quick deploy window provides buffer if the go-live date shifts by a few days.

---

## Example 2: Phased Cutover for a Multi-Cloud Implementation

**Context:** An enterprise is going live with Sales Cloud, Service Cloud, and a custom community portal simultaneously. The deployment includes 450+ metadata components, 3 data migration jobs, and 6 external integrations. Three separate development teams contributed code.

**Problem:** The team initially planned a single monolithic deployment. During the mock deployment in the Full sandbox, the community portal metadata failed due to a dependency on a Service Cloud permission set that had not yet deployed. The entire 4-hour deployment rolled back, wasting the mock deployment window.

**Solution:**

```text
Phased Cutover Runbook
======================

Phase 1: Foundation (Saturday 5:00 AM - 6:30 AM)
  Owner: Platform Team Lead
  - Deploy: Custom objects, fields, permission sets, sharing rules
  - Quick deploy from validated ID: 0Af_PHASE1_ID
  - Verify: Object access confirmed, field-level security correct
  - Rollback trigger: Any permission set deployment failure
  - Rollback action: Redeploy previous permission set package

  >>> HOLD POINT — Phase 1 verified before proceeding <<<

Phase 2: Automation (Saturday 6:30 AM - 8:00 AM)
  Owner: Automation Team Lead
  - Deploy: Apex classes, triggers, Flows (inactive)
  - Quick deploy from validated ID: 0Af_PHASE2_ID
  - Activate Flows in sequence: validation rules → record-triggered → scheduled
  - Verify: Create test records, confirm automation fires correctly
  - Rollback trigger: >3 Flow errors in smoke test
  - Rollback action: Deactivate Flows, redeploy previous Apex

  >>> HOLD POINT — Phase 2 verified before proceeding <<<

Phase 3: Data Migration (Saturday 8:00 AM - 10:00 AM)
  Owner: Data Team Lead
  - Run Account/Contact migration (Bulk API 2.0, 150k records)
  - Run Opportunity migration (80k records with line items)
  - Run historical Case migration (200k records)
  - Verify: Record counts match source, spot-check 50 records per object
  - Rollback trigger: >1% error rate on any migration job
  - Rollback action: Delete migrated records via Bulk API delete job

  >>> HOLD POINT — Phase 3 verified before proceeding <<<

Phase 4: Integrations and UI (Saturday 10:00 AM - 11:30 AM)
  Owner: Integration Team Lead
  - Activate Named Credentials for 6 external systems
  - Deploy community portal metadata
  - Enable Lightning pages and app assignments
  - Verify: End-to-end integration test for each external system
  - Rollback trigger: Any integration returning errors
  - Rollback action: Deactivate Named Credentials, revert to prior Lightning pages
```

**Why it works:** Each phase has an independent validation deploy, its own rollback trigger, and a hold point that prevents cascading failures. When Phase 1 succeeds, Phase 2 can safely reference the deployed permission sets. The data migration in Phase 3 runs after automation is active, ensuring Flows fire on migrated records.

---

## Anti-Pattern: Deploying Without a Validation Deploy Pre-Stage

**What practitioners do:** Skip the validation deploy earlier in the week and run a full deploy (with test execution) during the cutover window, assuming it will take about the same time as it did in the sandbox.

**What goes wrong:** Production orgs often have more Apex classes, more data, and more active metadata than sandboxes. Test execution in production can take 2-5x longer than in a sandbox. A deploy that took 45 minutes in the sandbox takes 3 hours in production. Combined with debugging any test failures, the team runs past the cutover window. Under time pressure, they either push the go-live incomplete or rush through smoke testing.

**Correct approach:** Always run a validation deploy (checkOnly:true) against production 2-5 days before the cutover window. Use the quick deploy path during the actual cutover to skip test re-execution. This reduces cutover-window deployment time from hours to minutes.
