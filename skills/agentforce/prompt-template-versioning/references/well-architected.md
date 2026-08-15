# Well-Architected Notes — Prompt Template Versioning

## Scope Boundary With `agentforce/agentforce-prompt-versioning`

These two skills sit either side of one seam. Read this one for **runtime
promotion mechanics**; read the other for the **repository lifecycle**.

| Question | Skill |
|---|---|
| How does the live version change, and how fast? | **this skill** |
| What does rollback cost in wall-clock time? | **this skill** |
| How do I serve two variants concurrently? | **this skill** |
| Where do templates live in the repo? | `agentforce-prompt-versioning` |
| What does the changelog entry contain? | `agentforce-prompt-versioning` |
| Do I pin the model, and how often do I re-evaluate? | `agentforce-prompt-versioning` |
| How do I detect UI-vs-repo drift? | `agentforce-prompt-versioning` |

They meet at `activeVersionIdentifier`: the other skill decides *which* version
should be live and records why; this skill is about the flip itself.

---

## Relevant Pillars

### Operational Excellence

The platform already provides most of what teams try to build here. Multiple
versions per template, activation and deactivation, and a metadata
representation carrying every retained version means "how do I keep history" is
a solved problem. What remains unsolved by the platform is narrow and worth
naming precisely:

1. **Promotion latency** equals your metadata deploy latency. That is an
   organisational property, not a technical one.
2. **Concurrent variants** are impossible natively — only one version can be
   active at a time.

Everything this skill recommends beyond plain activation exists to address one
of those two. Adopting indirection for any other reason adds a component and a
permission surface for no benefit.

The operational discipline that matters most is **ordering**: consumers deploy
first (able to handle both versions), activation second, retirement third on a
date. That sequence is what keeps rollback available, and it is the sequence
most often inverted under release pressure.

### Reliability

Rollback availability is a property of the *sequence*, not of the tooling. A
one-field revert is only a rollback if the previous version still exists and the
consumers can still handle it. Two rules follow:

- **Retain at least two prior versions.** Retirement is a dated decision, not a
  cleanup instinct. A deactivated version costs file size.
- **Keep consumers version-tolerant during the overlap.** A consumer that only
  understands v4 converts a reversible promotion into a one-way door.

The version envelope is where reliability is actually won or lost. `content`
changes are low-risk; `inputs.required`, `responseFormat`, `outputSchema`,
`templateDataProviders`, and `primaryModel` changes each have a distinct failure
signature, and none of them fail at deploy time. A structural diff before
promotion is the cheapest control available.

### Security

Two changes to a prompt version are security events wearing quality-improvement
clothes:

- **New grounding** (`templateDataProviders`) means new data reaching a model.
  For agents, pattern-based and field-based LLM data masking is disabled, so
  there is no platform filter behind you. Any grounding diff re-opens the PII
  register review in `agentforce/agentforce-pii-redaction`.
- **CMDT indirection widens the change surface.** The pattern's justification is
  faster *controlled* change; if the binding is directly editable in production
  by anyone with Customize Application, it has traded audit for speed. Deploy
  binding records as metadata so a change remains a reviewable commit.

### Performance

Canary ramps have a performance dimension that is easy to miss: a v4 whose
prompt is 40% longer costs more tokens and more latency on every invocation, and
the canary is the only place you will see that before 100% of traffic pays it.
Include latency and reasoning-intensity in the canary's watch list, not only
quality — see `agentforce/agent-metric-dashboards` for the tiles.

---

## Architectural Tradeoffs

### Native activation vs. slot indirection

| | Native `activeVersionIdentifier` | CMDT slot binding |
|---|---|---|
| Promotion | Metadata deploy | Record edit |
| Rollback | Metadata deploy (inverse) | Record edit |
| Extra components | None | Object, resolver class, tests |
| Audit trail | Git, reviewed by default | Git *if* records are deployed as metadata |
| Change surface | Deploy permission | CMDT edit permission — wider |
| Concurrent variants | Impossible | Possible |
| New failure mode | — | Binding points at a retired version |

