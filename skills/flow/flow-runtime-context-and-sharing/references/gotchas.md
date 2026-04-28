# Gotchas — Flow Runtime Context And Sharing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Before-Save Record-Triggered Flows Always Run in System Context

**What happens:** A record-triggered flow configured for User Context is opened by a developer, who confirms the run-mode setting in Flow Builder reads "User Context." The flow contains a Get Records on a related object, which the developer expects to fail when the triggering user lacks sharing. In testing, the Get Records succeeds — and updates a child record the user shouldn't be able to touch.

**When it occurs:** Whenever the flow trigger is **Before Save**. Before-save flows execute inline with the triggering DML, before sharing-rule evaluation. The platform does not honor the configured run mode for before-save flows. The setting in Flow Builder is silently ignored.

**How to avoid:**
- Treat every before-save flow as System Context regardless of the UI setting.
- For after-save logic where sharing must be enforced, use an after-save flow and set `<runInMode>SystemModeWithSharing</runInMode>` explicitly.
- Add a comment in the flow description: "Before-save trigger; ignores runInMode by platform design."
- During code review, automatically flag any before-save flow whose `<runInMode>` is set to something other than `DefaultMode` — the setting is misleading.

---

## Gotcha 2: `$User` Returns the Triggering User in After-Save Flows, Not the Flow Owner

**What happens:** A record-triggered after-save flow sends a confirmation email to `$User.Email`. During testing, sysadmins receive the email. In production, when end users save records, *they* receive the email — even though the flow author intended the email to go to the flow's "owner" or to a service inbox.

**When it occurs:** Any record-triggered flow (before or after save) where the merge field `$User` is referenced. `$User` always resolves to the user who initiated the triggering DML, not the flow author and not a system identity. The same applies to `$Profile`, `$UserRole`, and `$Permission` — all reflect the triggering user.

**How to avoid:**
- Never assume `$User` is the system or the flow owner.
- For "send email to a fixed address," store the address in a Custom Metadata Type or an `Org_Settings__c` Custom Setting.
- For "act on behalf of a service user," pass the service user's Id explicitly into a subflow, do not derive from `$User`.
- During audit, grep for `$User`, `$Profile`, `$Permission` references in flows whose run mode is System Context — these are likely bugs waiting to happen.

---

## Gotcha 3: System Context Without Sharing Inherits to Subflows by Coincidence, Not by Design

**What happens:** A parent flow is set to System Context Without Sharing. It calls a subflow. The author assumes the subflow inherits the parent's mode. In a refactor, the subflow's `runInMode` is changed (or is set as a Screen subflow), and suddenly the parent's behavior breaks — Get Records inside the subflow returns fewer records, Update Records fails, audit logs go missing.

**When it occurs:** Any time a parent and child flow have different `runInMode` settings. There is **no inheritance**. Each flow's `runInMode` is independent. If both happen to be `SystemModeWithoutSharing`, the behavior looks like inheritance — but it isn't.

**How to avoid:**
- Set `<runInMode>` explicitly on every subflow, even shared utility subflows.
- Document the expected calling context in the subflow description.
- During refactor reviews, diff `<runInMode>` across all callers and the subflow — flag any mismatch.
- For shared utility subflows that need to honor the caller's intent, use `DefaultMode` and document: "Inherits the auto-launched-flow default for this org."

---

## Gotcha 4: FLS Still Enforces in Some Action Elements Regardless of Run Mode

**What happens:** A flow runs in System Context Without Sharing. It uses Send Email Alert with a merge field that references a field hidden from the running user's profile. The email is sent — but the merged value is blank. The author assumed System Context bypasses everything; it doesn't.

**When it occurs:**
- Send Email Alert respects FLS on merge fields it pulls into the email body.
- Post to Chatter respects FLS on merge fields.
- Apex Action elements enforce FLS per the called Apex class's own `with sharing` / `WITH SECURITY_ENFORCED` declarations.
- Outbound Message actions enforce FLS for the field set sent.

**How to avoid:**
- Don't rely on flow run mode to bypass FLS for actions. Run mode controls record-level visibility; FLS in actions follows the action's own enforcement model.
- For email templates that need cross-FLS merge values, build the body in the flow itself (System Context bypasses FLS for assignment-into-variables) and pass the assembled body to Send Email Action as plain text.
- Test every action element with the actual running user persona, not just sysadmin.

---

## Gotcha 5: API-Version Pinning Determines the Default

**What happens:** Two flows in the same org behave differently. Both rely on the implicit default. One was created in Spring '20 (API 48.0); one in Spring '21 (API 52.0). The first runs as User Context; the second as System Context Without Sharing. Audit findings differ even though the metadata "looks the same."

**When it occurs:** Any flow without an explicit `<runInMode>` element. The platform picks the default based on the flow's `<apiVersion>`. The cutover for record-triggered flows was Spring '21 (API 52.0).

**How to avoid:**
- Set `<runInMode>` explicitly on every flow — never rely on the API-version default.
- Pin `<apiVersion>` explicitly so a Flow Builder Save doesn't silently bump it.
- Add a CI lint that fails any flow with no `<runInMode>` set.
- For legacy flows being touched, set `<runInMode>` to whatever the historical behavior was, then plan a separate change to align with current security policy.

---

## Gotcha 6: Sharing Rules Are Evaluated Lazily, Not on Every Get Records

**What happens:** A System Context With Sharing flow does a Get Records, gets 5 records back. A sharing rule is added that should grant the running user access to 5 more records. The next execution of the flow returns 5, not 10 — the sharing recalculation hasn't completed yet.

