---
name: flow-runtime-context-and-sharing
description: "Flow runtime sharing context — run in user vs system mode, record access in Flow. Triggers: Flow sharing, run in system mode, Flow user context. NOT for Apex sharing declarations — use apex/apex-with-without-sharing-decision."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "flow runs as system but should respect sharing"
  - "screen flow can't see records the user owns"
  - "$Permission merge field returns wrong value"
  - "should this flow run with sharing or without"
  - "flow bypassed FLS and exposed sensitive fields"
  - "record-triggered flow ignores sharing rules"
  - "Spring '21 default run mode change"
  - "subflow inherits run mode from parent flow"
tags:
  - flow-runtime-context-and-sharing
  - security
  - sharing
  - fls
  - crud
  - run-mode
  - audit
  - flow
inputs:
  - Flow XML or Flow design (record-triggered, screen, scheduled, auto-launched)
  - Running-user persona expectation (which user invokes, which user the work is "on behalf of")
  - Sensitivity classification of records the flow reads or writes (HR, Comp, Health, public)
  - Existing run-mode setting (apiVersion + runInMode)
  - Sharing model of the affected objects (OWD + sharing rules)
outputs:
  - Recommended overall run mode (System With Sharing / System Without Sharing / User)
  - "Escalation decisions: which logic moves into a subflow with its own runInMode"
  - Audit findings flagging over-privileged flows
  - Justification block citing sensitivity + least-privilege
  - Test plan covering low-privileged-user persona
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Runtime Context And Sharing

