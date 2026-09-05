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

---

## Gotcha 6: A Refresh Scheduled Mid-Cycle Deletes the Build You Are Testing

**What happens:** UAT starts on Monday. On Wednesday the platform team runs the sandbox refresh that was booked six weeks earlier for a different project. Thursday morning the testers find the new object, the assignment rule and the seeded test data gone, and every case that had passed is now unprovable. The build is still in version control, so nothing is lost permanently — but the UAT cycle restarts from the environment checklist, not from where it stopped.

**When it occurs:** Any release whose UAT window overlaps a booked refresh. It is likeliest on a Full sandbox, because a Full sandbox can only be refreshed every 29 days (`admin/sandbox-strategy` § Type Capacities and Refresh Windows) and teams therefore treat the refresh slot as unmissable and book it far ahead. Refreshing over live work destroys the metadata and test data sitting in the sandbox (`admin/sandbox-strategy` → `references/gotchas.md` § Refreshing Over Active Work).

**How to avoid:** The refresh date is a field in the UAT plan header, not a footnote — `refreshed_on` and `build_deployed_on`, in that order, with the checker asserting the refresh came first. Freeze the environment for the length of the cycle and name the person who can approve a refresh during it. If the refresh cannot move, the honest choice is to run UAT after it and re-deploy the build, not to run UAT across it.

---

## Gotcha 7: The Three Load Paths Disagree About Whether Assignment Rules Run

**What happens:** A developer inserts 50 cases through the REST API while building; they route correctly. The data owner loads the same 50 rows through Data Loader during UAT and every case lands on the load user instead of a queue. The rule is identical. Nothing was deployed in between.

**When it occurs:** Whenever a UAT case creates Cases, Leads or Accounts through anything other than the UI, and the case does not name the tool. The three paths have different defaults:

| Path | Behaviour when nothing is specified | Source |
|---|---|---|
| REST API | "If the header is not provided with a request, REST API defaults to using the active assignment rules" | `api_rest.txt` L691–694 |
| Bulk API 2.0 | `assignmentRuleId` is listed as **Optional** on the ingest job resource — absent means no rule runs | `api_asynch.txt` L1591–1595 |
| Data Loader | An **Assignment rule** setting takes the rule id for inserts, updates and upserts on cases and leads, and "the assignment rule overrides Owner values in your CSV file" — left blank, the CSV's owner wins | `salesforce_data_loader.txt` L379–383 |

**How to avoid:** Name the tool *and* the setting in the case preconditions, never "load the file." If the story says the backlog must route like a UI-created case, the case has a control set: create one record in the UI with the same field values and assert that the loaded rows landed on the same owner. Comparing to an expectation in the tester's head is how this defect reaches production.

---

## Gotcha 8: Partial Copy Sampling Hides Every Volume-Dependent Behaviour

**What happens:** UAT runs in a Partial Copy that "has production data in it." Every case passes. In production the same automation times out on the first end-of-month batch, or a report that returned in two seconds returns in ninety, or a rollup that was correct in UAT is wrong because the sandbox held a tenth of the child records.

**When it occurs:** Any release touching a query, rollup, escalation queue or automation whose behaviour is a function of row count. A Partial Copy holds 5 GB, or 10,000 records per selected object plus its children (`admin/sandbox-strategy` § Type Capacities and Refresh Windows) — the sample is a sample, and the sampling is per selected object, so parent and child volumes come out of proportion to each other. A synchronous transaction has 100 SOQL queries, 150 DML statements and 10,000 ms of CPU to work in (`apexdev.txt` L19544, L19554, L19579); none of those ceilings is anywhere near reachable at sample volume.

**How to avoid:** Decide the sandbox type from the *cases*, not the budget: if any acceptance criterion depends on volume, the programme needs a Full sandbox or the case has to be run somewhere that has the rows. When a Partial Copy is the only option, write the list of cases it cannot prove into the plan header and get the business owner to accept that list explicitly at sign-off. An unprovable case marked "Not Run" is a known risk; the same case marked "Pass" is a lie the release rests on.

---

## Gotcha 9: Defects Logged Against Symptoms Cannot Be Closed

**What happens:** The defect log fills with entries like "case went to the wrong queue," "email didn't arrive," "field is missing." Weeks later nobody can tell whether a fix closed the defect, because the entry never said what the correct behaviour was. Retest becomes an argument about what was originally meant, and the release ships with defects marked Closed that were only ever forgotten.

**When it occurs:** Any UAT run where testers log defects from the record page rather than from the test script. It is worst when the script and the defect log live in different tools, because the case id is then a manual copy-paste and the first tester who skips it sets the pattern.

**How to avoid:** A defect entry that does not carry a `case_id` — which in turn carries a `story_id` and an `ac_id` — is not accepted into the log. The expected result is copied from the case, not re-described. This makes the retest mechanical: re-run the named case, compare against the same expected string, close or reopen. It also makes the disposition honest, because a "defect" that no case predicts is either a missing case or a change request, and both of those are decisions someone has to make rather than a bug someone can quietly fix.

---

## Gotcha 10: Sign-Off on an All-Positive Script Proves Only That the Feature Exists

**What happens:** The script has twenty cases, all twenty pass, the business owner signs. Two weeks after go-live a user saves a record the validation rule was written to block, or opens a record the sharing model was written to hide. Nothing regressed — the guardrails were never tested, because every case in the script drove the feature the way it was designed to be driven.

**When it occurs:** Scripts generated directly from acceptance criteria that are all phrased as "the user can…". Restrictions — validation rules, FLS, sharing, required fields, permission gates — only fire on the conditions a positive case avoids by construction, so a script with no negative cases will never touch them regardless of how many rows it has.

**How to avoid:** Make negative coverage a property of the plan rather than a habit of the tester: at least one case with `negative_path: true` per story, and a go decision that is invalid unless those cases were executed and passed. For anything volume-sensitive, add the bulk case on the same footing — the checker in this skill fails a plan with no negative case and no bulk case for exactly this reason. `admin/uat-test-case-design` § Negative-Path Coverage gives the decomposition; this skill's contribution is that the programme cannot be signed off without it.

---

## Gotcha 11: "Works in Lightning, Fails in Mobile" Is a Layout Assignment, Not a Bug

**What happens:** Every case passes on the desktop. A tester opens the same record in the Salesforce mobile app and the new fields are not there, or the record opens on an entirely different page. The build team cannot reproduce it and closes the defect as "cannot reproduce" — from a desktop browser.

**When it occurs:** Whenever a release adds fields or a Lightning record page and UAT is executed only in a desktop browser. Two separate mechanisms are in play. Lightning page assignments are per form factor: `Large` "represents the Lightning Experience desktop environment," `Small` "represents the Salesforce mobile app on a phone or tablet," and `Medium` is reserved (`api_meta.txt` L39827–39836) — a page assigned only for `Large` is simply not what the phone renders. Separately, the at-a-glance fields the mobile app shows come from the compact layout, which "displays a record's key fields at a glance in the Salesforce mobile app, Lightning Experience, and in the Outlook and Gmail integrations" and supports every field type **except** text area, long text area, rich text area and multi-select picklist (`api_meta.txt` L43076–43082). A new long-text field can never appear there, and that is correct behaviour rather than a defect.

**How to avoid:** If any story mentions phone or field use, the persona row in the plan carries a device and at least one case is executed on it; otherwise state in the plan header that mobile is out of scope, so a mobile finding after go-live is a known gap rather than a surprise. When a mobile-only failure is reported, check the form-factor assignment and the compact layout before opening a defect against the build — most of these are configuration that was never assigned, and one of them is a field type that cannot be shown at all.
