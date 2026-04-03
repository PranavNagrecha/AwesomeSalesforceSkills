# Gotchas — UAT and Acceptance Criteria

Non-obvious Salesforce platform behaviors that cause real production problems during UAT.

## Gotcha 1: Sandbox Email Deliverability Blocks Email-Based Test Cases

**What happens:** Acceptance criteria that include email delivery (e.g., "An email notification is sent to the Account owner when a Case is escalated") produce a false failure during UAT. The Flow or Workflow Rule fires correctly, but the email never arrives in the tester's inbox. The tester marks the test case Failed and raises a defect.

**When it occurs:** Any time UAT involves email alerts, email templates, or email-send actions in Flows. Salesforce sets all sandboxes to "System email only" deliverability by default. This means only system-generated emails (password reset, login confirmation) are delivered. Email alerts from automation are silently dropped.

**How to avoid:** Before UAT begins, navigate to Setup → Email → Deliverability in the UAT sandbox and set the Access Level to "All Email." Document this as a pre-UAT environment setup step. Note that enabling "All Email" in a sandbox may send emails to real business contacts if test records use production email addresses — use a test email domain (e.g., `@test.invalid` or a shared testing mailbox) for all tester accounts.

---

## Gotcha 2: Profile-Scoped FLS Defects Are Invisible from the Wrong User

**What happens:** An admin tests a new field from their own admin user and confirms it is visible and editable. The field is deployed. During UAT, a business tester logged in as a Sales Rep cannot see the field at all. The defect is reported as a major P2 — a core workflow is broken for the actual users.

**When it occurs:** Any feature that involves Field-Level Security (FLS) configuration. Admins have implicit field access that bypasses FLS in the UI. Testing from an admin account does not expose FLS defects. The field may be fully configured for admins and completely hidden or read-only for every other profile.

**How to avoid:** UAT test cases for any field-related acceptance criteria must include a precondition specifying the tester's exact profile. Create a dedicated set of named test users, one per profile in scope, with realistic profile and permission set assignments (not system administrator). Run every field-visibility and field-editability test case logged in as the actual end-user profile. FLS can be verified in Setup → Object Manager → [Object] → Fields & Relationships → [Field] → Field Accessibility, but execution-time testing from the correct profile is the only reliable UAT confirmation.

---

## Gotcha 3: Time-Triggered Automation Cannot Be Tested by Waiting

**What happens:** A feature includes a time-based Flow ("Send a reminder email 3 days before an Opportunity Close Date"). The tester sets a Close Date to 3 days in the future and waits 3 days for the email. In a sandbox, the time-based Flow queue does not advance at real-time speed — the Flow fires based on the processing schedule, not the wall clock. In some sandbox configurations, time-based entries never execute without manual intervention.

**When it occurs:** Record-Triggered Flows with scheduled paths, scheduled Flows, Workflow Time Triggers, and Process Builder scheduled actions. These all use the Salesforce time-based workflow queue which has a processing cadence that differs from production in sandboxes.

**How to avoid:** For time-based acceptance criteria, use one of these approaches:
1. Set the trigger date to "today" (or past) so the scheduled action fires on the next queue processing cycle (usually within minutes in a Full sandbox).
2. In Developer Console, run the scheduled job manually: `System.schedule()` or trigger the underlying class directly.
3. Accept this as an environment limitation, document it in the preconditions as "time-trigger tested via Developer Console execution," and obtain business owner acknowledgment.
Document time-based automation as a separate test case category with explicit sandbox limitations noted in the preconditions column.

---

## Gotcha 4: Sharing Recalculation Is Asynchronous — Record Visibility Tests Can Return Stale Results

**What happens:** A tester updates a record's owner or Account parent to trigger a sharing rule change. They immediately log in as a different user to verify the record is now visible. The record does not appear in the second user's list view. The tester reports a sharing defect. The admin confirms the sharing rule is correctly configured. After an hour, the sharing is correct.

**When it occurs:** Sharing rule recalculation, ownership transfers, and manual shares all run asynchronously via the sharing recalculation batch job. The visibility change is not instantaneous. In orgs with large data volumes or complex sharing models, recalculation can take minutes to hours.

**How to avoid:** Add a precondition note to all sharing-related test cases: "Allow 5–10 minutes after the trigger action before checking record visibility. For large sandboxes, sharing recalculation may take longer." Do not log a defect based on an immediate check. Validate sharing via Setup → Sharing Settings → Recalculate if you need to force a faster result. For UAT environments with large data volumes, schedule sharing-related test cases at the start of a session so the recalculation completes before the tester checks the result.

---

## Gotcha 5: Record Type Defaults and Page Layouts May Not Match Production

**What happens:** A sandbox was refreshed 6 months ago and has since had other projects applied to it. Record type default assignments, page layout assignments, and profile permission changes from those other projects now exist in the sandbox but not in production. A test case for a page layout change passes in the sandbox but the same layout would behave differently in production because the record type default assignment was changed in the sandbox and not in scope for the current release.

**When it occurs:** Any multi-project sandbox where configuration changes accumulate across projects without a full refresh. The UAT environment diverges from production over time.

**How to avoid:** Before UAT for each release, generate a metadata diff between the sandbox and production using `sf project retrieve` or a change management tool. Verify that record type assignments, page layout assignments, and profile configurations for the personas in scope match production. If they do not match, either refresh the sandbox or document the known differences and adjust test preconditions accordingly. Include sandbox configuration verification as a formal pre-UAT setup step in the test plan.
