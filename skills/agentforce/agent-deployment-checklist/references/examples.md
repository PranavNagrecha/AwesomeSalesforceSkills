# Examples — Agent Deployment Checklist

The checklist exists because agent deployment has failure modes that ordinary
Salesforce deployment does not: metadata that cannot be edited after commit,
versions that must be matched by hand across two bundles, a runtime user whose
permissions are invisible in the deploy, and observability that only records
data from the moment it is switched on.

---

## Example 1 — The `package.xml` that actually retrieves an agent

### Context

A team is promoting an agent from a sandbox to production for the first time.
Their manifest lists `Bot` and `BotVersion` — the shape they learned from
Einstein Bots — and the deploy lands an agent with no subagents (called *topics*
before April 2026) and no actions.

### Problem

Modern Agentforce agents are not one metadata type. Which types you need depends
on whether the agent is **draft** or **committed**, and the required API version
is higher than most existing projects use.

### Solution

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

    <!-- Draft agent authored in the new Agentforce Builder. -->
    <types>
        <members>Resort_Manager</members>
        <name>AiAuthoringBundle</name>
    </types>

    <!-- Committed agent: AiAuthoringBundle PLUS Bot and BotVersion. -->
    <types>
        <members>Resort_Manager</members>
        <name>Bot</name>
    </types>
    <types>
        <!-- Version-qualified. Deploying a single version requires that the
             full agent has already been deployed to the target org. -->
        <members>Resort_Manager.v2</members>
        <name>BotVersion</name>
    </types>

    <!-- Supporting resources the agent references. NAME THEM EXPLICITLY. -->
    <types>
        <members>CloseCaseAction</members>
        <members>GetRoomBalance</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Create_Service_Request</members>
        <name>Flow</name>
    </types>
    <types>
        <members>RefundStatusSummary</members>
        <name>GenAiPromptTemplate</name>
    </types>

    <!-- API version 66.0 or later is required for GenAiPlannerBundle and the
         other new agent metadata types. An older project default silently
         retrieves an incomplete agent. -->
    <version>67.0</version>
</Package>
```

```bash
sf project retrieve start --manifest manifest/package.xml --target-org sandbox
sf project deploy start   --source-dir force-app --target-org production
```

### The four things that bite

1. **API version.** Below 66.0, `GenAiPlannerBundle` and the new agent metadata
   types are not available. The retrieve succeeds and returns less than you
   asked for.
2. **No wildcards on the supporting types.** Using `*` for `ApexClass`, `Flow`,
   or `GenAiPromptTemplate` *"can pull excessive data, leading to very long
   deployments or timeouts"*. Name what the agent references.
3. **`BotVersion` needs the full agent first.** *"Before deploying a single agent
   version into an org (using `BotVersion`), you must have deployed the full
   agent to the org."* A version-only promotion into a fresh org fails.
4. **Do not hand-edit retrieved metadata.** The guide is explicit: *"Don't
   modify the metadata that you retrieved. Uploading edited metadata to an org
   can corrupt your org."* Changes belong in the Builder, then re-retrieve.

Source for all four: [Retrieve and Deploy Agent
Metadata](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html).

---

## Example 2 — Version mismatch between the authoring bundle and the Bot

### Context

An agent has been saved eleven times in the Builder and committed three times.
The team retrieves and deploys. The target org ends up with a `BotVersion` whose
behaviour does not match the authoring bundle they reviewed.

### Problem

Committing an agent version creates the `Bot`/`BotVersion` metadata. Saves and
commits are different counters. *"If you save more versions than you commit, the
version of your `AiAuthoringBundle` won't match the version of your
`Bot`/`BotVersion`, and you'll need to specify the correct version numbers to
match the correct `AiAuthoringBundle` to the correct `Bot` and `BotVersion`."*

### Solution — record the pair, don't infer it

Make the version pair an explicit field on the activation record rather than
something reconstructed at deploy time:

```text
Agent_Activation__c
  Agent_Api_Name__c            Resort_Manager
  Authoring_Bundle_Version__c  11        <- saves
  Bot_Version__c               v3        <- commits
  Committed_By__c              User lookup
  Committed_At__c              DateTime
