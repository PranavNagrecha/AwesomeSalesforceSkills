# Well-Architected Notes — Agentforce Prompt Versioning

## Scope Boundary With `agentforce/prompt-template-versioning`

Two skills, one seam. This one is the **repository lifecycle**; the other is the
**runtime flip**.

| Question | Skill |
|---|---|
| Where do templates live in the repo? | **this skill** |
| What does a change record contain? | **this skill** |
| Do I pin the model, and how often do I re-evaluate? | **this skill** |
| How do I detect org-vs-repo drift? | **this skill** |
| Who owns the wording vs. the envelope? | **this skill** |
| How does the live version change, and how fast? | `prompt-template-versioning` |
| What does rollback cost in wall-clock time? | `prompt-template-versioning` |
| How do I serve two variants concurrently? | `prompt-template-versioning` |

They meet at `activeVersionIdentifier`: this skill decides *which* version should
be live and records why; the other is about the flip itself.

---

## Relevant Pillars

### Operational Excellence

A prompt is executable configuration whose behaviour cannot be verified by
reading it. That makes the *record* of why a version exists more load-bearing
than for ordinary code, where the code is its own documentation.

The change record's job is to let a future reader answer three questions without
running anything:

1. **Was this change safe to activate alone?** — the contract-impact section,
   which determines whether the release is a one-field flip or a coordinated
   deployment with consumers.
2. **What did we believe, and on what evidence?** — measurements with sample
   sizes, so the conclusion is falsifiable rather than remembered.
3. **What is the way back?** — the retained prior version and its measured
   rollback time.

The file layout follows from the metadata: all versions live inside one
`GenAiPromptTemplate` file, so git history is per-template and the changelog is
per-version. Neither substitutes for the other.

### Reliability

Reproducibility has two independent inputs — the template version and the model
— and the second can change without any action on your side. Pinning
`primaryModel` removes that variable, at the cost of an ongoing obligation.

The obligation is the part that gets dropped. A stale pin produces no error; it
produces output that quietly stops improving. That is why the review cadence
belongs in the design rather than in a good intention, and why a *declined*
upgrade with a written reason counts as a completed review.

Retention is the other reliability lever. An inactive version costs file size,
and the weeks right after a promotion — when the cleanup instinct fires — are
exactly when the rollback is most likely to be needed. Two-version retention with
a dated retirement makes rollback availability a property of the process rather
than of whether someone tidied up.

### Security

Two areas where the repository lifecycle carries a security consequence:

- **Grounding changes.** `templateDataProviders` determines what data reaches the
  model. For agents there is no Trust Layer masking behind you, so a grounding
  addition is a disclosure change dressed as a quality improvement. Any diff
  touching it re-opens the register review in
  `agentforce/agentforce-pii-redaction`.
- **Production edit rights.** Prompt Builder edit access in production is
  effectively the ability to change customer-facing behaviour without review.
  Restricting it is the structural control; the nightly drift detector is the
  safety net for whatever exceptions remain.

### Performance

Prompt length is a per-invocation cost paid on every call forever. A version that
adds 40% more instruction text raises token consumption and latency for the
entire user population, and the change record is the only place that cost is
visible before it is universal. Include a length delta and any latency
observation in the "Measured" section — see
`agentforce/agent-metric-dashboards` for the tiles that catch it afterwards.

---

## Architectural Tradeoffs

### Pin the model vs. take the platform default

| | Pin `primaryModel` | Platform default |
|---|---|---|
| Reproducibility | High | Varies over time |
| Benefits from model improvements | Only on re-evaluation | Automatically |
| Ongoing cost | Quarterly re-evaluation per template | None |
| Failure mode | Silent staleness | Silent drift |

Both fail silently, in opposite directions. Choose per template on whether
reproducibility is a stated requirement — parsed output, regulated wording,
customer-facing copy — and be honest about re-evaluation capacity. Pinning
without capacity is the worse of the two options, because it converts a drift you
would have noticed into a staleness you will not.

### Version inside the template vs. template per version

