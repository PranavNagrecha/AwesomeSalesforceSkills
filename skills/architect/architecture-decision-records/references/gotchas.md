# Gotchas — Salesforce ADRs

The generic ADR failure modes are well documented elsewhere. These are the ones
that bite specifically on Salesforce programmes, plus the handful of universal
ones that are worth restating because they are violated constantly.

---

## 1. An ADR That Re-Derives A Decision Tree Is A Fork Waiting To Diverge

**What happens:** Three ADRs across a programme each argue Flow versus Apex from
first principles. They reach subtly different conclusions, and now the
organisation has three standards.

**When it occurs:** Whenever the author does not know a
`standards/decision-trees/` tree covers the choice — or knows and re-derives it
anyway because the ADR "should show its reasoning."

**How to avoid:** When a tree routes the decision, the ADR records **which
branch applied and what was true that made it apply**. Not the reasoning — the
tree owns that, and duplicating it guarantees drift the first time the tree is
updated.

```markdown
## Decision Trees Consulted
- `automation-selection.md` — Q1 (scheduled clock) → Q10 (>50k records) → Batch Apex
- `async-selection.md` — Q9 (needs ad hoc re-run) → Schedulable wrapper
```

The inputs are the valuable part. "1.9M rows today, 3.4M after the Q3
acquisition" is what lets a future reader test whether the routing still holds.
A paragraph of general reasoning about Flow's limitations does not.

**Source:** `standards/decision-trees/README.md` (this repository): trees sit above skills and own technology routing. Repository convention, not a platform claim.

---

## 2. Salesforce's Three-Release Cadence Expires ADR Premises Faster Than Most Platforms

**What happens:** An ADR rejects an approach because the platform could not do
something. Two releases later it can. The ADR still reads as authoritative.

**When it occurs:** Constantly, and more than on most platforms — Salesforce
ships three major releases a year, and capability gaps that motivated a
workaround close on that cadence. Common examples: a feature that was
Apex-only becoming available to Flow, a governor ceiling being raised, a
declarative capability reaching GA.

**How to avoid:** Where a decision hinges on a *current platform limitation* —
as opposed to an architectural principle — say so in the ADR and give it a
review trigger:

```markdown
## Review Trigger
This decision rests on [capability] being unavailable declaratively as of
Spring '26. Re-evaluate if it reaches GA. Owner: Platform Architect.
Checked at each seasonal release readiness review.
```

The distinction to hold onto: "we chose Apex because Flow cannot do X *yet*"
expires; "we chose Apex because this needs assertion-style tests behind a
coverage gate" does not. Only the first needs a trigger.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04): "Maybe something built to fill a gap in Salesforce platform functionality suddenly becomes redundant with a new Salesforce release or product launch." Release naming (Spring, Summer, Winter) per Well-Architected, Adaptable > Resilient.

---

## 3. "Decide To Wait" Is A Decision, And It Is The One Nobody Writes Down

**What happens:** A team decides not to migrate, not to adopt, not to
restructure. Nothing is recorded because "we didn't do anything." The question
is re-raised every quarter by a different stakeholder, re-argued from scratch,
and nobody notices when the conditions that justified waiting stop holding.

**When it occurs:** Platform lifecycle decisions especially — CPQ versus Revenue
Cloud Advanced, Aura versus LWC migration, single-org versus multi-org,
Workflow Rule and Process Builder retirement.

**How to avoid:** Write the ADR, and give it **named triggers with a named
owner**:

```markdown
## Decision
Remain on X through FY27. Re-evaluate immediately if EITHER trigger fires:
  Trigger A: [vendor announces an end-of-life date]
  Trigger B: [a requirement lands that Y supports and X demonstrably cannot]
Owner of the trigger watch: Platform Architect, reviewed quarterly at ARB.
```

Then surface the open triggers in `INDEX.md` as their own table. A trigger
buried in the body of a document nobody re-reads is not a trigger.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Technical Debt patterns: decision records should frame "trade-off discussions for action and inaction" in business terms.

---

## 4. Alternatives Considered Is Where The Value Is, And It Is Usually Empty

**What happens:** An ADR lists rejected options that were never real — a
strawman and an absurdity — so the section is present and worthless.

**When it occurs:** When the author already knew the answer and is writing the
record afterward, which is most of the time and is fine. The failure is not
retrospective writing; it is not doing the work of reconstructing what was
genuinely open.

**The diagnostic:** a rejected alternative that a competent person could
actually have chosen. In `examples.md` Example 2, Apex Managed Sharing was
viable — all its prerequisites were met — and it lost on maintainability. That
is a real alternative. "We could have hardcoded it in a formula field" is not.

**How to avoid:** If you cannot name two alternatives a reasonable person could
have chosen, you are not deciding — you are documenting a standard. That is a
different artifact, and it does not go in `docs/adr/`.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Readability: "Decision records. Keep a record of the options considered, trade-offs, final decision, and reasoning."

