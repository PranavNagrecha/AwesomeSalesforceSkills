# Skill Builder Core

The four skill-builders — `admin-skill-builder`, `dev-skill-builder`, `data-skill-builder`, `architect-skill-builder` — share 80% of their workflow. This file is that shared core. Each domain-specific builder extends or specializes from here.

Read the builder AGENT.md alongside this file: the AGENT.md holds what makes that builder distinct (trigger phrasing, body template, gotcha ideas, checker targets). The workflow itself lives here.

---

## Shared activation triggers

Every skill-builder activates on one of:

- Orchestrator routes a `TODO` / `RESEARCHED` / `RESEARCH` row in `MASTER_QUEUE.md` whose domain matches the builder.
- A human runs `/new-skill` for a topic the builder owns.
- A skill under `skills/<domain>/` needs a material update.

Each builder's AGENT.md lists its specific domains. Example: `dev-skill-builder` owns `apex`, `lwc`, `flow`, `integration`, `devops`.

---

## Shared mandatory reads

1. `AGENT_RULES.md`
2. `standards/source-hierarchy.md` — resolves contradictions between Tier 1/2/3 sources
3. `standards/skill-content-contract.md` — what every SKILL.md must contain
4. `standards/official-salesforce-sources.md` — starting point for citations
5. `agents/_shared/AGENT_CONTRACT.md` — the contract this builder lives under

Builder-specific additions (naming conventions, code review checklist, WAF mapping) are listed in the builder's own AGENT.md.

---

## Shared workflow (9 steps)

### Step 1 — Get the task

Read from `MASTER_QUEUE.md` (or the calling agent) the task row with these fields at minimum: skill name (kebab-case), domain, cloud, role, short description. If the row is missing any of these, refuse per `REFUSAL_MISSING_INPUT`.

### Step 2 — Check for existing coverage

```bash
python3 scripts/search_knowledge.py "<skill-name>" --domain <domain>
```

- `has_coverage: true` → surface the existing skill. The default is to extend it, not duplicate. Only proceed with a new skill if the topic is genuinely orthogonal.
- `has_coverage: false` → proceed to Step 3.

### Step 3 — Call Content Researcher

Hand off to `agents/content-researcher/` with: topic, domain, cloud, role, and the specific questions the skill must answer (limits involved, security posture, API-version sensitivities, governor-limit implications — whichever matter for the domain).

Wait for the research brief. Do not write skill body without it. An un-grounded skill is a liability.

### Step 4 — Scaffold

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

The scaffolder produces the full package with pre-seeded TODOs and official sources.

### Step 5 — Fill `SKILL.md`

Frontmatter rules that apply to every builder:

- `name` must match the folder name.
- `category` must match the parent domain.
- `description` must include an explicit scope exclusion (`"NOT for …"`).
- `triggers` must be 3+ **symptom phrases a practitioner would type** — not feature names. Each ≥ 10 characters.
- `inputs` must name the specific context the skill requires.
- `outputs` must name concrete artifacts.

Body rules:

- ≥ 300 words.
- Ends with a `## Recommended Workflow` section (3–7 numbered steps an AI agent follows when this skill activates).
- Every factual claim about platform behavior must cite the backing source — official first, local second.

The builder's own AGENT.md defines the body structure for that domain (e.g. "Mode 1 / Mode 2 / Mode 3" for admin; "Build / Review / Troubleshoot / Performance & Scale" for dev).

### Step 6 — Fill `references/`

- `examples.md` — real scenarios, not synthetic ones. Domain-specific guidance lives in the builder's AGENT.md.
- `gotchas.md` — non-obvious platform behaviors the skill's users hit.
- `well-architected.md` — map the skill to WAF pillars with usage context, and list `## Official Sources Used` with at least one entry.
- `llm-anti-patterns.md` — 5+ mistakes AI assistants commonly make in this skill's domain; each entry includes what the LLM generates wrong, why, the correct pattern, and a detection hint.

### Step 7 — Fill `templates/`

Every skill ships at least one deployable or copy-ready template. The builder's AGENT.md says what that looks like in its domain (configuration checklist vs Apex scaffold vs data-migration playbook vs decision matrix).

Every template includes a verification section: *How to confirm this is working correctly.*

### Step 8 — Fill `scripts/check_*.py`

Python stdlib only. At minimum the checker must have: ≥ 10 meaningful lines, at least one conditional branch, and at least one error-output path (`sys.exit(1)`, `raise`, or ERROR/ISSUE/WARN print). Stub checkers fail validation.

The builder's AGENT.md lists the 2–3 checks that matter most in its domain.

### Step 9 — Hand off to Validator

```
Hand off path: skills/<domain>/<skill-name>
```

Validator runs both structural and quality gates. On `SHIPPABLE`, Validator commits. Builders do NOT commit.

---

## Anti-patterns shared across all builders

- **Freestyling body content** — every factual claim must come from the research brief or an official source; inference without citation is not allowed.
- **Treating scaffold TODOs as placeholders** — they are mandatory content slots, not suggestions. `validate_repo.py` fails hard on residual TODO markers.
- **Declaring a skill "done" without `## Recommended Workflow`** — the section exists so an AI agent activating the skill knows what to do; without it the skill is inert.
- **Skipping `llm-anti-patterns.md`** — this is the file that teaches future skill consumers which training-data shortcuts to avoid. It is not optional.
- **Duplicating a decision tree's logic in a skill body** — link to the tree under `## Related` instead; do not re-answer its decisions.
- **Inventing template code when a canonical template exists** — reference `templates/<domain>/…` by relative path. If a needed idiom is missing, flag the gap rather than inventing a one-off.

---

## How a builder's AGENT.md extends this core

Each builder's AGENT.md may specialize:

- `Activation Triggers` — tighten to the builder's domain vocabulary.
- `Mandatory Reads Before Starting` — add the domain-specific standards / decision trees.
- `Step 5 — Fill SKILL.md` — provide the body template for the domain (Mode 1/2/3 for admin, Build/Review/Troubleshoot/Performance for dev, etc.).
- `Step 6 — Fill references/` — list domain-specific gotchas.
- `Step 8 — Fill scripts/check_*.py` — list the 2–3 highest-value checks.
- `Anti-Patterns` — add domain-specific anti-patterns.
- Extra trailing sections — "Admin Domain Knowledge", "Dev Domain Knowledge", etc. capturing the non-negotiable mental model for the domain.

Builders SHOULD NOT repeat the shared workflow verbatim in their own AGENT.md. If a step here applies as-is, cite this file and move on.