One file with `templateVersions[]` is what the platform models, keeps consumers
decoupled from version numbers, and makes activation a one-field change. Template
per version breaks all three and only makes sense as temporary scaffolding for a
concurrent canary — because only one version can be active at a time. Delete the
scaffolding when the ramp ends.

### Embedded policy vs. injected data

Embedding is simpler to author and produces a coherent prompt. It binds the
policy's release cadence to the prompt's — a 30-day-to-45-day change becomes a
version, a review, a canary, and a deploy. Injecting via an input keeps policy in
data where it is auditable in one place.

The exception is real and worth stating: when the exact sentence *is* the
artefact — legally-reviewed disclosure wording — embedding is correct, because
the sentence is what version control exists to protect. Decide per value and
record which case applies.

### Detector vs. policy for drift

A policy costs nothing and catches nothing, because both failure directions are
silent. A nightly retrieve-and-diff costs a CI job and catches the case that is
otherwise only discovered as unexplained behaviour weeks later. Run the detector
*after* production deploys as well as nightly — that converts it from monitoring
into release verification.

### Single owner vs. dual ownership

One owner is simpler and means one of the two review lenses is always missing.
The wording and the envelope fail differently — a bad sentence is a business
problem, a changed `outputSchema` is an engineering one — so CODEOWNERS should
name both. The cost is a second reviewer on prose-only changes, which the
structural-diff command in the PR template reduces to a glance.

---

## Anti-Patterns

1. **Inventing `<modelVersion>`.** The field is `primaryModel`, and a
   plausible-but-wrong model id deploys and then misbehaves.

2. **File-per-version layout.** Creates separate templates, bypasses the
   platform's activation model, and couples every consumer to a version number.

3. **A changelog with no measurements.** Records a belief instead of a finding;
   unfalsifiable six months later when a regression is suspected.

4. **Pinning everything.** Converts a drift you would notice into a staleness you
   will not, unless the re-evaluation capacity genuinely exists.

5. **"The repo is authoritative" with no detector.** Both drift directions are
   silent, so a convention is not a control.

6. **Deleting the superseded version at promotion.** Removes the rollback exactly
   when it is most likely to be needed.

7. **Policy literals in prompt text.** Binds two release cadences together for no
   benefit, except in the one case where the sentence itself is the artefact.

---

## Hygiene

- One file per template; changelog entry per version, keyed by
  `versionIdentifier`.
- Contract-impact section first in every change record.
- Structural-diff command in the PR template.
- Quarterly model re-evaluation per pinned template, with a recorded outcome
  either way.
- Nightly drift check, plus a post-deploy run as release verification.
- Two prior versions retained; retirement dates recorded.
- CODEOWNERS names both the wording owner and the envelope owner.

---

## Related

- `agentforce/prompt-template-versioning` — the runtime flip: promotion latency,
  rollback timing, canary bucketing and attribution.
- `agentforce/prompt-builder-templates` — authoring the template itself.
- `agentforce/agentforce-testing-strategy` — the goldens re-run whenever
  `primaryModel` changes, and the adversarial gate on a model upgrade.
- `agentforce/agentforce-pii-redaction` — the register a `templateDataProviders`
  change re-opens.
- `agentforce/agent-deployment-checklist` — prompt templates roll back on their
  own lifecycle, not with the agent.
- `devops/release-management` — the release train templates belong in.

---

## Official Sources Used

- GenAiPromptTemplate (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm
- GenAiPromptTemplateActv (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplateactv.htm
- Use Multiple Versions of a Prompt Template (Help) — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_use_multiple_versions.htm&type=5
- Activate and Deactivate Prompt Templates (Help) — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_activate_deactivate_templates.htm&type=5
- Manage Prompt Templates (Help) — https://help.salesforce.com/s/articleView?id=ai.prompt_builder_manage_prompt_templates.htm&type=5
- Create Custom Scorers, deploy ordering (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-custom-scorers.html
- Prompt Builder (Agentforce Developer Guide) — https://developer.salesforce.com/docs/einstein/genai/guide/get-started-prompt-builder.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
