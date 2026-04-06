# Gotchas — Go Live Cutover Planning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Quick Deploy Window Is Exactly 10 Days, Not 10 Business Days

**What happens:** The validated deploy ID from a checkOnly deployment expires exactly 10 calendar days (240 hours) after the validation completed. There is no grace period, no warning notification, and no way to extend it. If your go-live date shifts even one day past the window, the quick deploy fails silently and you must re-run the full validation deploy during the cutover window.

**When it occurs:** When a go-live is postponed for business reasons (stakeholder unavailability, unresolved UAT defects) but the team does not re-run the validation deploy. Also when the validation deploy runs on a Monday but the cutover is scheduled for the following Friday (11 days later).

**How to avoid:** Calculate the exact expiration timestamp when the validation deploy completes. Build 2-3 days of buffer into the timing. If the go-live date shifts, immediately schedule a new validation deploy. Document the expiration date prominently in the cutover runbook.

---

## Gotcha 2: Apex Test Failures in Production That Did Not Occur in Sandbox

**What happens:** The validation deploy passes in the sandbox but fails in production because production contains managed packages, more data volume, or different org configuration that causes test failures. Common culprits: managed package triggers that fire on test data, SOQL queries hitting governor limits due to higher data volume, or test classes that reference hardcoded record type IDs that differ between orgs.

**When it occurs:** When the team validates only against sandboxes and assumes production will behave identically. Production orgs accumulate managed packages, custom settings data, and metadata that sandboxes may not have (especially Developer and Developer Pro sandboxes).

**How to avoid:** Always run the validation deploy against production itself, not a sandbox. This is the entire purpose of the checkOnly flag. If production-specific test failures appear, fix them before the code freeze — never plan to fix test failures during the cutover window.

---

## Gotcha 3: Flow Activation Order Matters for Record-Triggered Flows

**What happens:** When multiple record-triggered Flows exist on the same object, their execution order is not guaranteed unless explicitly set using the Flow trigger order (triggerOrder field, available since Spring '22). Deploying new Flows without setting trigger order can cause existing Flows to execute in a different sequence than expected, producing wrong field values or duplicate DML operations.

**When it occurs:** During go-live when new record-triggered Flows are activated alongside existing ones. The cutover team activates Flows without verifying trigger order, and production users create records that fire Flows in an unexpected sequence.

**How to avoid:** Include explicit trigger order values in the Flow metadata before deployment. Document the expected execution order in the cutover runbook. After activation, create a test record and verify the Flows fired in the correct sequence by checking debug logs or Flow interview records.

---

## Gotcha 4: Named Credential and Auth Provider Token State Is Not Deployed

**What happens:** Deploying Named Credentials deploys the metadata configuration (endpoint URL, authentication protocol, named principal identity) but does not deploy the actual authentication token or OAuth refresh token. After deploying Named Credentials to production, all callouts fail with authentication errors until someone manually completes the OAuth flow or enters the credentials in Setup.

**When it occurs:** Every time Named Credentials are deployed to a new org or re-deployed after being deleted. The cutover team deploys the credential metadata, sees a successful deployment, and assumes the integration is ready. The first callout fails at go-live.

**How to avoid:** Add explicit post-deployment steps in the cutover runbook for each Named Credential: navigate to Setup > Named Credentials, verify authentication status, and complete OAuth authentication if required. Test each integration endpoint before declaring the cutover complete.

---

## Gotcha 5: Scheduled Jobs and Scheduled Flows Do Not Auto-Resume After Deployment

**What happens:** If a deployment modifies an Apex class used by a scheduled job (CronTrigger), Salesforce automatically aborts the scheduled job during deployment. The job does not automatically reschedule after the deployment completes. Similarly, scheduled Flows that are deployed in an inactive state must be manually activated and their schedule re-confirmed.

**When it occurs:** During cutover when Apex scheduled jobs are already running in production. The deployment succeeds, but overnight batch jobs stop running because the CronTrigger was deleted during the deploy. The team discovers the issue Monday morning when reports show no data processed over the weekend.

**How to avoid:** Document every scheduled job and scheduled Flow in the cutover runbook with explicit post-deployment steps: verify the job exists in Setup > Scheduled Jobs, re-schedule if aborted, and confirm the next execution time is correct. Run a query on CronTrigger after deployment to verify all expected jobs are active.