```

The deploy step reads `Bot_Version__c` to build the `<members>Resort_Manager.v3`
entry. Nobody counts saves in a UI at release time.

### The related trap

*"You can't edit a committed agent. Instead, create and edit a new version."*
A hotfix is therefore always a new version, never an in-place tweak — which
means the rollback target is a *previous version that still exists*, and
retaining it is a deliberate act. See Example 4.

---

## Example 3 — Rollback rehearsal that produces facts instead of confidence

### Context

The runbook says "if v3 misbehaves, roll back to v2." Nobody has done it.

### Problem

"We have a rollback" is a belief. In an incident you need three numbers you can
only get by doing it: how long it takes, what happens to conversations that are
mid-flight, and what does *not* roll back.

### Solution — a scripted rehearsal in a representative sandbox

```text
ROLLBACK REHEARSAL — Resort_Manager v3 -> v2
Sandbox: Full, refreshed 2026-08-04 (10 days old)
Rehearsed by: <name>   Observed by: <name>   Date: 2026-08-14

T+0:00  Start one conversation on v3. Reach turn 3 (mid-task, action pending).
T+0:20  Activate v2 in Setup.
T+0:35  v2 reported active in Setup.
T+1:10  New conversation started -> served by v2. CONFIRMED.
T+1:10  The v3 conversation left running at turn 3:
          OBSERVED: ______________________________________
          (finished on v3 / errored / silently switched — record which)
T+2:00  Verify the three things that DID NOT roll back:
          [ ] Apex classes deployed with v3 — still v3 code. Is v2 compatible?
          [ ] Custom fields added for v3 — still present. Harmless?
          [ ] Prompt template activated for v3 — still active. Reverted separately?
T+3:00  Verify observability still reporting after the flip.

MEASURED ROLLBACK TIME: ____ minutes
KNOWN SIDE EFFECTS: _________________________________________
OWNER FOR THE REAL EVENT: ___________________________________
```

### Why the "did not roll back" section is the point

Activating a previous agent version reverts the agent's configuration. It does
not revert the Apex, the custom fields, or an activated prompt template that
shipped alongside it. If v3's action signature changed, v2 may now be calling
Apex it does not match. The rehearsal is what turns that from a discovery during
an incident into a line in the runbook.

**Sandbox representativeness matters more here than in most rehearsals**, because
agent behaviour depends on retrieved content. A developer sandbox with three
Knowledge articles cannot rehearse the grounding behaviour of a production agent.
Record the sandbox type and refresh age on the checklist, so a reviewer can
judge how much the rehearsal proves.

---

## Example 4 — The runtime user, which the deploy does not carry

### Context

Everything deploys clean. In production the agent answers general questions
correctly and fails every action with a permission error.

### Problem

An agent executes as a user. That user's permissions are org configuration, not
part of the agent metadata. The docs note that the agent user must have
sufficient permissions for all its tasks *including custom field access*, and
that agent usernames require manual configuration after deployment unless
string replacement is configured beforehand.

### Solution — a pre-flight the deploy cannot do for you

```text
AGENT RUNTIME USER — PRE-ACTIVATION VERIFICATION
Agent: Resort_Manager v3     Target org: PROD

[ ] Agent user exists in target org and is Active
[ ] Username matches the value the deployed metadata expects
      (or string replacement was configured before deploy)
[ ] Permission set group assigned, containing:
      [ ] Apex class access: CloseCaseAction, GetRoomBalance
      [ ] Object CRUD for every object any action touches
      [ ] FIELD-LEVEL access for every field any action reads or writes
            <- the row that is missed; object access is not field access
      [ ] Flow access: Create_Service_Request
      [ ] Named Credential access: ERP_Orders
      [ ] Data Cloud User (required to see Session Tracing output)
[ ] Sharing: can the agent user see the RECORDS, not just the object?
[ ] Verified by invoking each action once as that user in the target org
```

### The check that finds it

Object-level access without field-level access is the classic. It passes every
smoke test that reads a name and fails the moment an action reads a custom
field. The last row — actually invoking each action as that user — is the only
verification that covers CRUD, FLS, and sharing at once.

---

## Example 5 — Observability before activation, not after

### Context

Week one in production. A supervisor reports odd behaviour. The team goes to
inspect the session traces and finds nothing.

### Problem

Agentforce Session Tracing records only conversations that happen **after** the
Session Tracing Data Model is set up
([Set Up Agentforce Session
Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5)).
The first week is unrecoverable. Enabling tracing during an incident produces
data starting from the incident.

### Solution — a blocking checklist row with an evidence field

```text
OBSERVABILITY — must be GREEN before activation