---

## 5. Consequences With No Negatives Means The Thinking Did Not Happen

**What happens:** "Consequences: faster, simpler, more maintainable." The ADR
reads as a sales document.

**When it occurs:** When the ADR is written to justify a decision rather than to
record it — often because it is going to a steering committee.

**How to avoid:** Require at least one real negative, and make it specific
enough to be checkable. Not "some complexity" but "two code paths instead of
one" or "the admin team can no longer modify this without a developer" or "we
accumulate 12-24 months of additional customisation debt."

The forcing question: *what will the team writing the superseding ADR in three
years complain about?* Write that down now. If nothing comes to mind, the
decision was not a tradeoff and probably was not an ADR.

**Source:** Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011), Consequences: "All consequences should be listed here, not just the 'positive' ones."

---

## 6. A Named Managed Package Constraint Is A Fact With A Version Number

**What happens:** An ADR says "the managed package doesn't support X." Two years
later nobody knows whether that is still true, which version was tested, or
whether "doesn't support" meant "cannot" or "we couldn't work out how."

**When it occurs:** Whenever a decision is shaped by an ISV package, an
industry-cloud managed package, or a platform component with independent
versioning.

**How to avoid:** Record the package name, the **version tested**, and *how* you
established the constraint:

```markdown
## Context
[Package] 4.12 does not expose [capability] through its public API.
Verified 2026-06-02 by [method — vendor ticket #, doc URL, scratch-org test].
Vendor's response to ticket #4471: no committed roadmap date.
```

Without the version and the method, a future reader cannot re-test the claim,
so the safe assumption becomes "it is probably still true," which is how
programmes carry workarounds for constraints that were lifted years earlier.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Maintainability: evaluate AppExchange and package solutions on "near-term and long-term costs". Recording the version tested is practice guidance, not a platform claim.

---

## 7. Org Strategy ADRs Need The Licensing Consequence, Not Just The Topology

**What happens:** A single-org versus multi-org ADR argues data model, sharing,
and governance — and omits the licensing and org-limit consequences, which are
frequently the ones that actually bind.

**When it occurs:** Because topology is the interesting part and licensing is
the boring part, and the boring part is the one that appears in a budget
eighteen months later.

**How to avoid:** For any org-topology, environment-strategy, or
platform-boundary ADR, require a section naming the consequences for: licence
counts and types, sandbox allocation and refresh intervals, org-level limits
that are shared rather than per-team, data residency, and the integration
surface between orgs that does not exist today. These make the negative
consequences concrete instead of abstract.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Standard vs. Custom patterns: "Decision records show calculation for near- and long-term costs when choosing to build or buy solutions."

---

## 8. Date The Decision, Not The Document

**What happens:** An ADR is edited for wording in 2027 and its date is updated.
A reader now believes the decision was made under 2027's constraints.

**When it occurs:** During documentation clean-ups, template migrations, or a
wiki-to-repo move where a tool rewrites the date field on save.

**How to avoid:** The date field is the date the decision was made and never
changes. Add a `Last edited: YYYY-MM-DD` footer if wording changes. Status
transitions get their own dates — "Superseded by ADR-0039 on 2027-11-04" —
which is why they are written into the Status line rather than replacing the
Date.

**Source:** Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011): a later ADR that reverses a decision marks the old one "deprecated" or "superseded" with a reference to its replacement. The separate decision-date rule is practice guidance.

---

## 9. Never Delete; Never Edit The Body Of A Superseded ADR

**What happens:** ADR-0014 is rewritten in place to reflect current thinking, in
the name of keeping the docs accurate.

**When it occurs:** When a team treats `docs/adr/` as living documentation and
"keeps it current" the way it would a design doc.

**Why it is wrong:** the value of a superseded ADR is entirely historical. It
tells a future reader *what was true when* — which is the only thing that lets
them judge whether the current decision's premises still hold. An edited ADR
teaches nothing and destroys the record that anything changed.

**How to avoid:** The only edit ever made to a superseded ADR is its Status
line, which flips and links forward. Everything else is frozen. Deletion is
never correct: a missing number in a sequence is worse than a superseded one,
because it looks like an error rather than a history.

**Source:** Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011): "If a decision is reversed, we will keep the old one around, but mark it as superseded."

---

## 10. Numbering Is Global, Never Per-Team

**What happens:** `adr/platform/0001-...` and `adr/integrations/0001-...`. Two
ADR-0001s. Every citation now needs a folder qualifier, and the folders
reorganise when the teams do.

**When it occurs:** When several delivery teams start ADR logs independently
and nobody owns the sequence.

