---
name: salesforce-learning-brief
description: "Turn a verified Salesforce research packet into a concise, role-aware learning brief with clear objectives, concept sequencing, worked examples, release caveats, checks for understanding, and citations mapped to claims. Trigger keywords: teach me Salesforce, explain Salesforce concept, create learning brief, Salesforce study guide, role-based lesson. NOT for open-ended source discovery or freshness verification — use architect/salesforce-learning-research first. NOT for generating production metadata or changing an org."
category: admin
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
triggers:
  - "teach me this Salesforce topic using verified current sources"
  - "turn these Salesforce sources into a beginner-friendly learning brief"
  - "create a role-based Salesforce study guide with knowledge checks"
  - "explain this Salesforce feature and distinguish facts from recommendations"
  - "prepare a cited lesson for an admin developer architect or release manager"
tags:
  - learning-brief
  - teaching
  - study-guide
  - citations
  - role-aware
  - knowledge-check
inputs:
  - "Verified research packet from architect/salesforce-learning-research or equivalent source-bounded evidence"
  - "Learner role, current level, desired outcome, time budget, and preferred depth"
  - "Release, API, org, product, and license context when material"
outputs:
  - "Learner-facing brief with objectives, prerequisites, mental model, workflow, example, caveats, citations, and checks for understanding"
  - "Practice task and next-step reading tied to the learner's outcome"
  - "Explicit list of unsupported or context-dependent claims not taught as fact"
dependencies:
  - architect/salesforce-learning-research
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-09-01
---

# Salesforce Learning Brief

Use this skill after evidence has been gathered and classified. The brief teaches a bounded Salesforce outcome without flattening product guarantees, recommendations, org assumptions, preview features, and practitioner judgment into one authoritative voice.

---

## Input Gate

A valid input must provide:

- learner role, current level, and concrete learning outcome;
- an evidence or research packet with claim-to-source mapping;
- release/API/product context for changing behavior;
- visible gaps, contradictions, and claims that must not be taught as fact.

When evidence is missing, do not fill the lesson from memory. Route to `architect/salesforce-learning-research`, remain explicitly source-bounded, or return a partial brief whose unsupported sections are marked.

---

## Brief Shape

| Section | Purpose | Maximum useful scope |
|---|---|---|
| Outcome | State what the learner can explain or do afterward | One measurable outcome |
| Prerequisites | Surface concepts or access needed first | Three to five items |
| Mental model | Give the organizing idea that makes details coherent | One diagram/table or short explanation |
| Core concepts | Teach only the concepts needed for the outcome | Three to seven concepts |
| Workflow | Show the order of decisions or actions | Five to nine steps |
| Worked example | Connect the concepts in one realistic scenario | One end-to-end example |
| Boundaries and caveats | Preserve release, license, security, limit, and org context | Only load-bearing caveats |
| Knowledge check | Test understanding, not recall of wording | Three to five questions |
| Practice task | Let the learner apply the concept safely | One bounded exercise |
| Sources | Map claims to evidence | Stable citations, not a link dump |

Do not reproduce the entire research packet. The packet is evidence; the brief is instruction.

---

## Role-Aware Teaching

Adjust examples and vocabulary without changing the facts.

| Learner | Emphasize | Avoid |
|---|---|---|
| Administrator | Business outcome, Setup model, permissions, automation interactions, safe validation | Assuming source-control or Apex fluency |
| Developer | Runtime behavior, metadata/code boundary, limits, testing, debugging, deployment | Treating every problem as code-first |
| Architect | Alternatives, NFRs, product boundaries, lifecycle, evidence, governance | A click-by-click tutorial with no tradeoffs |
| Analyst | Data meaning, joins, filters, security, freshness, interpretation limits | Presenting returned rows as complete business truth |
| Release/operations | Dependency order, gates, rollback, monitoring, audit evidence | Equating deploy success with outcome success |
| Consultant | Target identity, edition/package differences, handoff, client assumptions | Reusing one client's org facts in another context |

State the assumed level—foundation, practitioner, or advanced—and define unfamiliar terms at first use. Do not oversimplify away load-bearing Salesforce constraints.

---

## Claim-to-Teaching Rules

