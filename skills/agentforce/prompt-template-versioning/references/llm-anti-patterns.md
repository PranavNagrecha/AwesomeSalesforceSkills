# LLM Anti-Patterns — Prompt Template Versioning

---

## Anti-Pattern 1: "Prompt Builder has no version history"

**What the LLM generates:** a design premised on the platform having no
versioning — one template per version, an external archive of prompt bodies, or
a custom object storing past text — usually stated as fact: *"Prompt Builder
overwrites on save, so the previous text is lost."*

**Why it happens:** it was a reasonable description of an early iteration of the
feature, and early-product content is over-represented relative to the
subsequent capability. The model reproduces the older state with full
confidence.

**Correct pattern:** Prompt Builder supports multiple versions with
activation/deactivation, and the metadata carries them all —
`templateVersions[]` with per-version `versionNumber`, `versionIdentifier`,
`status`, and `content`, plus `activeVersionIdentifier` naming the live one.
Build on it rather than around it.

**Detection hint:** any claim that saving destroys the previous version, or a
design whose stated justification is the absence of history.

---

## Anti-Pattern 2: Inventing a subagent-level traffic split

**What the LLM generates:**

```yaml
prompt_variants:
  - name: RefundStatusSummary_v2
    weight: 90
  - name: RefundStatusSummary_v3
    weight: 10
```

presented as agent or subagent configuration (subagents were called topics
before April 2026).

**Why it happens:** weighted variants are how every feature-flag and
experimentation platform works, so the shape is deeply familiar and interpolates
cleanly into a YAML-looking config. Nothing signals that the platform does not
offer it.

**Correct pattern:** **only one version of a prompt template can be active at a
time.** There is no platform traffic split. Concurrent variants require two
templates and a resolver in your own Apex or Flow that chooses per user. The
platform gives you versioning; routing is yours to build.

**Detection hint:** any weight, percentage, or variant list expressed as
Salesforce configuration rather than as code you wrote.

---

## Anti-Pattern 3: Invented model-pinning metadata

**What the LLM generates:**

```xml
<modelVersion>gpt-4o-2024-08-06</modelVersion>
```

or an `auto` value, inside the template metadata.

**Why it happens:** model pinning is a real and important concept, the element
name is the obvious one, and a dated model identifier is exactly what such a
field would contain elsewhere. Every part of the guess is individually
reasonable.

**Correct pattern:** the documented field on `GenAiPromptTemplateVersion` is
`primaryModel`. Do not write a model identifier you have not verified against
the org's available models — a plausible-looking but wrong value is worse than
omitting the field, because it deploys and then behaves unexpectedly.

**Detection hint:** any element name in a `genAiPromptTemplate` file that is not
in the documented field list. Deploy to a scratch org before it reaches a design
document.

---

## Anti-Pattern 4: CMDT indirection as the default recommendation

**What the LLM generates:** a Custom Metadata binding layer as step one of the
answer, regardless of whether the deploy path is actually the constraint.

**Why it happens:** CMDT-as-configuration is a strong, correct, well-represented
Salesforce idiom, and "make it configurable" is a high-prior architectural move.
The model has no way to know the team's deploy latency.

**Correct pattern:** the platform's own promotion — a one-field change to
`activeVersionIdentifier`, deployed — is sufficient for most teams and has zero
extra moving parts. Indirection is justified when a **measured** deploy time
fails a stated rollback requirement, or when you need concurrent variants (which
is a hard platform limit, not a preference). Adopting it otherwise adds a
component, widens who can change production behaviour, and creates a new failure
mode: a binding pointing at a retired version.

**Detection hint:** the recommendation includes an indirection layer and nowhere
states the deploy time it is meant to improve on.

---

## Anti-Pattern 5: Treating promotion as a text-only change

**What the LLM generates:** a promotion checklist covering the prompt body and
nothing else — review the wording, run the tests, activate.

**Why it happens:** "prompt version" reads as "prompt text version". The rest of
the version envelope — inputs, output schema, response format, grounding
providers, model — is structure the model does not surface unless asked about it
specifically.

