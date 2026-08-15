# LLM Anti-Patterns — Salesforce ADRs

Mistakes AI assistants reliably make when asked to write or review an
Architecture Decision Record on a Salesforce programme. Each entry names the
wrong output, the mechanism producing it, the corrected version, and a check.

---

## Anti-Pattern 1: Re-Deriving A Decision Tree Inside The ADR

**What the LLM generates:** three paragraphs comparing Flow and Apex in general
terms, inside an ADR about one nightly job — fluent, accurate, and entirely
duplicative of `standards/decision-trees/automation-selection.md`.

**Why it happens:** The model is optimising for a self-contained, well-argued
document, which is what "write an ADR" evokes. It has an enormous amount to say
about Flow versus Apex and no signal that a routing artifact already owns that
reasoning. The output *looks* like a better ADR — more thorough, more
justified — which is exactly why it survives review.

The damage is not the length. It is that the tree and the ADR are now two
sources for the same rule, and the first time the tree is updated they diverge.

**Correct pattern:**

```markdown
## Context
Routing per `standards/decision-trees/automation-selection.md`:
  - Q1: trigger is "a scheduled clock" → Q10
  - Q10: "> 50k records or run > 5 minutes?" → yes → Batch Apex

Cross-checked against `async-selection.md` Q1, which routes the same way.

Inputs at the time of this decision:
  - 1.9M Account rows today
  - ~3.4M projected after the Q3 acquisition
  - business requirement: accurate by 07:00 each day
```

The tree owns the reasoning. The ADR owns **which branch applied** and **what
was true that made it apply** — because the inputs are what a future reader
must re-test.

**Detection hint:** Any ADR whose Context argues a technology comparison in
general terms rather than citing a tree branch plus this situation's inputs.
Grep the ADR for a `decision-trees/` reference; if the choice is one a tree
covers and the reference is absent, the ADR is either duplicating or
contradicting it.

---

## Anti-Pattern 2: Alternatives Considered Populated With Strawmen

**What the LLM generates:** rejected options nobody would have chosen —
"hardcode the values in a formula field", "do it manually in a spreadsheet",
"build a custom framework from scratch" — so the section is present and empty
of information.

**Why it happens:** The model knows the section is required and generates
something plausible to fill it. It does not have access to what was actually on
the table in the room, so it manufactures options from the space of *things one
could conceivably do* rather than *things this team seriously considered*. The
weakest options are the easiest to reject convincingly, so they are what get
generated.

**Correct pattern:**

```markdown
### Apex Managed Sharing for all four audiences
Rejected. sharing-selection.md Q5 lists prerequisites, all of which we
meet — so this was viable, not impossible. It loses because Q2 and Q3
resolve three audiences declaratively, and Apex Managed Sharing would put
that access behind code, tests, a recalculation job, and a deployment for
every rule change.
```

The test: **could a competent person have chosen this?** If not, it is not an
alternative. And if you cannot name two that pass the test, the decision was
not open — you are documenting a standard, not deciding, and it does not belong
in `docs/adr/`.

**Detection hint:** Any rejected alternative whose rejection reason is a
one-liner about it being obviously bad. Any ADR where every alternative was
non-viable. Ask of each: what would have had to be different for this to win?
If there is no answer, it is a strawman.

---

## Anti-Pattern 3: Consequences That Are All Positive

**What the LLM generates:** "faster deploys, better maintainability, improved
scalability, happier developers."

**Why it happens:** The model is completing a document that argues *for* a
decision, and the surrounding text is persuasive in register. Listing genuine
downsides reads as arguing against the thing the document just decided, which
is locally incoherent — so the generation smooths toward consistency. There is
also a helpfulness pressure: naming a real cost feels like delivering bad news.

**Correct pattern:**

```markdown
### Negative
- Requires Apex test coverage (75% org-wide gate) that a Flow would not
  have required. Estimated 2 days of the 5-day build.
- The admin team cannot modify the rollup logic without a developer.
  Accepted: the rollup definition is stable and field selection is
  configuration-driven via Custom Metadata.
- Debugging is developer-side; there is no Flow debug UI equivalent.
```

