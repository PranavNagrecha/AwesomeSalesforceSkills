# Well-Architected — Salesforce ADRs

## Relevant Pillars

- **Adaptable** — an ADR's real product is not the decision; it is the recorded
  *premise*. "1.9M rows today, 3.4M after the Q3 acquisition, next-morning
  freshness" is what lets a future team test whether the decision still holds
  instead of re-litigating it from scratch. A decision without its premise
  cannot be safely revisited, which makes it harder to change than one that was
  never written down.
- **Resilient** — superseded decisions documented forward stop teams re-trying a
  path that previously failed, and stop them reverting a path that succeeded for
  reasons nobody remembers.
- **Trusted** — on a platform with three releases a year and active product
  lifecycle churn, an unsourced claim about a retirement date or a GA capability
  becomes load-bearing for a decision and is then frozen forever. Sourcing
  discipline in ADRs is not pedantry; it is the difference between a record and
  a rumour.

## ADRs And Decision Trees Are Different Layers

This repository has `standards/decision-trees/`. An ADR that re-derives one of
those trees is a fork waiting to diverge.

| | Decision tree | ADR |
|---|---|---|
| Scope | organisation-wide routing rule | one situation |
| Question answered | "which technology, in general, for this shape of problem?" | "which branch applied *here*, and what was true that made it apply?" |
| Lifecycle | updated as the platform changes | frozen on acceptance; superseded, never edited |
| Owner | the standards layer | the team that made the call |

Available trees and the ADR classes they route:

| Tree | Routes | ADR class |
|---|---|---|
| `automation-selection.md` | Flow, Apex, Agentforce, Approvals, Platform Events, Batch | "how is this automation built" |
| `flow-pattern-selector.md` | before/after-save, scheduled, screen, orchestration, PE-triggered | "which Flow shape" |
| `async-selection.md` | `@future`, Queueable, Batch, Schedulable, Platform Events | "which async mechanism" |
| `integration-pattern-selection.md` | REST, Bulk API, Platform Events, CDC, Pub/Sub, Salesforce Connect, MuleSoft | "how do these systems talk" |
| `sharing-selection.md` | OWD, role hierarchy, sharing rules, teams, manual, Apex Managed, restriction/scoping | "who can see this object" |
| `agentforce-capability-selector.md` | Agent, Prompt Builder, Next Best Action, Model Builder, Einstein Bots | "which AI capability" |
| `performance-tuning.md` | Apex CPU/heap, SOQL/index, sharing recalc, LDV, LWC render, Platform Cache | "why is this slow, and what do we change" |

**The rule for ADR authors:** cite the tree branch, record the inputs, stop.

```markdown
## Decision Trees Consulted
- `automation-selection.md` — Q1 (scheduled clock) → Q10 (>50k records) → Batch Apex
- `async-selection.md` — Q9 (needs ad hoc re-run) → Schedulable wrapper
```

**Two cases where an ADR is still needed even though a tree answered:**

1. **You are deviating from the tree.** That is precisely an ADR — record the
   branch, record why this situation is the exception, and name what would have
   to be true for the exception to end. A deviation with no ADR is
   indistinguishable from an error.
2. **The tree does not cover the scenario.** Per the trees' own README, that is
   a gap to surface rather than force-fit. Write the ADR for the situation, and
   raise the gap so the tree can be extended.

Conversely, when the same ADR-worthy decision recurs across teams, that is
evidence the *tree* should absorb it. A rule that has been re-decided three
times identically is a standard, not a decision.

## Architectural Tradeoffs

- **Lightweight (Nygard) vs heavyweight RFC.** Nygard ADRs are one page and get
  read. RFCs cover spec-level detail and slow the decision. Default to Nygard;
  the design doc is a separate artifact with a separate lifecycle — which is the
  real argument for separating them, since the design changes every sprint and
  the ADR never changes at all.
- **Proposed status vs direct-Accepted.** Proposed is valuable where a genuine
  review forum exists, and harmful where none does, because nothing forces
  closure and a directory of year-old Proposed ADRs teaches readers to stop
  trusting the index. Retrospective Accepted ADRs are a legitimate mode, not a
  degraded one.
- **Repo-local vs central ADR repository.** ADRs in the repo they govern appear
  in diffs, in review, and in `grep`. A central org-wide ADR repo is
  discoverable in principle and skipped in practice, because nothing about
  changing the code forces anyone to open it. For decisions spanning repos, put
  the ADR in the repo that owns the *implementation* and link from the others —
  "both" means neither.
- **Completeness vs readability of the index.** Every ADR added dilutes the
  index. The candidacy bar exists to protect the reader, not to save the
  author's time. A forty-ADR index where six matter is a five-minute filtering
  task that nobody performs.