**Correct pattern:** four things beyond the text can differ between versions, and
each has a distinct failure signature: a new **required input** fails at
invocation rather than deploy; `responseFormat` and `outputSchema` break
downstream parsers silently; `templateDataProviders` change what data reaches the
model; and `primaryModel` invalidates the goldens even when the text is
identical. Diff the envelope structurally before promoting.

**Detection hint:** the promotion procedure has no step that inspects anything
other than `content`.

---

## Anti-Pattern 6: Activating before consumers can handle the new version

**What the LLM generates:** an ordering of activate → then update consumers, or
no ordering at all.

**Why it happens:** the prompt is the thing being changed, so it leads. The
dependency direction — consumers depend on the template's input and output
contract — is not visible in the artefact being edited.

**Correct pattern:** deploy consumers first (able to handle both versions),
activate second, observe, retire third. Consumers that can only handle the new
version remove the rollback, which is precisely the property the sequencing
exists to protect.

**Detection hint:** the plan has no explicit ordering, or activation precedes
consumer deployment.

---

## Anti-Pattern 7: A canary with no attribution

**What the LLM generates:** a bucketing function that returns one template name
or the other, and nothing that records which was served.

**Why it happens:** the request is "route 10% to v4", the function routes 10% to
v4, and the request is satisfied. Measurement is a separate concern that was not
asked for.

**Correct pattern:** emit the variant assignment — slot, variant, template, user,
timestamp — at resolution time, before the ramp starts. Attribution cannot be
recovered from conversations that have already ended, so a canary without a tag
produces two populations and no conclusion.

**Detection hint:** the canary code has no logging, event publish, or telemetry
call.

---

## Anti-Pattern 8: Random-per-invocation bucketing

**What the LLM generates:** `Math.random() < 0.1 ? canary : stable`.

**Why it happens:** it is the textbook random assignment and it is
distributionally correct.

**Correct pattern:** bucket deterministically on a stable key such as user id, so
a given user's assignment does not change mid-experiment. Random-per-call means
a rep sees v4 in the morning and v3 in the afternoon — an incoherent experience
that users report as a bug, and that contaminates any qualitative feedback.

**Detection hint:** `Math.random()` or any non-deterministic source in variant
selection.

---

## Anti-Pattern 9: Deleting the old version as cleanup

**What the LLM generates:** a retirement step of "remove the old version and
deploy" immediately after promotion.

**Why it happens:** cleanup after a successful migration is standard good
practice in most contexts.

**Correct pattern:** the retained prior version *is* the rollback plan. Keep at
least two, retire on a defined schedule with an observation period, and record
the retirement date. Deactivated versions cost only file size.

**Detection hint:** a retirement step with no waiting period, or a plan that
retains only the current version.

---

## Anti-Pattern 10: Ignoring deploy ordering in the manifest

**What the LLM generates:** a `package.xml` with types in alphabetical or
arbitrary order.

**Why it happens:** for most metadata types the order genuinely does not matter,
so it is not a variable the model tracks.

**Correct pattern:** the Metadata API deploys types in the order they appear.
`GenAiPromptTemplate` must precede `AiAgentScorerDefinition` because the template
must exist before a scorer referencing it can deploy. Generalise: prompt
templates are a dependency of agents, scorers, Flows, and Apex, so put them
early.

**Detection hint:** a manifest containing both types with the scorer first.

---

## Anti-Pattern 11: Assuming the org and the repository agree

**What the LLM generates:** a workflow that edits in the repo and deploys, with
no mechanism to detect that someone edited in Setup.

**Why it happens:** source-of-truth discipline is stated as a convention, and
conventions are assumed to hold.

**Correct pattern:** a nightly retrieve-and-diff. The failure — a UI edit
silently reverted by the next deploy — is invisible until behaviour changes for
an unexplained reason, so it needs a detector rather than a policy.

```bash
sf project retrieve start --metadata GenAiPromptTemplate --target-org prod
git diff --exit-code force-app/main/default/genAiPromptTemplates/
```

**Detection hint:** the workflow states "the repo is authoritative" and contains
nothing that would notice if it were not.
