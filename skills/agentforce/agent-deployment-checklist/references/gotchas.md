# Gotchas — Agent Deployment Checklist

Deployment failure modes that are specific to Agentforce and are not covered by
a general Salesforce release process.

---

## 1. An API version below 66.0 silently retrieves an incomplete agent

**What happens:** `sf project retrieve start` succeeds. The agent lands in the
target org missing its planner, subagents, or actions. No error mentions the API
version. (Subagents were called *topics* before April 2026; the metadata type is
still `GenAiPlugin`.)

**When it occurs:** any existing project whose `sourceApiVersion` or manifest
`<version>` predates the new agent metadata types — which is most projects,
since the default is set once at project creation and rarely revisited.

**The documented requirement:** API version 66.0 is required to support
`GenAiPlannerBundle` and the new agent metadata types
([Retrieve and Deploy Agent
Metadata](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html)).
The corpus targets 67.0.

**How to avoid:** pin `<version>` in the agent manifest explicitly rather than
inheriting the project default, and make "manifest version ≥ 66.0" a checklist
row. A silent partial retrieve is worse than a failure because it produces a
deployable artefact.

---

## 2. Wildcards on supporting types cause deployment timeouts

**What happens:** the manifest uses `<members>*</members>` for `ApexClass` to
"be safe." The retrieve runs for forty minutes and times out, or the deploy
package is enormous and the release window is blown.

**The documented behaviour:** using wildcards for `ApexClass`, `Flows`, and
`GenAiPromptTemplates` *"can pull excessive data, leading to very long
deployments or timeouts."*

**How to avoid:** enumerate exactly the classes, flows, and templates the agent
references. This has a second benefit — the enumerated list *is* the dependency
inventory, so a reviewer can see what the agent touches without opening the
Builder.

---

## 3. `BotVersion` alone fails into an org that has never had the agent

**What happens:** a team promotes a hotfix as a version-only deploy into a new
sandbox. It fails with a reference error that reads like a metadata problem.

**The documented rule:** *"Before deploying a single agent version into an org
(using `BotVersion`), you must have deployed the full agent to the org."*

**How to avoid:** two deployment shapes, chosen by target state — full agent
into a fresh org, version-only into an org that already has it. Put the
distinction in the runbook, because the failure message does not explain it.

---

## 4. A committed agent cannot be edited — every fix is a new version

**What happens:** production behaviour needs a one-word instruction change. The
team opens the committed version to edit it and cannot.

**The documented rule:** *"You can't edit a committed agent. Instead, create and
edit a new version."*

**How to avoid:** plan for it rather than discovering it. Two consequences for
the checklist: the hotfix path is the same path as a feature release (so its
duration is known, not hoped for), and the rollback target must be a *retained*
prior version — retention is a decision, not a default.

---

## 5. Authoring bundle version and Bot version are different counters

**What happens:** the wrong behaviour ships. The reviewed authoring bundle and
the deployed `BotVersion` were not the same generation of the agent.

**The documented behaviour:** committing creates the `Bot`/`BotVersion`
metadata; *"if you save more versions than you commit, the version of your
`AiAuthoringBundle` won't match the version of your `Bot`/`BotVersion`"*, and
you must specify the correct version numbers to pair them.

**How to avoid:** record both numbers on the activation record at commit time
and have the deploy script read them. Never reconstruct the pairing at release
time by counting in a UI.

---

## 6. Hand-editing retrieved metadata can corrupt the org

**What happens:** a developer opens the retrieved agent metadata to fix a
label — the exact instinct that is correct for every other metadata type — and
deploys it.

**The documented warning:** *"Don't modify the metadata that you retrieved.
Uploading edited metadata to an org can corrupt your org."*

**How to avoid:** treat retrieved agent metadata as a build artefact, not as
source. Changes go through the Builder and are re-retrieved. Enforce it with a
CODEOWNERS rule or a CI check that fails when agent bundle files are modified in
a PR that does not also refresh them wholesale.

---

## 7. The agent's runtime user is not part of the deployment

**What happens:** clean deploy, and every action fails in the target org with a
permission error while general conversation works fine.

**When it occurs:** every first promotion, because the permission model is org
configuration and the metadata carries no dependency on it.

