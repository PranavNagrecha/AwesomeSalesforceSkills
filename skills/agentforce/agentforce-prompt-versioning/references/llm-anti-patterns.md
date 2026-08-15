# LLM Anti-Patterns — Agentforce Prompt Versioning

---

## Anti-Pattern 1: Inventing `<modelVersion>` for pinning

**What the LLM generates:**

```xml
<modelVersion>gpt-4o-2024-08-06</modelVersion>
```

usually with a specific dated model identifier, presented as the pinning
mechanism.

**Why it happens:** model pinning is a real, important, and widely-discussed
practice; `modelVersion` is the name an English-speaking engineer would choose;
and dated model ids are exactly what such a field contains in other platforms.
Every component of the guess is individually reasonable, which is what makes it
convincing.

**Correct pattern:** the documented field on `GenAiPromptTemplateVersion` is
`primaryModel`
([GenAiPromptTemplate](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm)).
And do not write a model identifier you have not verified against the org's
available models — a wrong-but-plausible value deploys and then behaves
unexpectedly, which is worse than omitting it.

**Detection hint:** any element in a `genAiPromptTemplate` file that is not in
the documented field list. Deploy to a scratch org before it enters a design
document.

---

## Anti-Pattern 2: A file-per-version repository layout

**What the LLM generates:**

```text
genAiPromptTemplates/
  RefundStatusSummary.genAiPromptTemplate-meta.xml       # v1 (retired)
  RefundStatusSummary_v2.genAiPromptTemplate-meta.xml    # current
  RefundStatusSummary_v3.genAiPromptTemplate-meta.xml    # A/B variant
```

**Why it happens:** file-per-version is the standard way to version an artefact
that has no internal versioning, and the model does not know that
`templateVersions` is an array inside a single file. It also compounds with the
outdated belief that Prompt Builder has no version history.

**Correct pattern:** one file per template, all versions inside it,
`activeVersionIdentifier` naming the live one. The layout above creates three
separate *templates*, which means every consumer must be repointed to promote
and the platform's activation model is bypassed entirely.

**Detection hint:** version suffixes in filenames. (Two templates for a
concurrent canary is the one legitimate exception, because only one version can
be active at a time — and that scaffolding should be removed when the ramp ends.)

---

## Anti-Pattern 3: Inventing a subagent-level A/B configuration

**What the LLM generates:**

```yaml
prompt_variants:
  - name: RefundStatusSummary_v2
    weight: 90
  - name: RefundStatusSummary_v3
    weight: 10
```

described as subagent routing configuration (subagents were called topics before
April 2026), with "weights changed by metadata deploy."

**Why it happens:** weighted variant routing is how every experimentation
platform works. The YAML shape is so familiar it does not read as an invention,
and Agentforce genuinely has subagent configuration — just not this.

**Correct pattern:** only one version of a template can be active at a time and
there is no platform traffic split. Concurrent variants require two templates and
a resolver you write. See `agentforce/prompt-template-versioning` for the
bucketing and attribution mechanics.

**Detection hint:** weights or percentages expressed as Salesforce configuration
rather than as code.

---

## Anti-Pattern 4: "Bump the Revision field for minor changes"

**What the LLM generates:** a two-tier versioning policy — "bump the Revision
field in metadata for backwards-compatible changes, bump the name suffix for
breaking ones."

**Why it happens:** major/minor versioning is a deeply ingrained convention and
"Revision" is a plausible metadata field name in a Salesforce context.

**Correct pattern:** the documented per-version fields are `versionNumber` (int)
and `versionIdentifier` (string), plus `status` (`Published`/`Draft`). There is
no separate revision counter. The compatible/breaking distinction is real and
valuable — record it in the change record's "Contract impact" section, where it
drives the deployment shape, rather than encoding it in a field that does not
exist.

**Detection hint:** any reference to a Revision field, or a policy that maps
change types onto metadata fields not in the documented list.

---

## Anti-Pattern 5: A changelog with no measurements

**What the LLM generates:**

```markdown
## 2026-08-10 — Sales Email v4
- Removed filler preamble.
- Tightened closing guidance.
- Rollout: 10% -> 50% -> 100% over 5 days.
```

**Why it happens:** it is a well-formed changelog by every convention the model
has seen, and software changelogs describe changes rather than evidence. The
model has no signal that a prompt change is an *experiment* whose result should
be recorded.