**How to avoid:** One global sequence, four-digit zero-padded, in one directory.
Teams change; the decisions they made do not. The number must be citable in a
PR description as "ADR-0021" with no further context.

**Source:** Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011): "ADRs will be numbered sequentially and monotonically. Numbers will not be reused."

---

## 11. ADRs Live In The Repo They Describe

**What happens:** ADRs go in Confluence. Eighteen months later they describe a
codebase that has moved on, and nobody noticed because nothing about changing
the code required opening the wiki.

**When it occurs:** When ADRs are written for a steering committee that works
in a wiki and never opens the repository.

**How to avoid:** `docs/adr/` in the repository the decision governs. A file in
the repo appears in diffs, in code review, in `grep`, and in the same PR as the
change it constrains. Link *to* it from the wiki if the wiki is where
stakeholders look; do not make the wiki the source of truth.

If the decision spans repos — an org-topology decision, an integration
contract — put it in the repo that owns the *implementation*, and link from the
others. "Both" means neither.

**Source:** Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011): "We will keep ADRs in the project repository." ThoughtWorks Technology Radar, Lightweight Architecture Decision Records (Adopt, May 2018): store them "in source control, instead of a wiki or website". See Gotcha 15 for the access caveat.

---

## 12. Deciders Are Named People With The Role They Held At The Time

**What happens:** "Deciders: Tech Lead." Two years later there have been three
tech leads and nobody knows which one, or whether the current one was even
consulted.

**When it occurs:** When the template offers a role field and no name field,
or when deciders are recorded as a team name.

**How to avoid:** Names plus the role at the time, plus the forum if there was
one: `R. Patel (Platform Architect), S. Ahmed (CFO), Architecture Review Board`.
This is not bureaucracy — when a decision needs revisiting, the fastest path is
usually a five-minute conversation with whoever made it, and that is only
possible if you know who they were.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Strategy: "Governance makes it clear how decisions are made and communicated." Naming people is practice guidance.

---

## 13. Proposed ADRs Rot Silently

**What happens:** A `docs/adr/` directory accumulates ADRs stuck in Proposed
for a year. Readers cannot tell which decisions are live, so they stop trusting
the index.

**When it occurs:** Proposed is valuable when there is a real review cycle and
harmful when there is not. Nothing forces closure.

**How to avoid:** Review Proposed ADRs quarterly and close every one — Accepted,
or withdrawn with a one-line reason and status `Rejected`. A rejected ADR is
useful (it records that the idea was considered and why it lost); a
year-old Proposed one is only noise. If your organisation has no review forum,
skip Proposed entirely and write ADRs as Accepted retrospectively — which is a
legitimate mode, not a degraded one.

**Source:** Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011), Status: "A decision may be 'proposed' if the project stakeholders haven't agreed with it yet, or 'accepted' once it is agreed."

---

## 14. Backwards Compatibility Means Nothing Breaks To Force A Re-Read

**What happens:** An ADR chose a workaround because the platform lacked a
capability. The capability ships. The workaround keeps running, so no
incident, failed deploy, or test failure ever sends anyone back to the ADR.
The org now carries the workaround as permanent technical debt.

**When it occurs:** Whenever the premise is a platform gap rather than a
principle, and the ADR has no Review Trigger. Salesforce keeps older
implementations working, which is a benefit that hides expired premises.

**How to avoid:** Treat the seasonal release readiness review as the trigger
check. Every ADR with a platform-gap premise gets a Review Trigger row in
`INDEX.md`, and the release readiness checklist includes "walk the open
triggers table". Close the row when the capability ships, by writing the
superseding ADR.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Technical Debt: "the backwards compatibility built into the platform ... new platform innovations may change the pattern you should use for solutions moving forward, but the everyday function of solutions you've built on previous Salesforce technologies will continue to work."

---

## 15. A Repo-Only Record That Business Deciders Cannot Open

**What happens:** ADRs live in `docs/adr/` as recommended, but the CFO and the
revenue operations director who co-decided the CPQ question have no
repository access. They re-raise the decision because they cannot read it.

**When it occurs:** When the repo-first rule (Gotcha 11) is applied without
checking who the readers are. Licensing, lifecycle, and org-topology ADRs
usually have business deciders.

**How to avoid:** Keep the repository file as the source of truth, and publish
a read-only rendering (a wiki page generated from the file, or a link to the
rendered file) for every named decider. Record the rendering location in
`INDEX.md`. Never let the wiki copy accept edits.

**Source:** Salesforce Well-Architected, Easy > Intentional (architect.salesforce.com/docs/architect/well-architected/guide/intentional.html, read via Wayback snapshot 2026-04-04), Readability: keep decision records "in a central location that all team members can access for future reference." Balanced against Michael Nygard, "Documenting Architecture Decisions" (cognitect.com, 2011) and the ThoughtWorks Radar entry cited in Gotcha 11.

