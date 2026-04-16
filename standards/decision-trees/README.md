# Decision Trees

Cross-skill routing logic. **Read one of these BEFORE activating any skill
that proposes a specific technology.**

Skills in this repo explain *how* to do a thing. Decision trees decide
*which thing* to do in the first place — they sit one layer above skills
and save agents (and humans) from picking the wrong tool before the skill
even opens.

## Available trees

| Tree | Routes between | Read before |
|---|---|---|
| [`automation-selection.md`](./automation-selection.md) | Flow, Apex, Agentforce, Approvals, Platform Events, Batch | Any skill in `apex/`, `flow/`, `agentforce/` |
| [`async-selection.md`](./async-selection.md) | `@future`, Queueable, Batch, Schedulable, Platform Events, Scheduled Flow | Any skill in `apex/async-*`, `apex/batch-*`, `apex/queueable-*`, `apex/scheduled-*` |
| [`integration-pattern-selection.md`](./integration-pattern-selection.md) | REST, Bulk API, Platform Events, CDC, Pub/Sub, Salesforce Connect, Named Credentials, MuleSoft | Any skill in `integration/` |
| [`sharing-selection.md`](./sharing-selection.md) | OWD, Role Hierarchy, Sharing Rules, Teams, Manual, Apex Managed, Restriction, Scoping | Any skill in `security/*sharing*`, `apex/apex-managed-sharing`, or when designing a new object's access model |

## How decision trees fit into the agent workflow

```
User query
    ↓
Retrieval (scripts/search_knowledge.py)
    ↓
Decision tree (if the query straddles multiple technologies)  ← routes here
    ↓
Skill activation (SKILL.md)
    ↓
Template reference (templates/<domain>/…)
    ↓
Output
```

## Rules for agents

1. **Before proposing a tech choice, search decision trees first.**
   If the user's ask touches more than one technology in a tree's scope
   (e.g. "automate approvals"), read the tree top-to-bottom.
2. **Quote the tree's reasoning, not just the answer.**
   "Per `automation-selection.md` Q3: this touches HTTP callouts, so Apex is
   the right choice — not Flow." Users trust justification more than verdicts.
3. **If the tree says "see skill X," activate skill X.**
   Decision trees are routers; skills are the implementation layer.
4. **If the tree doesn't cover the scenario, say so.**
   Don't force-fit. Surface it as a gap and propose a new tree section.
5. **Trees override retrieval ties.**
   When two skills score close in search, the tree's recommended skill wins.

## Rules for skill authors

1. Skills should **cite** the relevant decision tree under their `## Related`
   section, not duplicate its logic.
2. A skill body that re-answers a decision tree is a smell — delete the
   re-answer and link.
3. When you add a skill whose activation depends on a decision, either the
   tree covers it (link) or the tree needs a new branch (propose an edit).

## Rules for tree authors

1. Trees are opinion-heavy; that is their purpose. State the default clearly.
2. Every branch must resolve to either another question, a skill path, a
   template path, or a cross-tree link. No dead ends.
3. Trees reference official Salesforce docs for any quantitative claim
   (governor limits, edition feature availability).
4. Every anti-pattern gets a short "do this instead" — never just "don't."
5. Keep each tree under ~400 lines. If it grows past that, split it.

## Missing decision trees (future work)

These would all be high-leverage:

- `data-model-decision.md` — Master-Detail vs Lookup vs External Id vs
  Junction Object vs Big Object
- `testing-strategy.md` — Unit (Apex test) vs Integration (named mock) vs
  UI (Jest) vs E2E (Playwright) vs Apex Reality (dev sandbox)
- `deployment-strategy.md` — Change Set vs Metadata API vs Unlocked Package
  vs 1GP/2GP Managed vs DevOps Center
- `licensing-decision.md` — Platform vs Sales Cloud vs Service Cloud vs
  Experience Cloud vs Customer Community vs Partner Community
- `storage-decision.md` — Standard SObject vs Big Object vs Platform Cache
  vs External Object vs Data Cloud DMO
- `agentforce-vs-einstein-vs-model-builder.md` — when to use each AI surface
- `multi-org-decision.md` — single org vs multi-org vs hub-and-spoke
- `reporting-strategy.md` — Reports & Dashboards vs CRM Analytics vs Data
  Cloud vs external BI

Open a PR adding any of the above if you hit the use case.