**Correct pattern:** four sections — contract impact first (it determines the
deployment shape), what changed, why (with the observation that prompted it),
and what was measured with sample sizes. A reader six months later must be able
to disagree with the conclusion, which requires the evidence to be present.

**Detection hint:** no numbers, or numbers with no `n`.

---

## Anti-Pattern 6: Pinning everything

**What the LLM generates:** "pin the model version for all production
templates" as a blanket recommendation.

**Why it happens:** reproducibility is unambiguously good in the model's priors,
and pinning is the mechanism. The recurring cost is a process obligation, which
does not surface as a cost in an architectural answer.

**Correct pattern:** pinning is a commitment to quarterly re-evaluation. Pin
where reproducibility is a stated requirement — parsed output, regulated
wording, customer-facing copy. Leave the platform default where a human reviews
every output anyway. A pin nobody revisits freezes the template on progressively
older reasoning, and the cost is invisible because nothing breaks.

**Detection hint:** a pinning recommendation with no accompanying review cadence
and no named owner for it.

---

## Anti-Pattern 7: "The repo is authoritative" with no detector

**What the LLM generates:** a policy statement — *"UI edits are imported back
immediately or reverted"* — and no mechanism.

**Why it happens:** source-of-truth discipline is a convention, and conventions
are assumed to hold in a design document.

**Correct pattern:** the failure is silent in both directions — a UI edit does
not fail, and the deploy that reverts it does not fail either. The only symptom
is unexplained behaviour. A nightly retrieve-and-diff with a stated resolution
rule for each drift direction is the control; the policy alone is a hope.

**Detection hint:** the workflow states an authority and contains nothing that
would notice a violation.

---

## Anti-Pattern 8: Deleting the previous version at promotion

**What the LLM generates:** a retirement step immediately after promotion, framed
as cleanup, sometimes with a "0% traffic for 7 days" ritual borrowed from
service deployment.

**Why it happens:** cleanup after a successful migration is standard practice,
and the model has no representation of the retained version as the rollback
plan.

**Correct pattern:** two-version retention with a dated retirement. Inactive
versions cost file size. The weeks immediately after a promotion are precisely
when the rollback is most likely to be needed, which is precisely when the
cleanup instinct fires.

**Detection hint:** a retirement step with no observation window, or a policy
that retains only the current version.

---

## Anti-Pattern 9: Manifest ordering ignored

**What the LLM generates:** a `package.xml` with types in arbitrary or
alphabetical order.

**Why it happens:** for most metadata types the order genuinely does not matter,
so it is not a variable the model tracks.

**Correct pattern:** the Metadata API deploys types in the order they appear.
`GenAiPromptTemplate` must precede `AiAgentScorerDefinition`. Generalise:
templates are a dependency of agents, scorers, Flows, and Apex, so they go
early.

**Detection hint:** both types present with the scorer first.

---

## Anti-Pattern 10: Embedding policy values in the prompt text

**What the LLM generates:** a prompt containing *"the refund window is 30
days"* — because it reads naturally and produces a coherent instruction.

**Why it happens:** the model is optimising for a prompt that works, and an
inline value works. The coupling between policy cadence and prompt cadence is a
second-order operational consequence outside that frame.

**Correct pattern:** inject the value as an input (`refundWindowDays`) sourced
from Custom Metadata. The prompt describes how to use it; the data supplies what
it is. A policy change then costs a CMDT edit rather than a prompt version, a
review, a canary, and a deploy.

**The exception worth stating:** when the exact sentence *is* the artefact —
legally-reviewed disclosure wording, for instance — embedding is correct, because
the sentence is what is under version control. Decide per value and write down
which case you are in.

**Detection hint:** a date, a currency amount, a threshold, or a duration
appearing as a literal in prompt text.

---

## Anti-Pattern 11: Treating the prompt as purely an engineering artefact

**What the LLM generates:** a lifecycle owned entirely by the platform team —
branch, PR, review, deploy — with no business owner in the loop.

**Why it happens:** the request is framed as versioning and source control,
which are engineering practices, so the answer stays inside engineering.

**Correct pattern:** the wording is usually owned by someone who does not read
XML, and the envelope by someone who does not own the wording. CODEOWNERS should
name both. The failure modes split the same way — a bad sentence is a business
problem, a changed `outputSchema` is an engineering one — so a single reviewer
means one of the two lenses is missing from every change.

**Detection hint:** the process describes only engineering roles, or names one
owner per template.
