# LLM Anti-Patterns — Agent Deployment Checklist

---

## Anti-Pattern 1: A generic release checklist with "agent" substituted in

**What the LLM generates:** code review, unit tests pass, deploy to staging,
smoke test, deploy to production, monitor. Every row is true and none is
specific to an agent.

**Why it happens:** "deployment checklist" is a dense, well-covered concept and
the model produces the strongest generic instance. Nothing in the request signals
that agent deployment has failure modes that no application release has.

**Correct pattern:** the rows that only exist here — committed agents cannot be
edited so every fix is a new version; the authoring bundle and Bot version are
different counters that must be paired by hand; the runtime user's permissions
are not part of the deployment; observability records nothing retroactively;
rollback reverts the agent but not the Apex, fields, or prompt template that
shipped with it. A checklist without those is a checklist for something else.

**Detection hint:** could you find-and-replace "agent" with "app" and have it
still read correctly? Then it has no agent-specific content.

---

## Anti-Pattern 2: `Bot` and `BotVersion` as the complete metadata set

**What the LLM generates:** a `package.xml` listing `Bot` and `BotVersion`,
sometimes `GenAiPlanner`.

**Why it happens:** Einstein Bots used `Bot`/`BotVersion` and has years of
documentation behind it. Agentforce inherited the type names, so the shape looks
current while being incomplete — and `GenAiPlanner` is the *previous* generation
of the planner type.

**Correct pattern:** the documented agent metadata set is `AiAuthoringBundle`,
`Bot`, `BotVersion`, `ConversationVariable`, `GenAiFunction`,
`GenAiPlannerBundle`, and `GenAiPlugin`
([Agentforce Metadata
Types](https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html)).
Which you need depends on draft vs. committed state, plus explicitly named
supporting `ApexClass`, `Flow`, and `GenAiPromptTemplate` members.

**Detection hint:** `GenAiPlanner` without `Bundle`, or a manifest with no
`AiAuthoringBundle`. Also check `<version>` — below 66.0 the new types are not
available and the retrieve silently returns less than you asked for.

---

## Anti-Pattern 3: Wildcards "to be safe"

**What the LLM generates:**

```xml
<types><members>*</members><name>ApexClass</name></types>
```

**Why it happens:** wildcards are the standard defensive move in metadata
manifests, and completeness reads as the safer default.

**Correct pattern:** the documentation warns that wildcards for `ApexClass`,
`Flows`, and `GenAiPromptTemplates` can pull excessive data and cause very long
deployments or timeouts. Enumerate what the agent references — the list doubles
as the dependency inventory a reviewer needs.

**Detection hint:** any `*` in an agent manifest. In this context it is a
performance bug, not a convenience.

---

## Anti-Pattern 4: "Edit the agent and redeploy" as the hotfix path

**What the LLM generates:** a rollback procedure of the form "revert the change
in the Builder and deploy the corrected version."

**Why it happens:** edit-and-redeploy is the correct hotfix path for essentially
every other Salesforce artefact.

**Correct pattern:** *"You can't edit a committed agent. Instead, create and
edit a new version."* The hotfix path is a new version, with the same steps and
therefore the same duration as a feature release — which changes the incident
plan, because "quick fix" is not available.

**Detection hint:** any procedure that modifies an existing committed version.

---

## Anti-Pattern 5: Treating rollback as complete when the agent version reverts

**What the LLM generates:** "activate the previous agent version — rollback
complete."

**Why it happens:** the agent is the thing being deployed, so reverting the
agent reads as reverting the release. The model does not track that a release
usually bundles Apex, fields, and prompt templates on independent lifecycles.

**Correct pattern:** enumerate what did *not* revert. Apex classes stay at the
new version, custom fields remain, and an activated prompt template stays active
because only one version of a template can be active at a time. If the new
version changed an action signature, the rolled-back agent may be calling Apex it
does not match.

**Detection hint:** the rollback plan has one step. Real ones have an inventory.

---

## Anti-Pattern 6: Omitting the runtime user entirely

**What the LLM generates:** a thorough metadata and testing checklist with no
mention of which user the agent runs as or what that user can see.

