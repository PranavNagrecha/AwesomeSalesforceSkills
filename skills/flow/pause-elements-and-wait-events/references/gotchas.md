# Gotchas — Pause Elements and Wait Events

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: New Flow Version Activation Invalidates In-Progress Paused Interviews

**What happens:** When a new flow version is activated, paused interviews from the previous version may fail to resume or resume unpredictably. The serialized interview state references the old version's element GUIDs. If element identifiers or variable names change between versions, the resume either faults or skips steps silently.

**When it occurs:** Any time a new flow version is activated in production while interviews are paused. Common triggers: hotfix deployment during business hours, scheduled weekly release that happens to include a flow change, or a developer activating a fix for an unrelated flow element.

**How to avoid:** Before activating a new version, check Setup > Paused and Failed Flow Interviews for any currently paused interviews on the flow. If paused interviews exist, either wait for them to complete (if the wait event is imminent) or notify affected stakeholders that interviews will need to be manually restarted. Schedule flow version activations during maintenance windows when paused interview counts are at their lowest.

---

## Gotcha 2: Alarm Offset of Zero Days Does Not Resume Immediately

**What happens:** Setting an Alarm wait event with an offset of 0 Days does not trigger an immediate or near-immediate resume. Salesforce enforces a platform minimum fire time of approximately 15 minutes. The interview will remain paused for up to 15+ minutes even with a zero-day offset.

**When it occurs:** When a developer attempts to use a Pause element with a zero offset as a lightweight "defer to next transaction" mechanism, or when testing resume behavior and expecting instant results.

**How to avoid:** For immediate or sub-minute resume requirements, use a Platform Event wait event instead of an Alarm — the platform event path resumes the interview within seconds of the event being published. Reserve Alarm wait events for genuine time-based scenarios where a delay of at least 15 minutes is acceptable. For integration testing with Alarms, budget at least 20 minutes of waiting time per test case.

---

## Gotcha 3: Flow Builder Debug Mode Cannot Step Through Pause Elements

**What happens:** When running a flow in debug mode in Flow Builder, the debugger encounters the Pause element and immediately follows the first available output connector without actually pausing. Resume conditions are not evaluated. The specific wait event branch that would fire in production is not exercised during debug.

**When it occurs:** Every debug run of any flow containing a Pause element. Developers who test exclusively in debug mode ship flows with untested resume condition logic and untested wait event branch paths.

**How to avoid:** Treat Pause element paths as requiring functional (real-world) testing only. For Alarm wait events, set the base date to `{!$Flow.CurrentDateTime}` with an offset of 0 Days during testing, wait approximately 15 minutes, then verify the interview appeared in Setup > Paused and Failed Flow Interviews and subsequently completed. For Platform Event wait events, publish a test event via Apex anonymous execution in Developer Console after the interview reaches the Pause element, then verify the correct branch fired.

---

## Gotcha 4: Platform Event Resume Executes as the Automated Process User

**What happens:** When a flow interview resumes via a Platform Event wait event, the resume transaction runs in the context of the Automated Process user, not the user who originally launched the flow. Record Create, Update, and Delete elements in the resume path use the Automated Process user's permissions and run as that user in audit fields (`LastModifiedById`, `OwnerId` assignments, etc.).

**When it occurs:** Any resume via a Platform Event wait event. If the flow's resume path modifies records that require specific user ownership, field-level security based on the running user's profile, or triggers that check `UserInfo.getUserId()`, the Automated Process user context causes unexpected permission errors or incorrect data.

**How to avoid:** Design flows to avoid user-context-dependent logic after a Platform Event resume. Use System Mode with Sharing (Run in System Context) for the flow if record access is the concern. For audit trail correctness, include the original `RunningUserId` as an explicit field on records updated in the resume path. Review field-level security and record access rules against the Automated Process user before deployment.

---

## Gotcha 5: Paused Screen Flow Interviews Are Tied to the User Who Paused Them

**What happens:** A screen flow interview that a user manually pauses (via Save for Later) can only be resumed by that same user. Other users, including administrators, cannot resume the specific interview on behalf of the pausing user through the standard flow UI. The interview is private to the pausing user's Paused Interviews view.

**When it occurs:** When a screen flow supports collaborative processes where a supervisor might need to step in and complete a paused interview on behalf of an unavailable employee. The expectation that "admin can resume any paused flow" is incorrect for screen flow user-initiated pauses.

**How to avoid:** For use cases requiring shared resumption, avoid user-initiated screen flow pauses. Instead, use an auto-launched flow with a Pause element and a platform event to signal resume — the resume can then be triggered by any user with permission to publish the event. Alternatively, implement a custom Lightning component that surfaces paused interviews based on a record ID rather than relying on the standard Paused Interviews list view.

---

## Gotcha 6: Concurrent Paused Interview Count Is Org-Wide, Not Per-Flow

**What happens:** The limit on concurrently paused and waiting interviews applies across the entire org, not per flow. A single high-volume flow that pauses large numbers of interviews can consume the entire org limit, causing all other flows in the org that use Pause elements to fail when they attempt to pause.

**When it occurs:** In orgs with multiple flows using Pause elements, when one flow's volume scales up unexpectedly (e.g., a bulk data load triggers thousands of record-triggered flows that each pause), the entire org-wide pool is exhausted. New pause attempts across all flows fail with a governor limit error.

**How to avoid:** Estimate the peak concurrent paused interview count for all flows in the org, not just the one being designed. Monitor the count regularly via Setup > Paused and Failed Flow Interviews. If volume is a concern, implement cleanup routines (using an admin-accessible flow or Apex) to delete interviews that have been paused longer than the expected maximum wait window. Consider whether a Scheduled Apex pattern handles high-volume time-based requirements more scalably than per-record flow interviews.