[ ] Setup > Einstein Audit, Analytics, and Monitoring Setup:
      [ ] Agentforce Session Tracing enabled ....... date: ________
      [ ] Session Tracing Data Model enabled ....... date: ________
      [ ] Agentforce Optimization enabled .......... date: ________
[ ] "Data Cloud User" permission set assigned to everyone who must read it
      (supervisors, on-call, the named dashboard owner)
[ ] SYNTHETIC TRAFFIC TEST: ran 3 conversations in prod pre-activation and
      confirmed they appear in session-tracing data ....... evidence: ______
[ ] Alert rules active and fired at least once against synthetic traffic
[ ] On-call rota updated; named owner for the agent dashboard: __________
```

The synthetic-traffic row is what distinguishes a configured feature from a
working one. A tickbox in Setup and a visible trace are different claims.

---

## Example 6 — The activation record as the system of record

### Context

A quarterly audit asks who approved v3 and on what evidence. The answer is a
Slack thread in a channel with 90-day retention.

### Problem

Chat is not an audit trail: it is not queryable, not immutable, not linked to
the version it approved, and it disappears. Reconstructing a decision chain from
it after an incident is archaeology.

### Solution — one record per activation, with the checklist as fields

```text
Agent_Activation__c
  Agent_Api_Name__c              Resort_Manager
  Bot_Version__c                 v3
  Authoring_Bundle_Version__c    11
  Target_Org__c                  PROD

  -- Gate 1: functional
  Test_Suite_Run_Id__c           (from `sf agent test run` output)
  Test_Suite_Result__c           PASS / FAIL
  Adversarial_Suite_Result__c    PASS / FAIL

  -- Gate 2: security
  PII_Register_Reviewed_On__c    Date
  Channels_At_Activation__c      Multi-select — a new channel re-opens gate 2

  -- Gate 3: observability
  Session_Tracing_Enabled_On__c  Date  (must predate activation)
  Dashboard_Owner__c             User lookup

  -- Gate 4: rollback
  Rollback_Rehearsed_On__c       Date
  Rollback_Measured_Minutes__c   Number
  Rollback_Target_Version__c     v2
  Rollback_Known_Side_Effects__c Long text

  -- Gate 5: sign-off
  Business_Owner_Approval__c     User lookup
  Security_Approval__c           User lookup
  SRE_Approval__c                User lookup
  Approved_At__c                 DateTime
```

### What makes it a control rather than a form

- **A validation rule blocks save** unless all three approval lookups are
  populated and all four gate results are non-null. A missing row cannot be
  waved through, which is the entire difference between a checklist and a habit.
- **`Session_Tracing_Enabled_On__c` must predate `Approved_At__c`.** Encode it as
  a validation rule; it is the one ordering constraint that cannot be fixed
  retroactively.
- **`Channels_At_Activation__c` is a multi-select**, so adding a channel later is
  visibly a change to an approved condition rather than a configuration tweak.
- **It is queryable.** "Show every agent activated in the last quarter where
  rollback was not rehearsed" is a report, not an interview.

---

## Anti-Pattern — treating a channel addition as a configuration change

**What practitioners do:** the agent is live and stable on the internal Service
Console. A product manager asks for it on the Experience Cloud customer portal.
Somebody ticks the channel and it goes live the same afternoon.

**What goes wrong:** the channel determines the threat model, and nothing else
changed to signal it. On an internal console the users are employees, weakly
adversarial at worst. On a public portal, users may be unauthenticated, actively
adversarial, and outside your jurisdiction. Every PII classification made under
the assumption of an internal audience is now wrong, the adversarial test suite
was written for a cooperative population, and prompt injection moves from
theoretical to routine.

**Correct approach:** a new channel re-opens the same gates as a new agent —
security review, PII register re-review under the new trust level, adversarial
suite re-run, and a fresh sign-off. `Channels_At_Activation__c` exists so that
this is a visible change to an approved condition. The checklist is short enough
to re-run in a day; the incident is not.