## Salesforce-Specific Requirements For An ADR

Beyond the standard Nygard sections, a Salesforce ADR should carry:

- **Decision Trees Consulted** — branch and question numbers, or an explicit
  "no tree covers this."
- **Inputs at the time** — the volumes, limits, and requirements the routing
  depended on. These are what a future reader re-tests.
- **Sourced platform claims** — any lifecycle, retirement, GA, or limit claim
  needs a Salesforce-hosted URL, or a named person and the date they confirmed
  it. Consultancy blogs are not sources for an architecture record.
- **Package versions** — for any constraint attributed to a managed package:
  name, version tested, and how the constraint was established.
- **Licensing and org-limit consequences** — for org-topology, environment, or
  platform-boundary decisions, these bind more often than the topology does.
- **A review trigger where the decision rests on a current platform limitation
  rather than a principle** — Salesforce ships three releases a year, and
  "Flow cannot do X yet" expires in a way that "this needs assertion-style tests
  behind a coverage gate" does not.

## Hygiene

- `docs/adr/INDEX.md` updated on every addition, with a separate **open review
  triggers** table naming each trigger's owner and last-checked date.
- Supersession links resolve in both directions.
- The only edit ever made to a superseded ADR is its Status line.
- Global four-digit numbering in one directory. Never per-team.
- Named deciders with the role they held at the time, plus the forum.
- Proposed ADRs reviewed quarterly and closed — Accepted or Rejected. A rejected
  ADR is useful; a stale Proposed one is noise.
- Every Consequences section contains at least one specific, checkable negative.

## Official Sources Used

- **Michael Nygard, "Documenting Architecture Decisions"** —
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
  — the origin of the format: the Status / Context / Decision / Consequences
  structure, the one-page constraint, and the principle that superseded records
  are retained rather than edited.
- **ThoughtWorks Technology Radar — Lightweight Architecture Decision Records** —
  https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records
  — the "Adopt" ring rationale for keeping ADRs short and storing them in the
  repository they describe.
- **Salesforce Well-Architected** —
  https://architect.salesforce.com/well-architected/overview
  — the pillar framing (Adaptable / Resilient / Trusted) used above.
- **`standards/decision-trees/README.md`** (this repository) — the layering rule
  that decision trees sit above skills and route technology choice, and the
  instruction to surface a gap rather than force-fit when no tree covers a
  scenario. The tree inventory in the table above is taken from it.
- **Salesforce Well-Architected: Easy > Intentional**:
  https://architect.salesforce.com/docs/architect/well-architected/guide/intentional.html
  (a direct fetch does not return the guide page; read via the Wayback
  Machine snapshot of 2026-04-04): "Decision records. Keep a record of the
  options considered, trade-offs, final decision, and reasoning in a central
  location"; the build-or-buy near- and long-term cost pattern; the
  backwards-compatibility passage behind Gotcha 14.
- **Salesforce Well-Architected: Adaptable > Resilient**:
  https://architect.salesforce.com/docs/architect/well-architected/guide/resilient.html
  (Wayback snapshot of 2026-06-13): release naming by season and the
  release-management guidance behind Gotcha 2.
- **Salesforce CPQ Developer Guide, Version 67.0 (Summer '26)**:
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/cpq_developer_guide.pdf
  Chapter 1 notice: the managed package "continues to be available for
  existing customers", has "no longer any new feature development", keeps
  support "for the duration of your contract", and allows adding licences and
  renewing. This replaces the earlier search-extract grounding for the CPQ
  lifecycle wording in `examples.md` Example 3.
- **Navigating the Future of Salesforce CPQ: Product End of Sale (Not End of
  Life)**, salesforce.com, 10 July 2026:
  https://www.salesforce.com/sales/cpq/end-of-life/
  Earlier versions of this skill recorded HTTP 403 for this page; a plain
  fetch returned the article on 2026-10-03. It states that CPQ "is end of
  sale, not end of life", that existing customers can buy additional users,
  renew, and receive support, that Salesforce "is no longer selling new
  Salesforce CPQ licenses to new customers", that investment has shifted to
  Revenue Cloud Advanced, and that there is "no forced migration". It states
  no end-of-sale date, so the 27 March 2025 date that circulates in
  consultancy writing stays marked `UNVERIFIED` in Example 3 and
  Anti-Pattern 7.
- **Salesforce Object Reference, Version 67.0 (Summer '26), ConversationEntry,
  Usage**:
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  "The legacy chat product is in maintenance-only mode, and we won't continue
  to build new features." Used in Anti-Pattern 9 as a second example of a
  maintenance notice that states no retirement date.