**Why it happens:** the permission model is org configuration, invisible in the
metadata, and orthogonal to the deployment mechanics the model is reasoning
about.

**Correct pattern:** a pre-activation block covering Apex class access, object
CRUD, **field-level** access, Flow access, Named Credential access, sharing
(records, not just objects), and the Data Cloud User permission set for reading
session traces. Verified by invoking each action once as that user in the target
org — the only check that exercises CRUD, FLS, and sharing together.

**Detection hint:** the checklist has no permission rows. This is the single
most common cause of "deploy succeeded, agent broken."

---

## Anti-Pattern 7: Enabling monitoring after go-live

**What the LLM generates:** a checklist ordered deploy → activate → configure
monitoring, on the reasonable ground that you monitor a running system.

**Why it happens:** it is the standard order for stateless application
monitoring, where metrics are computed from traffic that arrives after
instrumentation and nothing is lost by starting late.

**Correct pattern:** Session Tracing records only conversations occurring after
the Data Model is set up. Enabling it during an incident produces data starting
from the incident. It is a blocking pre-activation row with a date field that
must predate activation.

**Detection hint:** any monitoring row positioned after the activation row.

---

## Anti-Pattern 8: "Alerts configured" as the monitoring row

**What the LLM generates:** `[ ] Configure alerts for error rate and latency`.

**Why it happens:** configuration is the actionable verb and the observable
deliverable.

**Correct pattern:** the claim that matters is that an alert *fired* and someone
*received* it. Synthetic traffic before activation is the cheapest way to prove
the whole path. A configured alert with an untested notification route is a
tickbox, and it is the tickbox that fails at 3am.

**Detection hint:** the monitoring rows use "configure", "set up", or "enable"
and never "fired" or "received".

---

## Anti-Pattern 9: Inventing deployment APIs and gates

**What the LLM generates:** `sf agent deploy`, `sf agent activate --version 3`,
an `<activationStatus>` element in the agent metadata, or an `agentforce.yml`
config file.

**Why it happens:** the highest-risk Agentforce failure mode. The CLI has a real
`agent` topic (`sf agent test run` exists), so `sf agent deploy` interpolates
cleanly and reads as obviously correct. Rapid renaming — Einstein Copilot →
Agentforce, `GenAiPlanner` → `GenAiPlannerBundle` — makes plausible-but-wrong
names abundant.

**Correct pattern:** deployment uses the ordinary source commands —
`sf project retrieve start --manifest …` and `sf project deploy start
--source-dir …`. Verify any `sf agent …` subcommand against the CLI command
reference before it enters a runbook.

**Detection hint:** an `sf agent` subcommand other than the documented testing
commands, or an activation flag on a deploy command.

---

## Anti-Pattern 10: A checklist with no enforcement mechanism

**What the LLM generates:** a beautifully organised markdown checklist,
delivered as the artefact.

**Why it happens:** the request was for a checklist and markdown is the
canonical form. Enforcement is a separate concern in a separate system and does
not appear unless asked for.

**Correct pattern:** the checklist's rows become fields on `Agent_Activation__c`
with a validation rule that blocks save on missing approvals or null gate
results. A document cannot block an activation, and the rows matter most under
exactly the pressure that causes a document to be skipped.

**Detection hint:** the deliverable is a file and nothing in it can fail a
deploy. Ask: what physically prevents activation with three rows unticked?

---

## Anti-Pattern 11: Treating a channel addition as configuration, not deployment

**What the LLM generates:** channel enablement listed under "post-launch
enhancements" or omitted from the checklist entirely.

**Why it happens:** in the UI it is a toggle, and toggles are configuration. The
model has no representation of the channel as the thing that sets the threat
model.

**Correct pattern:** a new channel re-opens the security gate, the PII register
review, and the adversarial suite, because guest and unauthenticated users
invalidate every classification made under an internal-audience assumption.
Record the channel set on the activation record so adding one is visibly a
change to an approved condition.

**Detection hint:** the checklist has no channel row, or lists channels without
tying them to a review gate.
