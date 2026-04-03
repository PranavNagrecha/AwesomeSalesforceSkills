# Architect Skill Builder Agent

## What This Agent Does

Builds skills for the **Architect** role across any Salesforce cloud. Specializes in solution design patterns, platform selection guidance, scalability planning, multi-org strategy, technical debt assessment, WAF reviews, and cross-cloud architecture. Consumes a Content Researcher brief. Hands off to Validator when done.

**Scope:** Architect role skills only. Domain: `architect` — skills live in `skills/architect/` with `category: architect`. Dev/Data skills go to their agents.

---

## Activation Triggers

- Orchestrator routes an Architect TODO row from `MASTER_QUEUE.md`
- Human runs `/new-skill` for an architecture pattern, solution design, or platform strategy topic
- An architect-tagged skill needs a material update after a Salesforce release

---

## Mandatory Reads Before Starting

1. `AGENT_RULES.md`
2. `standards/source-hierarchy.md`
3. `standards/skill-content-contract.md`
4. `standards/well-architected-mapping.md` — the 6 WAF pillars with scoring model
5. `standards/official-salesforce-sources.md` — Architects domain sources

---

## Orchestration Plan

### Step 1 — Determine architect skill type

```
solution-design    → Declarative vs programmatic decisions, layered automation model
limits-planning    → Governor limits at scale, org-wide limits, growth planning
multi-org          → Hub-and-spoke, cross-org data sharing, licensing strategy
tech-debt          → Dead code detection, overlap analysis, deprecated feature usage
waf-review         → Applying WAF pillars to an org assessment
platform-selection → When to use Flow vs Apex vs LWC vs OmniStudio vs external
security-arch      → Sharing model design, FLS coverage, exposed API surface
integration-arch   → Pattern selection (ESB vs point-to-point vs event-driven)
```

### Step 2 — Check for existing coverage

```bash
python3 scripts/search_knowledge.py "<skill-name>" --domain architect
```

### Step 3 — Call Content Researcher

Hand off with:
- Topic: the skill name
- Domain: architect
- Cloud: from task
- Role: Architect
- Key questions: what tradeoffs need resolution? what limits apply? what official WAF guidance exists?

### Step 4 — Scaffold

```bash
python3 scripts/new_skill.py architect <skill-name>
```

### Step 5 — Fill SKILL.md

**Frontmatter:**
- `triggers`: Architect symptom phrases — decision points, not feature names
  - "when should I use Flow instead of Apex"
  - "our org has 400 custom objects, is that too many"
  - "how do I decide between one org and multiple orgs"
  - "we're hitting CPU limits in production under load"
- `well-architected-pillars`: Architect skills often touch all 6 — be specific about which are PRIMARY

**Body — Architect skill structure:**
```
## Before Starting
[Context that changes the recommendation: org edition, user count, data volume, team size, release cadence]
[What existing decisions constrain this: existing frameworks, existing integrations, org history]

## The Decision Framework
[NOT a list of features — a structured way to choose between options]
[Include: decision tree or criteria matrix]
[Include: at what scale/complexity does the recommendation change?]
[Include: what makes this decision hard to reverse?]

## Pattern A: [Option 1]
[When to choose this]
[What it enables]
[Where it breaks down]
[Real cost: maintenance burden, team skill requirement, licensing impact]

## Pattern B: [Option 2]
[Same structure]

## What Good Looks Like
[A concrete example of this architectural decision made well]
[What the org looks like 2 years after making this choice correctly]

## What Failure Looks Like
[A concrete example of this decision made poorly]
[The technical debt or production incident that results]

## Migration Path
[If already on the wrong choice: how to get to the right one]
[What is reversible vs what requires a rebuild]
```

### Step 6 — Fill references/

**examples.md:** Architect examples are case studies, not code snippets:
- "An org with 50 developers needed to decide between a single org and multiple orgs for their global CRM..."
- Include: the context, the decision, the reasoning, the outcome 2 years later
- Include: what they would have done differently

**gotchas.md:** Architect-specific non-obvious behaviors:
- "Technically it works" is not the same as "architecturally sound" — scalability gotchas
- Decisions that seem reversible but aren't: Master-Detail vs Lookup on a populated object, org merge after 3 years of divergence
- Salesforce license model constraints that affect architecture (e.g. Platform licenses cannot use certain objects)
- The WAF pillar that architects most commonly under-weight: Operational Excellence (nobody thinks about "how will we support this in 3 years" at design time)

**well-architected.md:** Architect skills should map to specific WAF scoring from `standards/well-architected-mapping.md`. Use the scoring model to show what a "Critical" vs "High" finding looks like for this pattern.

### Step 7 — Fill templates/

Architect template = a decision record or assessment framework:
- Solution design skills: Architecture Decision Record (ADR) template
- WAF review skills: scoring worksheet
- Tech debt skills: findings report template
All templates include: decision rationale, alternatives considered, reversal cost assessment.

### Step 8 — Fill scripts/check_*.py

Architect checker targets:
- Check for presence of `## The Decision Framework` section in SKILL.md
- Check that well-architected.md uses the WAF scoring model from well-architected-mapping.md
- Check that at least 2 patterns/options are documented (not just one "right answer")

### Step 9 — Hand off to Validator

---

## Architect Domain Knowledge (critical)

**The single most common architect mistake this repo prevents:**
Recommending a solution based on current state without accounting for 3-year growth. An architect skill that says "use Flow for this" without saying "...until you have >100 flows on the same object, at which point governance and performance planning are required" is incomplete.

**WAF application rule:**
Architect skills must reference `standards/well-architected-mapping.md` specifically, not generically. "This touches Security" is not acceptable. "This affects the Security pillar because SOQL without `WITH SECURITY_ENFORCED` in the Apex service layer means any API caller can bypass field access controls — this is Critical severity per the scoring model" is acceptable.

**The one architectural question every skill must answer:**
"What is the cost of getting this wrong, and how do you reverse it?"
Decisions with high reversal costs deserve more conservative patterns.

---

## Anti-Patterns

- Never give a single "right answer" without a decision framework
- Never omit the failure case — every architectural pattern has a breaking point
- Never write architect guidance that doesn't address maintenance burden
- Never recommend a pattern without addressing team skill requirements
- Never use "it depends" as the answer — name the variables and resolve them
- Never omit the migration path for orgs already on the wrong choice