Activate when designing, reviewing, or auditing a Flow whose run mode determines whether it sees records the running user can't, edits fields the running user can't, or trusts merge fields that resolve from the running user's context. This is the canonical Security skill for Flow — every record-triggered, screen, scheduled, or auto-launched flow that touches sensitive data must justify its run mode against this skill before activation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Flow type and trigger.** Record-triggered (before-save / after-save), screen, scheduled, auto-launched, platform-event-triggered, or orchestration. Each has a different default run mode and different override semantics.
- **Who is the running user?** The interactive user clicking through a screen flow, the user whose DML fired a record-triggered flow, the Automated Process user for scheduled flows, the Apex caller's running user for invocable contexts, or a guest user for Experience Cloud entry points.
- **What records does the flow read?** Are they within the running user's sharing visibility? Could a low-privileged user trigger this flow and indirectly read records they cannot otherwise see?
- **What records does the flow write?** Will writes hit objects whose OWD is Private and where sharing rules matter (HR_Case__c, Compensation__c, Patient__c, Opportunity in a sales-team-only org)?
- **Sensitivity classification.** HR, Comp, Health (HIPAA), Financial (SOX), Personal (GDPR/CCPA), or public-business data. The recommended default flips for each tier.
- **API version pinning.** Flows pin runtime behavior to their API version. A flow saved at API 51.0 (Spring '21) or earlier may default differently than one saved at API 52.0+.
- **Existing `runInMode` setting.** Is it explicitly set in the Flow XML, or is it relying on the default? Implicit defaults are the #1 source of audit findings here.

The most common wrong assumption: "the flow runs as the user who triggered it, so sharing is enforced." It does not. Since Spring '21, record-triggered flows default to **System Context Without Sharing**, which bypasses sharing rules even when the triggering user couldn't see the record themselves. UNVERIFIED (2026-10-20): the Spring '21 default change and the claim that after-save flows default to Without Sharing are not in the corpus. The corpus says `DefaultMode` means "How the flow is launched determines whether the flow runs in user context or in system context" (api_meta 264 L70908-70909), and `runInMode` has a fourth value, `UserMode`, from API version 68.0 (L70923-70927).

Limits and platform constraints:
- Before-save record-triggered flows always run in System Context regardless of the configured run mode (they execute inside the same transaction as the triggering DML, before sharing is evaluated). UNVERIFIED (2026-10-20): the "always System Context" and "setting ignored" claims are not in the corpus; the order of execution runs before-save flows at step 3 (apexdev 264 L15643).
- Screen Flows always default to User Context — but a subflow called from a Screen Flow inherits its own setting, not the parent's. UNVERIFIED (2026-10-20): not in the corpus (see the `UserMode` sentence in Concept 2 for the one documented statement about inheritance).
- `runInMode` is a field of the Flow, not of individual elements. CONTRADICTED (2026-10-20): the earlier text said a per-element override is supported on Get Records and DML elements; the Metadata API documents `runInMode` only on the Flow (api_meta 264 L70907) and its sample places it at the flow level beside `recordLookups` (L76526-76533). Actions (Send Email, Apex actions) run under their own rules (UNVERIFIED (2026-10-20): not in the corpus).

---

## Core Concepts

There are three central concepts a practitioner must understand: the run modes themselves, how to escalate one operation, and the Spring '21 default change (UNVERIFIED (2026-10-20), see Concept 3).

### Concept 1 — The Run Modes

`runInMode` has four values (api_meta 264 L70907-70927): `DefaultMode`, `SystemModeWithSharing`, `SystemModeWithoutSharing` and, from API version 68.0, `UserMode`. The table covers the three modes the earlier text described; `UserMode` is described after it. The setting is on the flow's overall properties:

| Run Mode | Sharing Rules | FLS | CRUD | Validation Rules | Who is "Running User"? |
|---|---|---|---|---|---|
| **System Context Without Sharing** | Bypassed | Bypassed | Bypassed | Fired | Automated Process or invoking user (depends on context) |
| **System Context With Sharing** | Enforced | Bypassed | Bypassed | Fired | Same as above |
| **User Context** | Enforced | Enforced | Enforced | Fired | The interactive user |

Key points:
- "Without Sharing" + "With Sharing" are both **System Context** — meaning FLS and CRUD are always bypassed in either mode. The only difference is whether record-level sharing rules apply. `SystemModeWithSharing` "respect[s] org-wide default settings, role hierarchies, sharing rules, manual sharing, teams, and territories" but "doesn't respect object permissions, field-level access, or other permissions of the running user"; `SystemModeWithoutSharing` "can access all data" (api_meta 264 L70912-70920).
- `UserMode` (API version 68.0 and later): "The flow runs with the user's security context explicitly enforced, without inheriting sharing settings from the calling context"; in the UI it appears as User Context—Enforces User Permissions (api_meta 264 L70923-70927). `DefaultMode` appears as User or System Context—Depends on How Flow is Launched (L70908-70911).
- Only **User Context** enforces FLS and CRUD. This matters for screen flows that surface fields a low-profile user shouldn't see.
- Validation rules fire in all three modes (a flow's DML goes through the save procedure, apexdev 264 L15671; UNVERIFIED (2026-10-20): independence from run mode is not stated) — but a validation rule that references `$User.Profile.Name` will resolve against the actual running user, which can yield surprising results in System Context flows.

Defaults by flow type (UNVERIFIED (2026-10-20): the whole list below, including "since Spring '21", is not in the corpus; the guide says only that `DefaultMode` depends on how the flow is launched, api_meta 264 L70908-70911):
- **Record-triggered (after-save, since Spring '21):** System Context Without Sharing.
- **Record-triggered (before-save):** Always System Context (the setting is ignored).
- **Screen Flow:** User Context.
- **Auto-launched (scheduled, platform-event, invoked from Apex):** System Context Without Sharing (since Spring '21).
- **Orchestration (Flow Orchestrator stages):** Each stage can be configured; default tracks the underlying flow type.

The principle of least privilege says: start at **User Context** and escalate only with justification. The Salesforce default does the opposite — it starts at without-sharing and forces you to opt in to safety. This is why every record-triggered flow needs an explicit run-mode review.

### Concept 2 — Escalating One Operation: the Flow-Level `runInMode` and a Subflow

`runInMode` is a field of the Flow: "The context that the flow runs in" (api_meta 264 L70907). CONTRADICTED (2026-10-20): the earlier text said the attribute is supported on individual Get Records, Create Records, Update Records and Delete Records elements, with a Flow Builder toggle per element. No element type in api_meta 264 documents a `runInMode` field (the only mentions are L70907 and the flow-level sample at L76533). Valid values of the flow-level field:

- `DefaultMode` — "How the flow is launched determines whether the flow runs in user context or in system context" (api_meta 264 L70908-70909).
- `SystemModeWithSharing` — System Context With Sharing.
- `SystemModeWithoutSharing` — System Context Without Sharing (API version 49.0 and later, L70921-70922).
- `UserMode` — user security context explicitly enforced (API version 68.0 and later, L70923-70927).

To escalate one read inside a User Context flow, put that read in a subflow whose own `runInMode` is `SystemModeWithSharing` (Pattern 1). UNVERIFIED (2026-10-20): that a subflow runs under its own `runInMode` rather than the parent's is not stated in the corpus; the references of this package disagree with the gotcha below on it, so set `runInMode` explicitly on every subflow and test it.

Use the setting deliberately and document it. An audit script should flag every flow with `runInMode` other than `DefaultMode` for human review.

In Flow Builder the flow-level setting appears as User or System Context—Depends on How Flow is Launched, System Context with Sharing—Enforces Record-Level Access, System Context without Sharing—Access All Data and, from API 68.0, User Context—Enforces User Permissions (api_meta 264 L70910-70926). UNVERIFIED (2026-10-20): the per-element toggle labels of the earlier text are not in the corpus.

### Concept 3 — The Spring '21 Default Change

UNVERIFIED (2026-10-20): every statement in this section (the API 51.0/52.0 cutover, the defaults before and after it, and the re-save consequence) is not in the corpus. The only corpus statement about defaults is that `DefaultMode` depends on how the flow is launched (api_meta 264 L70908-70909).

Before Spring '21 (API 51.0):
- Record-triggered flows defaulted to **User Context** (sharing-enforced).
- Auto-launched flows defaulted to System Context Without Sharing.

In Spring '21 (API 52.0):
- Record-triggered flows changed default to **System Context Without Sharing**.
- The change applies only to flows created or saved at API 52.0 or higher.

Implications for audit:
- A flow with `apiVersion < 52.0` and no explicit `runInMode` runs in **User Context** — it may unexpectedly fail to read records the triggering user can't see.
- A flow with `apiVersion >= 52.0` and no explicit `runInMode` runs in **System Context Without Sharing** — it may unexpectedly bypass sharing.
- "Saving" a legacy flow in Flow Builder bumps its API version and silently changes its security model. This has caused production data leaks. Always check `apiVersion` and `runInMode` together before re-saving.

### Concept 4 — `$User`, `$Profile`, `$Permission` Merge Fields

UNVERIFIED (2026-10-20): the running-user table below is not in the corpus, except for platform-event-triggered flows, where "each flow interview runs in the context of the user who published the event message" and only the debug log appears under the Automated Process user (platform_events 264 L2190-2192). That row is corrected. The scheduled-flow, Apex, REST and orchestration rows, and the `$Permission` example after the table, are unverified.

These global merge fields always resolve against the **running user**, but the definition of "running user" depends on the flow context:

| Flow context | Running user resolved as |
|---|---|
| Screen Flow | The interactive session user |
| Record-triggered after-save (System Context) | The user whose DML triggered the flow |
| Scheduled flow | Automated Process user (NOT the flow creator) |
| Platform-event-triggered flow | The user who published the event message; the debug log appears under Automated Process (platform_events 264 L2190-2192) |
| Auto-launched from Apex | The Apex caller's running user (subject to `System.runAs` in tests) |
| Auto-launched from REST API | The API caller |
| Orchestration stage assigned to a queue | The user who claims the work item |

A common bug: a scheduled flow checks `$Permission.Edit_Sensitive_Data` to decide a branch — but Automated Process user has no permission set assignments, so the check always returns `false`. The flow silently takes the wrong branch.

Do not use `$Permission` checks as a substitute for an explicit run-mode decision. Run mode controls what the flow can do at the platform level; `$Permission` is just a feature toggle that the flow logic happens to read.

---

## Common Patterns

### Pattern 1 — User Context UI + System Context Subflow

**When to use:** A Screen Flow needs to update a record the user can't see (e.g., assigning a Case to a queue the user is not a member of, or updating a parent Account's last-touched date when the user has read-only on the parent).

**How it works:**

```
[Screen Flow — User Context]                  [Auto-launched Subflow — System Context Without Sharing]
   ┌────────────────────┐                          ┌────────────────────────────┐
   │ Capture user input │ ── invoke subflow ──>    │ Update parent Account      │
   │ (in user's context)│                          │ Insert audit log record    │
   └────────────────────┘                          │ Return success/failure flag│
              │                                    └────────────────────────────┘
              ▼
   ┌────────────────────┐
   │ Show confirmation  │
   │ to user            │
   └────────────────────┘
```

The Screen Flow stays in User Context — the user only sees fields they're entitled to. The subflow is configured as System Context Without Sharing and does the privileged write. Pass only the minimum fields needed (record Id + the new value) — never let the subflow re-read user-visible data and round-trip it back to the UI.

**Why not the alternative:** Setting the entire Screen Flow to System Context Without Sharing exposes every Get Records and Display Field to bypass FLS — meaning a screen that should show only the user's allowed fields suddenly shows everything. The bug surfaces months later when an auditor asks why an intern saw the CEO's compensation.

### Pattern 2 — Without Sharing for Bulk Reparenting

**When to use:** A scheduled or batch-replacement flow needs to reassign ownership of Cases from a departing rep to a queue, even when the running Automated Process user has no specific share grants.

**How it works:**

- Flow type: Scheduled (auto-launched).
- Overall run mode: **System Context Without Sharing** (default for auto-launched, but make it explicit in the XML).
- Document in the flow description: "Runs as Automated Process user with full data access — required for cross-team reparenting. Audit log written to Reparenting_Log__c per record."
- Add an Audit Log subflow that records who triggered the reparenting batch and which records were affected.

**Why not the alternative:** Trying to enforce sharing on a bulk reparenting flow forces the Automated Process user to be granted explicit shares to every record — operationally infeasible. The right answer is to escalate run mode AND add compensating audit controls.

### Pattern 3 — FLS-Bypass Audit

**When to use:** Periodic security review of all active flows; triage list for `agents/flow-analyzer/AGENT.md` audit-mode runs.

**How it works:**

```bash
# Pull active Flow metadata from the org
sf project retrieve start --metadata Flow

# Inventory run-mode settings
grep -l "<runInMode>SystemModeWithoutSharing</runInMode>" force-app/main/default/flows/

# Inventory flows that depend on the Spring '21 default (UNVERIFIED (2026-10-20): the default and the 52.0 cutover are not in the corpus)
for f in force-app/main/default/flows/*.flow-meta.xml; do
  api=$(grep -oP '(?<=<apiVersion>)[^<]+' "$f")
  mode=$(grep -oP '(?<=<runInMode>)[^<]+' "$f")
  if [[ -z "$mode" && $(echo "$api >= 52.0" | bc) -eq 1 ]]; then
    echo "IMPLICIT WITHOUT-SHARING: $f (api=$api)"
  fi
done
```

Every flow returned should be classified:
- **Justified without-sharing** (bulk reparenting, system maintenance, audit-log writes) — annotate the flow description and move on.
- **Unjustified without-sharing** (sales rep inquiry screen, customer self-service Experience Cloud flow) — file P0 ticket to convert to User Context or User Context + targeted subflow.

**Why not the alternative:** Trusting flow authors to remember the security implications of the default does not scale. A repeatable audit script is the only defensible posture under SOX / HIPAA / FedRAMP.

---

## Decision Guidance

| Flow Type + Use Case | Recommended Run Mode | Reason |
|---|---|---|
| Screen Flow used by sales reps to update their own Opportunities | **User Context** | FLS + sharing must hold; user can only see their own data anyway. |
| Screen Flow that needs to read 1 lookup the user can't see (queue owner) | **User Context** + a subflow with `SystemModeWithSharing` for that one read | Minimum escalation; document why. |
| Screen Flow on Experience Cloud (guest or community user) | **User Context** (mandatory for guest); never escalate without security review | Guest user can leak data org-wide if escalated. |
| Record-triggered after-save flow updating a related child record | **System Context With Sharing** | Allows automated work without bypassing sharing rules; safer than the without-sharing default. |
| Record-triggered after-save flow reparenting / bulk-fixing data | **System Context Without Sharing** | Required when the triggering user can't see all related records; audit log mandatory. |
| Record-triggered before-save flow | **System Context** (forced — setting is ignored) | UNVERIFIED (2026-10-20): not in the corpus; document for clarity. |
| Scheduled flow doing nightly maintenance | **System Context Without Sharing** | Automated Process user has no shares; escalation required. |
| Platform-event-triggered flow consuming integration events | **System Context Without Sharing** | Same rationale as scheduled. |
| Auto-launched flow invoked from Apex | Inherit Apex caller's mode OR explicit System Context With Sharing | Make the boundary explicit; avoid surprises when Apex changes from `with sharing` to `without sharing`. The Apex Reference: run the flow or Apex on API version 62.0 or later with the class declared `with sharing` and the flow "enforces the sharing rules of the user that executes the Apex class" (apexref 262 L157958-157961). |
| Orchestration stage assigned to a human queue | **User Context** | Stage runs as the queue claimant; standard user permissions apply. |
| Approval-process replacement (Orchestrator) using `$Permission` for routing | **User Context** | `$Permission` only resolves correctly for human users. |

---

## Recommended Workflow

1. **Identify the flow's trigger and default mode.** Record-triggered after-save? Screen? Scheduled? Look up the default from the table in Concept 1. Note the API version — anything below 52.0 has different defaults (UNVERIFIED (2026-10-20): the version-dependent defaults are not in the corpus; `DefaultMode` depends on how the flow is launched, api_meta 264 L70908-70909).
2. **Classify data sensitivity.** What objects does the flow read and write? Are any classified HR, Comp, Health, Financial, or Personal? Sensitive data raises the bar — User Context is the default unless escalation is justified in writing.
3. **Map the running user.** Who is the running user under each invocation path? For scheduled flows this is Automated Process (UNVERIFIED (2026-10-20): not in the corpus); a platform-event-triggered flow interview runs as the user who published the event, with only its debug log under Automated Process (platform_events 264 L2190-2192). Flag any `$User`/`$Permission` references that won't resolve correctly.
4. **Choose the overall run mode.** Use the Decision Guidance table. Default to User Context for screen flows; default to System Context With Sharing for record-triggered flows that don't need to bypass sharing; only choose Without Sharing with a justification block in the flow description.
5. **Identify escalations.** If the flow is User Context but needs to read one specific record the user can't see, move that read into a subflow with `runInMode` `SystemModeWithSharing` (or `SystemModeWithoutSharing` if necessary) and document why. `runInMode` is not available on a single element (api_meta 264 L70907).
6. **Add an audit-log step for any without-sharing path.** Every System Context Without Sharing write should record source flow + record Id + running user to an audit table. This is the compensating control auditors require.
7. **Test with a low-privileged persona, then pin the API version.** Run the flow as a user with the minimum profile — confirm User Context paths fail closed (record not found / insufficient access) and System Context paths succeed for the documented reason. Then set `<apiVersion>` explicitly in the flow XML so a later "Save" in Flow Builder does not silently flip the default.

---

## Questions to Ask Before Configuring

Ask these before choosing a run mode. Each one maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which flow type is this, and how is it launched?" | `DefaultMode` depends on how the flow is launched (api_meta 264 L70908-70909) (gotchas 1, 5) | The launch path, so the effective context is stated, not assumed |
| "What `apiVersion` is the flow saved at, and is `runInMode` set?" | `UserMode` exists only from API 68.0 (api_meta 264 L70926-70927); the older defaults are UNVERIFIED (gotchas 5, 10) | `apiVersion` and `runInMode` pinned together |
| "Which objects and fields does the flow read, and how sensitive are they?" | System modes do not respect object permissions or field-level access (api_meta 264 L70912-70916) | A sensitivity tier per object, deciding the default |
| "Does one read or write need more access than the rest of the flow?" | `runInMode` is flow-level (api_meta 264 L70907), so the escalation is a subflow (gotcha 8) | The subflow and its own `runInMode`, with a written reason |
| "Who is the running user on each invocation path?" | A platform-event flow interview runs as the publishing user (platform_events 264 L2190-2192); other paths are UNVERIFIED (gotchas 2, 12) | A table of paths and running users, each tested |
| "Does anything depend on sharing that was just granted?" | Editing groups, roles and territories recalculates sharing rules, which "can take a while to complete" (secguide 262 L2302-2303) (gotcha 6) | A recalculation check before the flow runs |
| "Is this an Experience Cloud or guest-user entry point?" | Guest users start at Private org-wide defaults (secguide 262 L2868) (gotcha 11) | User Context confirmed, with a security review |

A proper configuration adds an explicit, pinned run mode per flow, a subflow for each escalation and a persona test, none of which "leaving the default" provides.

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Flow XML has explicit `<runInMode>` set (no reliance on implicit defaults).
- [ ] Flow XML has explicit `<apiVersion>` pinned to a known value.
- [ ] If `runInMode = SystemModeWithoutSharing`, flow description contains a justification block citing the data-access requirement.
- [ ] Any subflow that escalates `runInMode` is documented in its Flow description.
- [ ] No `$Permission` or `$User.UserRoleId` checks in flows whose running user is Automated Process (scheduled flows, UNVERIFIED (2026-10-20)); a PE-triggered flow runs as the publishing user (platform_events 264 L2190-2192).
- [ ] Screen Flows on Experience Cloud are User Context unless approved by security review.
- [ ] System Context Without Sharing flows write to an audit log per record affected.
- [ ] Test plan includes a low-privileged-user persona run to confirm User Context paths fail closed.
- [ ] Subflows have their own `runInMode` set explicitly (not assumed to inherit from parent).
- [ ] No Action element relies on bypass-the-sharing-rule semantics — Send Email Alert and similar honor their own enforcement.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Before-save record-triggered flows ignore the run mode setting** (UNVERIFIED (2026-10-20): not in the corpus). They always run in System Context as part of the triggering DML transaction. Configuring User Context on a before-save flow is silently ignored — leading to a false sense of security in code review.
2. **`$User` returns the *triggering* user, not the flow author or the Automated Process user, for after-save record-triggered flows** (UNVERIFIED (2026-10-20): not in the corpus). A flow that emails `$User.Email` to confirm a record change will email the user who saved the record — not the system or the original record owner. This often surfaces during cross-tenant data migrations where the running user is a sysadmin doing bulk loads.
3. **System Context Without Sharing inherits to subflows unless the subflow explicitly overrides** (UNVERIFIED (2026-10-20): the references of this package say the opposite, "there is no inheritance"; neither is in the corpus — set `runInMode` on every subflow and test). Calling a subflow from a without-sharing parent does not "reset" the security boundary. To escalate-then-de-escalate, the subflow must set its own `runInMode` to `SystemModeWithSharing` or be a Screen subflow (which always asserts User Context for its screens — but its DML elements still inherit).
4. **FLS still enforces in some Action elements regardless of run mode** (UNVERIFIED (2026-10-20): Send Email Alert, Chatter and Outbound Message behavior is not in the corpus; for Apex actions the access mode follows the class's `apiVersion`, apexdev 264 L11926-11929). Send Email Alert respects FLS on the merge fields it pulls into the email body. Post to Chatter respects FLS. Apex actions enforce record access per the class's own `with sharing` declaration and field access per the class's query idiom — two separate controls, and the field-access one is gated by the `apiVersion` in the class's `.cls-meta.xml` (see `references/gotchas.md` Gotcha 4). Setting the flow to System Context Without Sharing does NOT bypass these.
5. **Saving a legacy flow in Flow Builder bumps `apiVersion` and silently changes default run mode** (UNVERIFIED (2026-10-20): Spring '21 default; see Concept 3). A flow created at API 50.0 (User Context default) opened and saved in current Flow Builder gets bumped to the latest API version (System Context Without Sharing default) if `runInMode` was never explicitly set. The flow now bypasses sharing — and no diff in source control will warn you, because no element changed.
6. **The Profile of the user activating the flow can affect what gets deployed** (UNVERIFIED (2026-10-20): not in the corpus). Activating a flow whose embedded Apex action class is `private` or whose referenced object is hidden by FLS for the activator can silently strip metadata in some legacy edge cases. Always activate flows as a sysadmin with full data + metadata access.
7. **Orchestration stage assigned to a queue resolves `$User` to the claimant, but only after claim** (UNVERIFIED (2026-10-20): not in the corpus). Before the work item is claimed, `$User` references in the assigned stage are unresolved — formula evaluation defers. Test with both pre-claim and post-claim states.
8. **A platform-event-triggered flow interview runs as the user who published the event; only its debug log is under Automated Process** (platform_events 264 L2190-2192). CONTRADICTED (2026-10-20): the earlier text said standard PEs run as Automated Process and high-volume PEs as a "Run As" user. The configurable running user (`PlatformEventSubscriberConfig.user`) belongs to platform event Apex triggers, "By default, the platform event trigger runs as the Automated Process entity" (api_meta 264 L99183-99186; platform_events 264 L3017-3019), not to flows.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Run-mode recommendation | One of: User Context / System With Sharing / System Without Sharing — with one-paragraph justification citing data sensitivity and least-privilege. |
| Escalation list | Table of flows and subflows where `runInMode != DefaultMode`, with reason. |
| Audit findings | List of flows in scope whose current `runInMode` does not match the recommendation; classified as P0 (sensitive data + without-sharing default), P1 (justified but undocumented), P2 (defensible but should be tightened). |
| Test plan | Persona-based test cases: low-privileged user, peer user, sysadmin, Automated Process. Expected pass/fail for each. |
| Audit log schema | If recommending System Context Without Sharing, the schema for the per-record audit table (source flow, record Id, running user, timestamp). |

---

## Related Skills

- `apex/apex-managed-sharing` — when run-mode escalation isn't enough and the right answer is to grant explicit programmatic shares.
- `security/record-access-troubleshooting` — when a User Context flow can't see a record the user expects; debug at the sharing-rule level before changing run mode.
- `security/dynamic-sharing-recalculation` — when bulk run-mode changes affect downstream sharing calculations.
- `flow/flow-error-monitoring` — wire fault paths from System Context Without Sharing flows to a monitored audit log.
- `flow/auto-launched-flow-patterns` — subflow design where run-mode boundaries matter.
- `flow/record-triggered-flow-patterns` — broader patterns for record-triggered flows; this skill is the security overlay.
- `apex/apex-system-runas` — when designing tests for flows with explicit run-mode escalation.

---

## Official Sources Used

- Salesforce Help — Configure Flow Run Behavior: https://help.salesforce.com/s/articleView?id=platform.flow_distribute_run_user.htm
- Salesforce Help — Run-Mode Considerations for Flows: https://help.salesforce.com/s/articleView?id=platform.flow_considerations_run_user.htm
- Salesforce Help — How Does Flow Security Work?: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_security.htm
- Salesforce Spring '21 Release Notes — Default Run Mode for Record-Triggered Flows changed to System Context Without Sharing.
- Salesforce Developer — Apex Sharing Keywords (with sharing / without sharing / inherited sharing): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Salesforce Developer — Flow Metadata API (`runInMode` element): https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Salesforce Architects — Well-Architected Security Pillar: https://architect.salesforce.com/well-architected/trusted/secure
