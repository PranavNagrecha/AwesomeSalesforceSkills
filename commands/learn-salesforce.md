# /learn-salesforce — Research and teach one Salesforce topic with current evidence, citations, practice, and knowledge checks

Wraps [`agents/salesforce-learning-guide/AGENT.md`](../agents/salesforce-learning-guide/AGENT.md). It produces a learning brief, not repository content or org changes.

---

## Step 1 — Collect inputs

Require:

```text
1. What Salesforce topic should be learned?
2. What should the learner be able to explain or do afterward?
3. What is the learner's role and current level (foundation, practitioner, advanced)?
```

Collect when available: time budget, depth, product/release/API/org context, supplied sources, source boundary, and safe practice authority.

When the user asks to work from attached or named sources, default to `source_boundary: supplied-only`. Do not browse or fill gaps silently unless outside research is explicitly authorized.

---

## Step 2 — Load the agent

Read `agents/salesforce-learning-guide/AGENT.md` and every Mandatory Read. Validate inputs against `agents/salesforce-learning-guide/inputs.schema.json`.

---

## Step 3 — Execute the learning lifecycle

1. Bound the topic and disambiguate terminology.
2. Build a source inventory and atomic, release-aware claim ledger.
3. Resolve contradictions and preserve unsupported/unknown claims.
4. Synthesize a role-aware brief with one worked example.
5. Add application questions, answers, and one safe practice task.

Capture every skill, source, evidence item, and MCP tool consulted.

---

## Step 4 — Deliver the output

Conform to `agents/_shared/DELIVERABLE_CONTRACT.md`:

- Markdown: `docs/reports/salesforce-learning-guide/<run_id>.md`
- JSON: `docs/reports/salesforce-learning-guide/<run_id>.json`
- Atomic pair, short chat confirmation, and fenced JSON envelope preview
- `--no-persist` allowed for exploratory learning

The report contains the research digest, learning brief, caveats, knowledge checks/answers, safe practice task, and `Do Not Teach as Fact` section.

---

## Step 5 — Recommend one follow-up

Recommend the single next domain skill, practice exercise, or deeper brief that directly advances the stated learning outcome. Do not launch it automatically.

---

## What this command does NOT do

- Does not create or modify canonical SfSkills repository packages.
- Does not fabricate missing source support or blend outside research into supplied-only work.
- Does not certify the learner or provide legal/compliance assurance.
- Does not mutate an org, grant permissions, or use production as a practice environment.
