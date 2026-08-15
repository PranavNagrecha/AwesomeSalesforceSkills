# Gotchas — Prompt Template Versioning

---

## 1. Prompt Builder does have version history — designs built on the opposite premise are wrong

**What happens:** a team builds an elaborate "version history" layer — one
template per version, an external copy of every prompt body, a spreadsheet of
past text — to solve a problem the platform already solves.

**The documented behaviour:** you can create and use multiple versions of a
prompt template in Prompt Builder, and control which one users reach through
activation and deactivation
([Use Multiple Versions of a Prompt
Template](https://help.salesforce.com/s/articleView?id=sf.prompt_builder_use_multiple_versions.htm&type=5)).
The metadata carries every retained version in `templateVersions`, each with its
own `versionNumber`, `versionIdentifier`, `status`, and `content`, and
`activeVersionIdentifier` names the live one
([GenAiPromptTemplate](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm)).

**How to avoid:** start from what the platform provides. The genuine gaps are
*promotion latency* and *concurrent variants*, not history — and only the second
is a hard platform limit.

---

## 2. Only one version can be active at a time — there is no built-in traffic split

**What happens:** a team plans a 90/10 A/B by "setting weights on the subagent"
(called a topic before April 2026) and discovers no such configuration exists.

**The documented behaviour:** activation and deactivation control which version
users can access, and **only one version can be active at a time**
([Activate and Deactivate Prompt
Templates](https://help.salesforce.com/s/articleView?id=sf.prompt_builder_activate_deactivate_templates.htm&type=5)).

**How to avoid:** concurrent variants require **two templates** and a resolver in
your own code that chooses between them per user or per request. The platform
supplies versioning; you supply routing. Treat the resolver as temporary
scaffolding for the duration of the canary, not as permanent architecture.

---

## 3. Consumers coupled to a version number make rollback as expensive as release

**What happens:** Flows and Apex reference `SalesEmail_v3` by name. Promoting to
v4 means editing and deploying every consumer. So does rolling back — in an
incident, under pressure.

**How to avoid:** consumers reference the **template**, and the version is chosen
by `activeVersionIdentifier`. If your deploy path is too slow even for that, add
one slot-based indirection layer (`references/examples.md` Example 2) — but adopt
it because you measured the deploy time, not because it sounds sophisticated.

---

## 4. Promotion is a metadata deploy, so "instant rollback" is a claim about your pipeline

**What happens:** the runbook says rollback takes 30 seconds. In practice it
takes 40 minutes because production deploys require two approvals and a window.

**How to avoid:** measure it. Rehearse the rollback and record the wall-clock
time on the release record, the same way
`agentforce/agent-deployment-checklist` treats agent rollback. If the measured
number does not meet the requirement, that is the evidence for adding
indirection — and the only good evidence for it.

---

## 5. A new required input breaks at invocation, not at deploy

**What happens:** v4 adds a required input. The deploy succeeds. Every
invocation fails afterwards.

**Why:** `GenAiPromptTemplateVersion.inputs` entries carry a `required` flag.
Nothing at deploy time checks that consumers supply the new input, because
consumers are Flows, Apex, and agent actions with no static link to the
template's input list.

**How to avoid:** the ordering rule is absolute — **deploy consumers first,
activate second.** And structure the consumer to handle both versions during the
overlap, because a consumer that only handles v4 removes your rollback.

---

## 6. `responseFormat` and `outputSchema` changes break parsers silently

**What happens:** v4 switches `responseFormat` from `MarkDown` to `JSON` for
tidiness. A downstream LWC that rendered the markdown now displays raw JSON, or
an Apex parser reads the wrong values without throwing.

**The fields:** `responseFormat` takes `HTML`, `JSON`, or `MarkDown`;
`outputSchema` constrains the JSON shape.

**How to avoid:** before promoting, ask whether anything *parses* this output. If
yes, the format change is a coordinated release with the consumer, not a prompt
edit. Add the structural diff from `references/examples.md` Example 4 to the
pre-promotion checklist so the question is asked automatically.

---

## 7. `primaryModel` changes mean the goldens are stale even when the text is identical

**What happens:** v4 differs from v3 only in `primaryModel`. The team treats it
as a non-change because the prompt text is byte-identical, and skips the
regression run.

**How to avoid:** the model is part of the version envelope precisely because it
changes behaviour. Any diff touching `primaryModel` triggers a full golden run
before promotion. See `agentforce/agentforce-prompt-versioning` for the pinning
strategy and the quarterly re-evaluation cadence.

---

## 8. Grounding changes are a security event, not a content edit

**What happens:** v4 adds a `templateDataProvider` for a new object to improve
answers. Nobody reviews what fields that object exposes.

**Why it matters more here than elsewhere:** for agents, pattern-based and
field-based LLM data masking is disabled — the Trust Layer does not scrub prompt
content. New grounding means new data reaching a model with no platform filter
in front of it.

**How to avoid:** any diff touching `templateDataProviders` re-opens the PII
register review in `agentforce/agentforce-pii-redaction`. Make it a labelled
gate, because a grounding addition looks like a quality improvement and reviews
as one.

---

## 9. `GenAiPromptTemplate` must deploy before anything that references it

**What happens:** a release deploying a template and a scorer together fails with
a reference error.

**The rule:** the Metadata API deploys types in the order they appear in
`package.xml`, so `GenAiPromptTemplate` must appear before
`AiAgentScorerDefinition` — the template must exist before the scorer that
references it can deploy successfully.

**How to avoid:** put prompt templates early in the manifest as a standing
convention. They are a dependency of agents, scorers, Flows, and Apex, never the
reverse.

---

## 10. Deleting a retired version removes your rollback target

**What happens:** v3 is deleted during a tidy-up sprint. Two weeks later v4 needs
reverting and there is nothing to revert to.

**How to avoid:** retention is a decision with a date, not a cleanup instinct.
Keep at least the two prior versions. Retire on a schedule — 0% traffic (or
deactivated) for a defined observation period, then delete — and record the
retirement date. `status` on each version is `Published` or `Draft`, so a
retained-but-not-active version costs only file size.

---

## 11. Editing directly in Setup diverges the org from the repository

**What happens:** a quick tone fix is made in Prompt Builder in production. A
week later a deploy from the repo silently reverts it, and nobody can explain the
behaviour change.

**How to avoid:** pick one authority and enforce it. If the repository is
authoritative, UI edits are retrieved within 24 hours or reverted. Detect drift
by retrieving on a schedule and diffing:

```bash
sf project retrieve start --metadata GenAiPromptTemplate --target-org prod
git diff --exit-code force-app/main/default/genAiPromptTemplates/ \
  || echo "DRIFT: org and repo disagree on prompt templates"
```

Run it nightly. The failure this catches is silent, so it needs an automated
detector rather than a convention.

---

## 12. CMDT indirection widens who can change production behaviour

**What happens:** the binding layer is added for rollback speed. Six months
later, changing which prompt version serves customers is available to anyone with
"Customize Application", and it happens without a review.

**How to avoid:** if you adopt indirection, deploy the binding records as
metadata so a change is still a reviewable commit, and restrict direct CMDT edit
rights in production. The pattern's whole justification is faster controlled
change — uncontrolled change is a regression, not a feature.

---

## 13. A canary with no variant tag produces no conclusion

**What happens:** 10% of reps get v4 for a week. At the end, nobody can say which
emails came from which version, so the decision is made on anecdote.

**How to avoid:** emit the variant assignment at resolution time — slot, variant,
template, user, timestamp — before the ramp starts. Attribution cannot be
retrofitted onto conversations that have already ended. This is the single most
common reason a canary produces no answer.

---

## 14. Non-deterministic bucketing makes the experience incoherent

**What happens:** the resolver randomises per invocation. A rep gets v4 at 9am
and v3 at 11am, notices the inconsistency, and reports it as a bug — which it is.

**How to avoid:** bucket deterministically on a stable key (user id), so a given
user's assignment does not change during the experiment. Random-per-call is
statistically tidy and experientially wrong, and users notice.