Specific, checkable, and each with the mitigation or the explicit acceptance.
The forcing question: *what will the team writing the superseding ADR complain
about?* If nothing comes to mind, this was not a tradeoff and probably was not
an ADR.

**Detection hint:** A Consequences section with no Negative subsection, or with
negatives so vague they cannot be checked ("some added complexity", "a learning
curve"). Both mean the thinking did not happen.

---

## Anti-Pattern 4: Editing The Superseded ADR Instead Of Superseding It

**What the LLM generates:** asked to "update the ADR to reflect the new
approach," it rewrites ADR-0014's Context, Decision, and Consequences in place.

**Why it happens:** "Update the document to be accurate" is the correct
instinct for essentially every other document type, and the model has no reason
to know that an ADR is an append-only log rather than a living document. The
instruction it was given ("update") also literally asks for an edit.

**Correct pattern:**

```markdown
Write a NEW ADR. The ONLY edit to the old one is its Status line:

    ## Status
    Superseded by ADR-0039 on 2027-11-04.

Everything else in ADR-0014 is frozen. Its value is now entirely
historical: it records what was true in May 2026, which is the only thing
that lets a reader judge whether today's premises still hold.

State in the NEW ADR why the supersession happened — a premise EXPIRED,
or a mistake was FOUND. These teach different lessons and the distinction
matters:

    "ADR-0014 was not wrong; its premise expired. Volume grew from 1.9M
     to 4.1M and the freshness requirement changed from next-morning to
     15 minutes."
```

**Detection hint:** Any diff touching a superseded ADR outside its Status line.
Any ADR whose `Date` field has changed. Any supersession that does not link
both ways.

---

## Anti-Pattern 5: An ADR For Every Decision

**What the LLM generates:** asked to "document our architecture decisions," it
produces forty ADRs covering naming conventions, field types, folder structure,
and which framework to use for a specific trigger.

**Why it happens:** The model optimises for coverage — more documented decisions
reads as more thorough, and there is no signal in the prompt about where the
threshold sits. Every choice genuinely *is* a decision in the literal sense, so
nothing in the instruction excludes any of them.

**Correct pattern:**

```text
ADR candidacy — promote only when ANY holds:

  Multi-quarter impact     platform choice, pattern adoption, org topology,
                           integration approach, sharing model, licensing
  Reversal                 of an earlier recorded choice (always supersede,
                           never delete)
  The 6-month test         a joiner will ask "why did we do this?" and needs
                           a document to read

Excluded:
  - applying an EXISTING ADR to a new object or class
    -> a line in the PR description: "Follows ADR-0003."
  - task-level tradeoffs
  - anything fully internal to one feature's lifecycle

The test: if it fits in a PR description, it is not an ADR.
The corollary: if you cannot name two viable alternatives, you are
documenting a standard, not deciding.
```

**Detection hint:** Any ADR with no Alternatives Considered — that is the
signature of applying an existing standard. Any ADR whose decision is "follow
the convention we already agreed." Any index where the ratio of ADRs to
genuinely open architectural questions exceeds roughly one to one.

---

## Anti-Pattern 6: An ADR As A Design Specification

**What the LLM generates:** a ten-page document with the object model, field
lists, sequence diagrams, API contracts, and a phased implementation plan,
under an ADR heading.

**Why it happens:** "Architecture" and "decision record" both pull toward
comprehensiveness, and the model has far more training signal on design
documents than on the deliberately minimal Nygard ADR format. Length also reads
as effort, and a one-page ADR can look like an under-delivered answer.

**Correct pattern:**

```text
ADR: WHAT we decided and WHY, plus what we rejected. One page.
Design doc: HOW it works. As long as it needs to be. Linked from the ADR.

They have different lifecycles, and that is the real reason to separate
them. The design doc changes every sprint as implementation proceeds.
The ADR is frozen the day it is accepted. Merging them means either the
decision record drifts, or the design goes stale — and in practice both.
```

**Detection hint:** Any ADR containing a sequence diagram, an object model, a
field list, an API schema, or an implementation phase plan. Any ADR over about
one page of prose. Any ADR that would need editing when implementation details
change — that is the diagnostic, because an ADR should never need editing at
all.

---

## Anti-Pattern 7: Stating Platform Lifecycle Facts Without Sourcing Or Dating Them

**What the LLM generates:** confident, specific, unsourced claims in an ADR's
Context — "Salesforce CPQ reaches end of life in 2027", "Workflow Rules will be
retired in Winter '26", "this feature is GA as of Spring '25".

**Why it happens:** This is the highest-consequence failure in the domain and
it has a specific mechanism. Salesforce lifecycle dates are heavily discussed in
consultancy blogs and community posts, which reliably state a date with
confidence and *without* linking a Salesforce source. A model trained on that
corpus absorbs the date and its confident register together, and reproduces
both. The date may even be right — the failure is that it enters a permanent
architecture record with no provenance, so nobody can ever check it.

An ADR is exactly the wrong place for this, because ADRs are *deliberately not
updated*. A wrong date in a design doc gets corrected next sprint. A wrong date
in an ADR is load-bearing for a decision and frozen forever.

**Correct pattern:**

```markdown
## Context
Salesforce CPQ has entered an end-of-sale phase: new customers can no
longer purchase it, and product investment has moved to Revenue Cloud
Advanced. Existing customers retain support. Salesforce has NOT announced
an end-of-life date.

Source: https://www.salesforce.com/sales/cpq/end-of-life/
Confirmed with account team (K. Nowak) on 2026-07-14; she stated no EOL
date is committed and none is expected before FY29.

<!-- A specific end-of-sale date of 27 March 2025 circulates widely in
consultancy writing. Not confirmed from a Salesforce source at time of
writing. Do not treat as fact. -->
```

Three elements: **the Salesforce URL**, **who confirmed it and when**, and an
**explicit marker on anything unverified**.

**Detection hint:** Any date, retirement, EOL, GA, or deprecation claim in an
ADR without a Salesforce-hosted URL or a named person and date of confirmation.
Any claim sourced to a consultancy blog. Treat every unsourced lifecycle date as
unverified until someone re-establishes it — and note that the model's
confidence carries no information here.

---

## Anti-Pattern 8: "Decide To Wait" Left Unwritten, Or Written Without Triggers

**What the LLM generates:** either nothing at all — because "we decided not to
act" does not present as a decision worth documenting — or an ADR that ends at
"re-evaluate in 12 months."

**Why it happens:** The training signal for ADRs is overwhelmingly about
choices *between things that get built*. A decision to defer produces no
artifact, no diagram, no implementation, so it does not match the shape of an
ADR the model has learned. And "re-evaluate later" feels like a complete
closing sentence, because in most documents it is.

**Correct pattern:**

```markdown
## Decision
Remain on Salesforce CPQ through FY27. Do not begin migration work.
Re-evaluate immediately if EITHER trigger fires:

  Trigger A: Salesforce announces an end-of-life date for CPQ.
  Trigger B: a business requirement lands that Revenue Cloud Advanced
             supports and CPQ demonstrably cannot.

Owner of the trigger watch: Platform Architect, reviewed quarterly at ARB.

## Consequences
### Negative
- We accumulate 12-24 months of additional customisation debt if teams
  keep extending CPQ. Mitigated: change-control gate on new CPQ price
  rules from 2026-09-01.
- If Trigger A fires late, a 12-18 month migration compresses into
  whatever remains. This risk is accepted explicitly by the named
  deciders below.
```

Then surface the open triggers in `INDEX.md` as their own table, so they are
visible without opening the ADR.

**Detection hint:** Any deferral decision with a calendar date rather than a
condition — "review in 12 months" is not a trigger, because nothing fires it.
Any review trigger with no named owner. Any `INDEX.md` with no open-triggers
section on a programme that has made deferral decisions.