Native first. Indirection when a **measured** deploy time fails a stated
requirement, or when you need concurrent variants. In the canary case treat the
indirection as scaffolding: remove it when the ramp completes.

### Canary vs. straight promotion

A canary buys evidence about the dimensions goldens cannot measure — tone,
usefulness, whether reps actually send the drafts. It costs a resolver, a
telemetry stream, and a week. Straight promotion is right when the change is
mechanical (a typo, a formatting fix) and wrong when the change is stylistic,
because style is exactly what automated evaluation is weakest at.

The ramp schedule is a risk-budget decision, not a ritual: 10 → 25 → 50 → 100 is
a reasonable default because each step roughly doubles exposure while keeping the
blast radius bounded if the previous step's signal was wrong.

### Deterministic vs. random bucketing

Deterministic on user id gives a coherent user experience and interpretable
qualitative feedback, at the cost of a slightly less clean random sample. Random
per invocation is statistically tidier and produces users who see two different
behaviours in one day — which they report as a bug and which contaminates every
comment you receive. Take determinism.

### Aggressive retirement vs. retention

Retention costs file size and a longer version list. Aggressive retirement costs
the rollback target. Because deactivated versions are inert, the asymmetry is
stark — keep two, retire on a date.

---

## Anti-Patterns

1. **Designing around a version history that already exists.** The platform
   retains versions; building a parallel archive solves nothing and adds drift.

2. **Expecting a platform traffic split.** Only one version can be active at a
   time. Concurrent variants are two templates plus your own resolver.

3. **Coupling consumers to version numbers.** Makes rollback exactly as
   expensive as release, at the moment you can least afford it.

4. **Indirection without a measured justification.** Adds a component, widens
   the change surface, and introduces a binding that can point at nothing.

5. **Promoting on a text diff alone.** Required inputs, output schema, response
   format, grounding, and model all live in the version envelope and none of
   them fail at deploy time.

6. **Deleting the previous version immediately.** The retained version is the
   rollback plan.

7. **A canary with no variant tag.** Produces two populations and no conclusion,
   and cannot be fixed retroactively.

---

## Hygiene

- Nightly `sf project retrieve start --metadata GenAiPromptTemplate` plus
  `git diff --exit-code` to detect UI-vs-repo drift.
- Measured rollback time recorded on the release record, refreshed when the
  pipeline changes.
- Structural diff of the version envelope on every promotion PR.
- Canary telemetry built before the first ramp, not during it.
- Retirement dates recorded; at least two prior versions retained.

---

## Related

- `agentforce/agentforce-prompt-versioning` — repository shape, changelog, model
  pinning, drift detection, and the decision of *which* version should be live.
- `agentforce/prompt-builder-templates` — authoring the template itself.
- `agentforce/agentforce-pii-redaction` — the register that a grounding change
  re-opens.
- `agentforce/agentforce-testing-strategy` — the goldens that must be re-run
  when `primaryModel` changes.
- `agentforce/agent-deployment-checklist` — prompt templates roll back on their
  own lifecycle, separately from the agent.
- `agentforce/agent-metric-dashboards` — the tiles a canary is watched on.

---

## Official Sources Used

- GenAiPromptTemplate (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm
- GenAiPromptTemplateActv (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplateactv.htm
- Use Multiple Versions of a Prompt Template (Help) — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_use_multiple_versions.htm&type=5
- Activate and Deactivate Prompt Templates (Help) — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_activate_deactivate_templates.htm&type=5
- Manage Prompt Templates (Help) — https://help.salesforce.com/s/articleView?id=ai.prompt_builder_manage_prompt_templates.htm&type=5
- Prompt Builder (Agentforce Developer Guide) — https://developer.salesforce.com/docs/einstein/genai/guide/get-started-prompt-builder.html
- Create Custom Scorers (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-custom-scorers.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