**The documented behaviour:** the agent user must have sufficient permissions
for all its tasks, *including custom field access*, and agent usernames require
manual configuration after deployment unless string replacement is configured
beforehand.

**How to avoid:** the pre-activation user verification in
`references/examples.md` Example 4. The row that gets missed is field-level
access — object CRUD passes the smoke test and fails on the first custom field.
The only verification that covers CRUD, FLS, and sharing together is invoking
each action once as that user in the target org.

---

## 8. Session Tracing records nothing retroactively

**What happens:** an incident in week one. The team enables tracing to
investigate and gets data starting from the moment they enabled it. The
conversations that caused the incident are gone.

**The documented behaviour:** analytics and insights appear only for
conversations occurring **after** the Session Tracing Data Model is set up
([Set Up Agentforce Session
Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5)).

**How to avoid:** a blocking checklist row with a date field that must predate
activation, plus a synthetic-traffic test proving traces actually appear. Also
assign the Data Cloud User permission set to everyone who needs to read it —
tracing that nobody can open is tracing that does not exist during an incident.

---

## 9. Rollback reverts the agent and nothing that shipped with it

**What happens:** v3 is rolled back to v2. The agent's configuration reverts.
The Apex classes, custom fields, and activated prompt template that shipped
alongside v3 do not. v2 now calls Apex whose signature it does not match.

**When it occurs:** any release where the agent change required a supporting
code or configuration change — which is most of them.

**How to avoid:** the rehearsal must include an explicit "what did *not* revert"
inventory (Example 3). Two design responses:

- **Backward-compatible actions.** An action that adds an optional input works
  for both versions; one that renames a required input does not. Prefer additive
  changes so the rollback surface stays small.
- **Prompt templates roll back separately.** Only one version of a template can
  be active at a time, so reverting the agent does not revert the template — see
  `agentforce/prompt-template-versioning`.

---

## 10. Rehearsing in a sandbox that cannot reproduce the behaviour

**What happens:** the rehearsal is green in a developer sandbox. In production
the rollback behaves differently because grounding returns different content and
the volume changes the timing.

**How to avoid:** rehearse in Partial or Full, refreshed recently, and record
the sandbox type and refresh age on the activation record so a reviewer can
weight the evidence. Agent behaviour depends on retrieved content, so "same
metadata" is not grounds to expect "same behaviour."

---

## 11. Alert rules configured but never fired

**What happens:** monitoring is ticked on the checklist. The first genuine
incident produces no page, because the rule's threshold was never exercised and
the notification path was never tested.

**How to avoid:** the checklist row is not "alerts configured" but "alerts
fired at least once against synthetic traffic, and the on-call person confirmed
receipt." Configuration and function are different claims, and only the second
one matters at 3am.

---

## 12. Sign-off recorded in chat

**What happens:** a quarterly audit asks who approved the activation. The answer
is a Slack thread in a channel with 90-day retention, in a workspace that has
since been reorganised.

**How to avoid:** the `Agent_Activation__c` record with lookup fields and a
validation rule that blocks save on missing approvals. The properties that
matter are queryable, immutable, and linked to the specific version — chat has
none of the three. "Show every activation last quarter where rollback was not
rehearsed" should be a report, not an interview.

---

## 13. The checklist lives in a document with no enforcement

**What happens:** the checklist is a well-written Google Doc. Under release
pressure, three rows go unticked and the activation happens anyway, because
nothing prevented it.

**How to avoid:** the enforcement is a validation rule on the activation record,
not the checklist's contents. A checklist that cannot block is a memory aid, and
memory aids fail exactly when the pressure is highest — which is the same
occasion on which the rows matter most.

---

## 14. A new channel bypasses the gates entirely

**What happens:** the agent is promoted from an internal console to a public
Experience Cloud site by ticking a box. No review, because "the agent didn't
change."

**Why it is a deployment event:** the channel sets the threat model. Guest and
unauthenticated users change every PII classification made under an
internal-audience assumption, and the adversarial suite was written for a
cooperative population.

**How to avoid:** record `Channels_At_Activation__c` on the activation record so
adding one is visibly a change to an approved condition. Re-run the security
gate, the PII register review, and the adversarial suite. See
`agentforce/agentforce-pii-redaction` for why the register is channel-dependent.
