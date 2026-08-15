---
name: architecture-decision-records
description: "Author and maintain Architecture Decision Records (ADRs) for Salesforce implementations: capture chosen approach, rejected alternatives, constraints, and consequences. Trigger keywords: adr, architecture decision record, design decision log, technical decision. NOT for making the design decision itself, e.g. Flow vs Apex — use architect/solution-design-patterns. NOT for a formal architecture review that produces findings — use architect/well-architected-review."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - architecture decision record
  - adr template
  - design decision log
  - technical rationale document
  - how do we record why we chose this approach
tags:
  - architect
  - adr
  - governance
  - documentation
  - decision-log
inputs:
  - A non-trivial technical decision (platform choice, pattern adoption, org topology)
  - Alternatives considered and the evaluation criteria
outputs:
  - One ADR file per decision, numbered, dated, statused
  - Index updated with new entry + any superseded links
dependencies:
  - architect/solution-design-patterns
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Architecture Decision Records

An ADR's real product is not the decision. It is the recorded **premise** — the
volumes, limits, and requirements the decision depended on. That is what lets a
future team test whether the choice still holds rather than re-litigating it,
and it is the part most ADRs omit.

On Salesforce specifically, two things make ADR discipline harder than
elsewhere: three major releases a year expire premises fast, and the platform's
lifecycle churn (product end-of-sale, feature retirement, GA dates) invites
confident unsourced claims into a document that is deliberately never updated.

---

## ADR Candidacy

Promote a decision to ADR when **any** of these holds:

- **Multi-quarter impact** — platform choice (Flow vs Apex vs Agentforce),
  pattern adoption (Trigger Handler, Selector Layer), org topology (single-org
  vs multi-org), integration approach, sharing model, licensing posture.
- **Reversal of an earlier recorded choice** — always a new ADR that supersedes;
  never a deletion, never an edit.
- **The 6-month test** — a joiner will ask "why did we do this?" and needs a
  document to read.

Out of scope:

- Applying an **existing** ADR to a new object or class. That is a line in the
  PR description — `"Follows ADR-0003 (TriggerHandler framework)."`
- Task-level tradeoffs.
- Anything fully internal to one feature's lifecycle.

**The test:** if it fits in a PR description, it is not an ADR.
**The corollary, which is more useful:** if you cannot name two alternatives a
competent person could actually have chosen, the decision was not open — you are
documenting a standard, not deciding.

---

## ADRs And Decision Trees Are Different Layers

This repository has `standards/decision-trees/`. An ADR that re-derives one of
those trees is a fork waiting to diverge — and the first tree update makes them
contradict each other.

| | Decision tree | ADR |
|---|---|---|
| Scope | organisation-wide routing rule | one situation |
| Answers | "which technology for this *shape* of problem?" | "which branch applied *here*, and what was true?" |
| Lifecycle | updated as the platform changes | frozen on acceptance |

When a tree routes the decision, the ADR records the **branch** and the
**inputs**, not the reasoning:

```markdown
## Decision Trees Consulted
- `automation-selection.md` — Q1 (scheduled clock) → Q10 (>50k records) → Batch Apex
- `async-selection.md` — Q9 (needs ad hoc re-run) → Schedulable wrapper

Inputs at the time of this decision:
- 1.9M Account rows today; ~3.4M projected after the Q3 acquisition
- Business requirement: accurate by 07:00 daily
```

Two cases still need an ADR even when a tree answered:

1. **You are deviating from the tree.** Record the branch, why this situation is
   the exception, and what would end the exception. A deviation with no ADR is
   indistinguishable from an error.
2. **The tree does not cover the scenario.** Write the ADR, and raise the gap so
   the tree can be extended — do not force-fit.

And the inverse: when the same decision recurs identically across teams, it
belongs in the *tree*, not in a fourth ADR.

---

## Required Sections

Standard Nygard structure, one file per decision in `docs/adr/`:

1. **Title** — `ADR-XXXX: <one-line decision>`
2. **Status** — Proposed / Accepted / Rejected / Superseded by ADR-YYYY (with date)
3. **Context** — the forces, the constraints, and the **inputs** the decision depended on
4. **Decision** — the choice, in the active voice
5. **Consequences** — positive **and** at least one specific, checkable negative
6. **Alternatives Considered** — at least two that a competent person could have chosen
7. **Date** — the decision date, ISO-8601, never updated
8. **Deciders** — named people with the role they held at the time, plus the forum

Plus, on Salesforce:

9. **Decision Trees Consulted** — branch and question numbers, or an explicit "no tree covers this"
10. **Review Trigger** — where the decision rests on a *current platform limitation* rather than a principle, with a named owner

---

## Sourcing Platform Claims