**When it occurs:** After any sharing-rule change, group membership change, role hierarchy reshuffle, or territory realignment. Sharing recalculation is asynchronous; the flow sees the pre-recalculation state until calculation completes (can take minutes for large orgs, hours for huge orgs).

**How to avoid:**
- For flows that depend on freshly granted sharing, queue them after `Database.executeBatch` for the sharing recalculation completes — or add a delay element.
- Document the sharing dependency in the flow description.
- For audit, run the flow with a known persona and compare the returned record count to the expected sharing-granted set.

---

## Gotcha 7: Validation Rules Reference `$User` Differently Across Modes

**What happens:** A validation rule fires only when `$User.Profile.Name = 'Standard User'`. A System Context flow updates a record, and the rule fires unexpectedly — even though the flow author thought "system context" would be exempt.

**When it occurs:** All flows fire validation rules regardless of run mode. The `$User` referenced in the rule is the running user (the user whose DML triggered the flow, or the Apex caller's user, or Automated Process). Validation rule logic that assumes "system bypasses me" is wrong.

**How to avoid:**
- For validation rules that should not fire during automation, use the `$Setup.Bypass_Validation__c` Custom Setting pattern: the rule checks a bypass flag that flows can set in their session.
- Or, gate the rule on `ISCHANGED` of a user-editable field, which automation typically doesn't change directly.
- Document in the validation rule description which automation flows are expected to bypass it and how.

---

## Gotcha 8: Per-Element Override Doesn't Exist on Action Elements

**What happens:** A flow runs in User Context. The author wants one specific Apex Action call to escalate to System Context Without Sharing. They look for a `runInMode` setting on the Action element — there isn't one.

**When it occurs:** Per-element `runInMode` is supported on Get Records, Create Records, Update Records, Delete Records. Action elements (Apex actions, Email Alert actions, Submit for Approval, etc.) have their own enforcement model — they cannot be escalated from the flow side.

**How to avoid:**
- For Apex actions that must escalate, declare the Apex class as `without sharing` and rely on the class-level enforcement; the flow's run mode does not affect it.
- For email actions that must reference data the user can't see, pre-load the data via an escalated Get Records (which DOES support per-element override) and pass the assembled values into the email action.
- Document the boundary: "This Apex action is `without sharing` independent of the calling flow."

---

## Gotcha 9: Orchestration Stages and `$User` Pre-Claim

**What happens:** An Orchestrator stage assigned to a queue references `$User.Email` in its work-item subject. Before any user claims the work item, the subject renders as blank. The customer sees a confused email.

**When it occurs:** Any Orchestrator stage assigned to a Queue (rather than a specific user) where `$User` is referenced before claim. The running user is undefined until claim.

**How to avoid:**
- Don't reference `$User` in pre-claim stage outputs. Use the queue's display name (looked up via Get Records on Group).
- Defer `$User`-dependent logic to post-claim stages.
- Test the stage with both pre-claim and post-claim states.

---

## Gotcha 10: Saving in Flow Builder Bumps API Version Silently

**What happens:** A developer opens a flow created at API 50.0 to fix a typo. They click Save. Flow Builder upgrades `<apiVersion>` to the current release version (e.g., 62.0). No git diff warning, no UI prompt. The flow's default run mode flips from User Context (API 50.0 default) to System Context Without Sharing (API 52.0+ default).

**When it occurs:** Any time a legacy flow is opened and saved in current Flow Builder. The API version bump is silent. The behavioral change is silent. The audit failure is loud — six months later.

**How to avoid:**
- Pin `<apiVersion>` and `<runInMode>` explicitly in every flow, especially before any maintenance edit.
- Add a CI check that fails if a flow's API version is bumped in a PR without an accompanying explicit `<runInMode>` set.
- Code-review every flow change: look for API version changes and demand a corresponding run-mode review.

---

## Gotcha 11: Experience Cloud Guest User and Run Mode Interaction

**What happens:** A Screen Flow on an Experience Cloud site is set to System Context Without Sharing "to make the customer-facing form work." A guest user (unauthenticated) navigates to it. The flow now reads any record matching its filter, including records from other customers, exposed via the form's confirmation screen.

**When it occurs:** Any flow on an Experience Cloud entry point where the run mode is System Context. Guest users have minimal permissions by design; escalating to System Context defeats that protection.

**How to avoid:**
- Never set Experience Cloud guest-accessible flows to System Context. Force User Context.
- Use the guest user profile + sharing sets to grant minimum access; do not bypass via flow.
- Add a deployment-time check that fails any flow associated with a guest user license profile if `<runInMode>` is `SystemModeWithoutSharing`.

---

## Gotcha 12: Platform Event Flow Subscriber Run-As User

**What happens:** A platform-event-triggered flow references `$User.Profile.Name`. For standard PEs the running user is Automated Process (no profile, returns blank). For high-volume PEs, the running user is whatever's set in the PE's "Subscriber Run As User" — could be a real user with a real profile. The flow's branching behavior differs across PE types.

**When it occurs:** Any flow subscribed to a Platform Event. The running-user identity depends on the PE's subscriber configuration.

**How to avoid:**
- Check the PE's Subscriber Run As User before designing flow logic that depends on `$User`.
- Avoid `$User`/`$Profile`/`$Permission` references in PE-triggered flows; use Custom Metadata Type feature flags instead.
- Document the expected running user in the flow description.