| Research state | How the brief may present it |
|---|---|
| `verified-fact` | State directly with a citation and applicability qualifier where material |
| `official-recommendation` | Attribute as recommended guidance, not a platform guarantee |
| `inference` | Label the reasoning and cite the facts it derives from |
| `assumption` | Present only inside the stated scenario; never generalize it |
| `unknown` | Teach the uncertainty and how to verify it |
| `unsupported` | Omit from the lesson or place in `Do not teach as fact` |

Every numeric limit, lifecycle date, feature status, command option, and release-sensitive behavior requires a nearby citation. Stable conceptual explanations can share citations at the paragraph or section level when the mapping remains unambiguous.

---

## Explain in Layers

Use a consistent learning progression:

1. **Definition** — what the capability is, in official/current terminology.
2. **Purpose** — which problem it solves and which problem it does not solve.
3. **Mental model** — the few relationships the learner must keep straight.
4. **Decision points** — what changes the correct approach.
5. **Procedure or pattern** — the safe sequence to use.
6. **Example** — one scenario with explicit assumptions.
7. **Failure modes** — the two or three mistakes most likely to mislead this learner.
8. **Verification** — how to prove the learner's interpretation or configuration.

For advanced learners, compress definitions and deepen tradeoffs, evidence, and exceptions. For beginners, reduce branching but retain safety and context.

---

## Examples Without Fabrication

A worked example must state:

- scenario and learner role;
- target product/release assumptions;
- object, metadata, or code names that are illustrative rather than claimed to exist;
- expected behavior;
- verification step;
- limits of what the example proves.

Use sample API names such as `Priority_Reason__c` only when clearly labeled illustrative. Never imply that a field, permission set, package, license, or org feature exists unless the evidence packet proves it.

For procedural lessons, show a dry-run, preview, scratch-org, or read-only verification path before any write. A learning brief does not authorize production mutation.

---

## Knowledge Checks

Prefer questions that expose misconceptions:

- distinguish two neighboring concepts;
- choose an approach under a changed constraint;
- identify which statement is a guarantee versus a recommendation;
- identify missing org/release evidence;
- predict a failure mode and verification step.

Provide answers separately so the learner can self-test. Do not write trivia about UI label location unless the UI path is the learning outcome.

---

## Recommended Workflow

1. **Validate the packet and learner context** with `architect/salesforce-learning-research`; preserve claim IDs and confirm role, level, outcome, time budget, and source boundary.
2. **Select and sequence concepts** from mental model to decision points to application, deferring neighboring topics that do not support the outcome.
3. **Draft with claim discipline** by mapping every material statement to evidence and retaining release, product, edition/license, API, org, and lifecycle qualifiers.
4. **Demonstrate transfer** with one worked example, explicit assumptions, failure modes, and a safe verification path.
5. **Assess and practice** with changed-constraint knowledge checks, answers, and one bounded practice task with acceptance checks and a stop condition.
6. **Expose uncertainty and validate** by listing unsupported/context-dependent claims under `Do not teach as fact`, running the bundled checker, and reviewing that every citation supports the claim attached to it.

---

## Completion Checklist

- [ ] One measurable learner outcome is stated
- [ ] Role, level, time budget, and product/release context are explicit
- [ ] Prerequisites and official terminology are clear
- [ ] Facts, recommendations, inferences, assumptions, and unknowns remain distinguishable
- [ ] Release-sensitive and numeric claims have nearby citations
- [ ] One example declares assumptions and verification
- [ ] Security, permissions, limits, and target identity remain visible where relevant
- [ ] Knowledge checks test application and misconceptions
- [ ] A bounded practice task is included
- [ ] Unsupported claims are omitted or listed under `Do not teach as fact`
- [ ] The brief does not authorize or perform production changes

---

## Output and Validation

Draft with `templates/salesforce-learning-brief-template.md`, then run:

```bash
python3 skills/admin/salesforce-learning-brief/scripts/check_salesforce_learning_brief.py --input path/to/learning-brief.md
```

The checker validates structure and citation signals; a human or independent reviewer must still confirm that each citation supports the associated claim.

---

## Related Skills

- `architect/salesforce-learning-research` — required evidence acquisition, freshness, and contradiction handling.
- Domain skill for the topic — supplies practitioner workflow and Salesforce-specific gotchas after source verification.
- `architect/salesforce-decision-analysis` — use when the learner's real need is to choose among viable approaches rather than understand one topic.
- Agent output-format skills — convert a completed brief to other artifacts without changing its claims.

See the bundled references for beginner/advanced variants, teaching gotchas, and LLM failure modes.