An ADR is the worst possible place for an unsourced lifecycle date, because
ADRs are deliberately not updated. A wrong date in a design doc is corrected
next sprint; a wrong date in an ADR stays load-bearing forever.

Every lifecycle, retirement, GA, or limit claim needs one of:

- a **Salesforce-hosted URL**, or
- a **named person and the date they confirmed it**.

Consultancy blogs are not sources for an architecture record. Where a claim
cannot be verified, mark it inline rather than laundering it:

```markdown
<!-- UNVERIFIED: a specific end-of-sale date of 27 March 2025 circulates
widely in consultancy writing. Not confirmed from a Salesforce source. -->
```

The same applies to managed-package constraints: record the package name, the
**version tested**, and *how* the constraint was established, so a future reader
can re-test it instead of assuming it still holds.

---

## Recommended Workflow

1. Apply the candidacy test. If it fits in a PR description, or you cannot name
   two viable alternatives, stop — this is not an ADR.
2. Check `standards/decision-trees/` before writing. If a tree routes this,
   record the branch and the inputs rather than re-deriving the reasoning. If
   you are deviating from the tree, say so explicitly and name what would end
   the exception.
3. Draft from `templates/adr-template.md` (Status = Proposed only if a real
   review forum exists; otherwise write it Accepted and retrospective), and
   source every platform claim as you go — Salesforce URL, or a named person
   and date. Mark anything unverifiable inline. Record package name, version
   tested, and method for package-attributed constraints.
4. Force the negatives. Ask what the team writing the superseding ADR will
   complain about, and write that down. If nothing comes to mind, this was not
   a tradeoff.
5. Add a **Review Trigger** with a named owner wherever the decision rests on a
   current platform limitation or on a pending vendor decision. A calendar date
   is not a trigger — a condition is.
6. Mark Accepted with the date and named deciders, update `docs/adr/INDEX.md`
   including the **open review triggers** table, and cite the ADR number in
   subsequent PR descriptions.
7. On supersession: write a new ADR, flip the old one's Status line and nothing
   else, link both ways, and state whether a premise **expired** or a mistake
   was **found** — they teach different lessons.

---

## Review Checklist

- [ ] Passes the candidacy test; two genuinely viable alternatives exist
- [ ] Decision trees checked; branch cited, or "no tree covers this" stated
- [ ] Deviation from a tree, if any, is explicit with an end condition
- [ ] Context records the **inputs** (volumes, limits, requirements), not just narrative
- [ ] Every platform lifecycle claim has a Salesforce URL or a named confirmer + date
- [ ] Unverifiable claims marked inline, not asserted
- [ ] Managed-package constraints carry package name, version tested, and method
- [ ] At least one specific, checkable negative consequence
- [ ] Review Trigger present where the decision rests on a current limitation, with an owner
- [ ] Deciders are named people with roles held at the time
- [ ] Date is the decision date and has never been updated
- [ ] Global four-digit numbering, one directory, in the repo the decision governs
- [ ] `INDEX.md` updated, including the open-triggers table
- [ ] Supersession links resolve both ways; the superseded body is untouched
- [ ] Fits on roughly one page; the design doc is linked, not inlined

---

## Worked Examples (see `references/examples.md`)

- *A decision the tree already answers* — record the branch, not the reasoning
- *A sharing model decision* — where the ordering **is** the decision
- *A platform lifecycle decision* — deciding to wait, with named triggers
- *Supersession done properly* — a premise expiring, not a mistake
- *A decision that should not have been an ADR* — and where it belongs instead
- *The index* — including the open-review-triggers table

## Common Gotchas (see `references/gotchas.md`)

- An ADR that re-derives a decision tree is a fork waiting to diverge
- Three releases a year expire ADR premises faster than most platforms
- "Decide to wait" is a decision, and the one nobody writes down
- A named managed-package constraint is a fact with a version number
- Org strategy ADRs need the licensing consequence, not just the topology
- Never edit the body of a superseded ADR
- Proposed ADRs rot silently

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Re-deriving a decision tree inside the ADR
- Alternatives Considered populated with strawmen
- Consequences that are all positive
- Editing the superseded ADR instead of superseding it
- An ADR for every decision
- An ADR as a design specification
- Stating platform lifecycle facts without sourcing or dating them
- "Decide to wait" left unwritten, or written without triggers

---

## Related

- **architect/solution-design-patterns** — for making the decision. This skill
  is for recording it.
- **architect/well-architected-review** — a review that produces findings, which
  is a different artifact with a different lifecycle.
- **standards/decision-trees/README.md** — the layer above ADRs. Read the
  relevant tree before writing an ADR about a technology choice.

## Official Sources Used

See `references/well-architected.md` for the full source list, including an
explicit caveat on the CPQ lifecycle claims used in the worked examples.
