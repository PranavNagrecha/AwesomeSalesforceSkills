# Agent Contract

Every agent in this repo — build-time or run-time — follows the same contract. This file defines that contract.

---

## Two classes of agents

| Class | Purpose | Examples | Invoked by |
|---|---|---|---|
| **Build-time** | Produce and maintain the skill library itself | `orchestrator`, `task-mapper`, `content-researcher`, the 4 `*-skill-builder` agents, `validator`, `currency-monitor` | Repo maintainers via `/run-queue`, scheduled task |
| **Run-time** | Use the skill library to do real Salesforce work against a user's org / codebase | `apex-refactorer`, `trigger-consolidator`, `test-class-generator`, `soql-optimizer`, `security-scanner`, `flow-analyzer`, `bulk-migration-planner`, `lwc-auditor`, `deployment-risk-scorer`, `agentforce-builder`, `org-drift-detector` | End users via slash commands, direct AGENT.md read, or MCP `get_agent` tool |

See [`RUNTIME_VS_BUILD.md`](./RUNTIME_VS_BUILD.md) for the full roster.

---

## AGENT.md frontmatter (required)

Every `agents/<slug>/AGENT.md` MUST start with a YAML frontmatter block validated against [`schemas/agent-frontmatter.schema.json`](./schemas/agent-frontmatter.schema.json):

```yaml
---
id: field-impact-analyzer          # must match the folder name (kebab-case)
class: runtime                     # runtime | build
version: 1.0.0                     # semver
status: stable                     # stable | beta | deprecated
requires_org: true                 # true if the agent needs an sf org alias to function
modes: [single]                    # [single] or [design, audit] etc. — free list of mode names
owner: sfskills-core               # team or handle responsible for the agent
created: 2026-04-16                # ISO date of first commit
updated: 2026-04-16                # ISO date of last material change
---
```

The canonical list of frontmatter keys, enums, and constraints lives in the JSON Schema. Do not duplicate it here.

---

## What an AGENT.md must contain

The required section shape depends on the agent's `class`.

### Run-time agents (`class: runtime`)

MUST have — after the frontmatter — all eight sections, in this order:

1. **What This Agent Does** — one paragraph, plain English, ends with the scope boundary.
2. **Invocation** — the three invocation modes (direct read / slash command / MCP `get_agent`) and what args the agent expects.
3. **Mandatory Reads Before Starting** — the files and skills the agent MUST read first. Always includes `AGENT_RULES.md` + any domain-specific decision trees or templates.
4. **Inputs** — structured list of what the agent needs from the caller (file paths, object names, target org alias, etc.). Ask for missing inputs up front; never guess. The canonical schema for typed inputs lives alongside the agent at `agents/<slug>/inputs.schema.json` when present; the Inputs section in the markdown is the human-readable view of that schema.
5. **Plan** — numbered steps. Each step cites the skill, template, or decision tree it relies on. Steps use MCP tools where the agent needs live-org data. Where possible, steps reference a probe recipe from [`probes/`](./probes/) rather than inlining a SOQL snippet.
6. **Output Contract** — exactly what the agent returns. Every run-time agent returns an envelope conforming to [`schemas/output-envelope.schema.json`](./schemas/output-envelope.schema.json), including at minimum: a `summary`, a `confidence` score (HIGH/MEDIUM/LOW — see rubric below), a **Process Observations** block (see below), and `citations[]` listing every skill/template/decision-tree branch the agent consulted.
7. **Escalation / Refusal Rules** — conditions under which the agent stops and asks a human. Refusal reasons should use the canonical codes from [`REFUSAL_CODES.md`](./REFUSAL_CODES.md) so downstream tooling can aggregate them. At minimum every agent covers: missing org connection when one is required, ambiguous inputs, contradicting skills (resolved per `standards/source-hierarchy.md`).
8. **What This Agent Does NOT Do** — explicit non-goals. Prevents scope creep.

### Build-time agents (`class: build`)

Build-time agents don't take caller-supplied inputs and don't produce user-facing deliverables in the same way — they read queues, commit skills, route work. They MUST have:

1. **What This Agent Does**
2. **Invocation** (alias: `Activation Triggers`, `Triggers`)
3. **Mandatory Reads Before Starting**
4. **Plan** (alias: `Orchestration Plan`)
5. **What This Agent Does NOT Do** (alias: `Anti-Patterns`)

Build-time agents MAY include `Inputs`, `Output Contract` (alias: `Output Format`), and `Escalation / Refusal Rules` when those concepts apply.

### Accepted section aliases

| Canonical name | Also accepted as |
|---|---|
| Invocation | `Activation Triggers`, `Triggers` |
| Plan | `Orchestration Plan` |
| Output Contract | `Output Format` |
| Escalation / Refusal Rules | `Escalation Rules` |
| What This Agent Does NOT Do | `Anti-Patterns` |

### The Process Observations requirement

Every run-time agent's Output Contract MUST include a **Process Observations** section, separate from the direct deliverable. This is the agent reporting back what it noticed *about the org and the process* while executing the task — the kind of peripheral signal a senior consultant captures in their head during a one-hour engagement but a junior admin walks past.

Why this matters: we are not just building. We are building while analyzing. Every agent run is also a lightweight assessment of the org's health in the agent's domain. An admin asking "rename this field" should also learn "by the way, 12 fields on this object have never been populated" — because that's the formula a real architect runs in the background.

Process Observations must include at minimum:

- **What was healthy** — patterns the org already gets right that the agent noticed in passing.
- **What was concerning** — issues the agent saw that weren't part of the direct ask but warrant attention.
- **What was ambiguous** — things the agent couldn't resolve and the human should adjudicate.
- **Suggested follow-up agents** — one or two other run-time agents that would deepen the analysis, with a one-sentence "because…".

Each observation conforms to [`schemas/observation.schema.json`](./schemas/observation.schema.json) so every run contributes to a rollable org-health signal.

Rules:

- Process Observations are observations, not accusations. "Noticed X" not "You did Y wrong."
- Every observation cites what the agent was looking at when it made the call — a file path, an MCP probe result, a query count.
- Do not inflate. If the agent genuinely observed nothing notable beyond the deliverable, say "nothing notable outside the direct finding." Empty honesty beats padded signal.
- Process Observations do NOT cross the boundary into the deliverable. They enrich, they don't replace.

### The Confidence rubric

Every run-time agent reports a single overall confidence: **HIGH / MEDIUM / LOW**. Absent a domain-specific override in the agent's own Plan, use this default rubric:

| Score | Condition |
|---|---|
| **HIGH** | All mandatory inputs were supplied, all required MCP probes returned without pagination or truncation errors, every recommendation cites at least one skill or template that exists in the registry, and the repo scan (if any) ran over a complete codebase. |
| **MEDIUM** | One probe paginated, one recommendation freestyled (no matching skill), or one mandatory-but-soft input (e.g. `repo_path`) was missing and a sensible default was used. |
| **LOW** | Any of: the target org was unreachable; a required input was missing and substituted; a critical skill/template citation resolved to a TODO; the agent had to freestyle more than one recommendation. |

An agent MAY override or extend this rubric in its Plan, but MAY NOT omit the score.

### Citations

Citations are data, not prose. Every output ends with a `citations[]` block where each entry matches [`schemas/citation.schema.json`](./schemas/citation.schema.json):

```json
{
  "type": "skill",
  "id": "admin/permission-set-architecture",
  "path": "skills/admin/permission-set-architecture/SKILL.md",
  "used_for": "PSG composition per persona"
}
```

`type` is one of `skill`, `template`, `standard`, `decision_tree`, `mcp_tool`, `probe`. Every citation must resolve to a real path (or a real MCP tool name) at validation time.

---

## Rules every agent follows

1. **Skill-first, never freestyle.** If `search_skill` or `get_skill` returns a matching skill, the agent MUST use that skill's guidance. If no skill matches, the agent MAY freestyle but MUST flag `confidence: LOW` and suggest adding the missing skill via `/request-skill`.

2. **Templates are canonical.** When generating Apex / LWC / Flow / Agentforce scaffolds, reference the file under `templates/` — never inline a parallel implementation. If a template is incomplete for the use case, flag it in the report instead of freestyling.

3. **Decision trees route technology choices.** If the user's request involves picking between automation / async / integration / sharing mechanisms, the agent MUST consult the matching file under `standards/decision-trees/` and cite which branch it followed.

4. **Source hierarchy for contradictions.** When skills disagree, Tier 1 (official Salesforce docs) wins. Per `standards/source-hierarchy.md`.

5. **Org-aware where possible.** If an MCP target-org is connected, the agent SHOULD call `describe_org` / `list_custom_objects` / `list_flows_on_object` / `validate_against_org` to ground recommendations in reality. If no org is connected, the agent MUST say so in the output and continue in "library-only" mode.

6. **Shared probes over inline SOQL.** Where a probe recipe exists under [`probes/`](./probes/) for an Apex-reference scan, a Flow-metadata scan, a matching/duplicate-rule listing, etc., the agent MUST cite the probe rather than inline the SOQL. This is how we prevent the same false-positive-avoidance logic from being re-invented in every agent.

7. **No hidden side effects.** Run-time agents NEVER deploy to an org, NEVER run `sf project deploy`, NEVER mutate files outside the paths the user gave as input. They produce plans, patches, and reports — execution is the human's call.

8. **One agent per invocation.** No auto-chaining. If another agent would help, recommend it in the output; don't silently invoke it.

9. **Return a report the user can paste into a PR.** Every output ends with a "Citations" block listing every skill id, template path, probe id, and decision tree branch the agent consulted — structured per the Citations schema above.

10. **The Apex security idiom is canonical here, not restated per agent.** Any agent that reads, writes, or scores Apex SOQL / SOSL / DML links [Apex security idiom by API version](#apex-security-idiom-by-api-version) rather than repeating the rule in its own Plan. The idiom is version-gated and changed in Summer '26; six divergent copies is exactly how the previous version went stale in-place.

11. **Every Apex identifier in a Plan step is copied, never recalled.** Class names, method names, parameter lists, and enum values that appear in a Plan step must be pasted from the `templates/apex/**/*.cls` file the step cites, or from official Salesforce documentation named in the same step. Writing a plausible-sounding name from memory is worse than writing none: the agent hands it to the user as finished work, and it does not compile. This rule is mechanically checkable — extract every `Identifier.method` token from an AGENT.md's Plan sections and grep it against `templates/apex/**/*.cls` plus a short allowlist of platform namespaces (`System`, `Schema`, `Security`, `Database`, `Test`, `Limits`, `Messaging`, `ConnectApi`, `Http*`) — so a future validator can enforce it instead of leaving it to review. Names that reached shipped agents before this rule existed, none of which exist in Apex: `stripInaccessibleFields`, `SecurityUtils.requireUpdateable`, `TestDataFactory.accounts(200)`, `MockHttpResponseGenerator.forEndpoint(…)`, `TestUserFactory.standardUser()`, `Test.setMock(ConnectApi.ConnectApi.class, …)`.

---

## Apex security idiom by API version

Canonical. Apex agents cite this section; they do not restate it.

The controlling fact is the **`apiVersion` in the class's `.cls-meta.xml`**, not the org's release. A Summer '26 org runs a class pinned to 58.0 quite happily, and that class keeps the older behaviour. An agent that cannot see the `apiVersion` says so and states which row it assumed.

| Class `apiVersion` | Default access mode | Read idiom | Write idiom | `WITH SECURITY_ENFORCED` |
|---|---|---|---|---|
| **67.0+** (Summer '26+) | **User mode.** SOQL, SOSL, DML, and `Database` methods enforce the running user's sharing rules, FLS, and object permissions with no keyword at all | `WITH USER_MODE` to state the intent explicitly; `WITH SYSTEM_MODE` plus a `// reason:` comment to opt out | `as user` / `as system`, or `AccessLevel.USER_MODE` on `Database` methods | **Does not compile.** Removed in 67.0. The compiler emits `WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead` |
| **57.0 – 66.0** | System mode | `WITH USER_MODE` — GA since Spring '23 (API 57.0) | `as user`, or `AccessLevel.USER_MODE` on `Database` methods | Compiles, but is the weaker construct: it checks only the `SELECT` list, mishandles polymorphic fields, and reports one violation rather than all. Legacy — migrate it |
| **≤ 56.0** | System mode | `WITH SECURITY_ENFORCED`, or `Security.stripInaccessible` on the result (48.0+) | `Security.stripInaccessible(AccessType.CREATABLE, records).getRecords()` (48.0+); below that, explicit `Schema.DescribeFieldResult` checks | The idiom available at this version. Prefer raising the class's `apiVersion` over hardening it in place |

What follows from the table:

- **Never emit `WITH SECURITY_ENFORCED` into new or rewritten code.** `WITH USER_MODE` is the default read idiom for every class an agent authors, at every version from 57.0 up.
- **A scanner flags `WITH SECURITY_ENFORCED` rather than scoring it clean.** On a 67.0+ class it is P0 — a compile failure, not a style note. On 57.0–66.0 it is P2 tech debt with a named migration. Treating its presence as evidence of a secure query is a defect in the scanner, at every version.
- **Default user mode is not permission to drop enforcement.** A 67.0 class still needs `Security.stripInaccessible` on write paths that assemble records from user input: user mode throws and fails the whole DML, while `stripInaccessible` removes the inaccessible fields and continues. Choose per `skills/apex/apex-stripinaccessible-and-fls-enforcement` — the choice is about whether silent partial success is acceptable, and default user mode does not decide it.
- **`Security.stripInaccessible(AccessType, records)` returns an `SObjectAccessDecision`.** Operate on `.getRecords()`; DML on the original list is unenforced. There is no `stripInaccessibleFields`.

Official sources: *Database Operations Run in User Mode by Default, Not System Mode* (`release-notes.rn_apex_default_user_mode.htm`, Summer '26); *The WITH SECURITY_ENFORCED SOQL Clause Is Removed* (`release-notes.rn_apex_removed_withSecurityEnforced.htm`, Summer '26); *Secure Apex Code with User Mode Database Operations (Generally Available)* (`release-notes.rn_apex_User_Mode_GA.htm`, Spring '23); *Enforcing Object and Field Permissions in Apex* (Lightning Web Components Developer Guide).

---

## Anti-patterns

- Reading `skills/` by globbing. Use `search_skill` or `get_skill` — they respect the registry.
- Inlining Apex patterns from memory. Use `templates/apex/*.cls`.
- Recommending a technology without citing the decision tree.
- Returning "HIGH confidence" without at least one official Salesforce docs citation in the skill's `references/`.
- Running `sf project deploy`, `sf data upsert`, or any write operation against the org.
- Inlining SOQL that already exists as a probe recipe.
- Returning Process Observations that restate the deliverable instead of adding peripheral signal.
- **Citing skills to clear the orphan gate.** `validate_repo.py` (`_check_orphan_skills`) emits a **WARN** — advisory, not an ERROR — for any skill that is neither cited in some agent's `dependencies.skills:` nor marked `runtime_orphan: true`. It used to ERROR, which made mass-citation the cheapest route to a green build; that is exactly how the stub wave happened, so coverage is now a signal rather than a contract. The WARN is cheap to leave standing. If a skill genuinely has no owner, record that with `runtime_orphan: true` plus a `runtime_orphan_reason:` — never with a citation the agent will not read, and never in bulk to quiet the warning. A citation the agent does not use makes the library measurably worse: it inflates the coverage number while diluting the reading list of the one agent that now has to carry it. That is how 52% of Mandatory Reads entries became echo stubs — see [Mandatory Reads](#mandatory-reads-human-authored-justified-bounded).
- **Restating canonical content across AGENT.md files.** When two or more AGENT.md files contain the same prose paragraph word-for-word, the canonical version belongs in `agents/_shared/` (linked) rather than copy-pasted. Enforced as ERROR by `pipelines/agent_validators.py:_validate_no_cross_agent_duplication` — the analog of skills' style guide § 6.6 (verbatim duplication between SKILL.md and references/gotchas.md). Exemptions: paragraphs inside the deliberately-templated Wave 10 sub-sections `### Persistence (Wave 10 contract)` and `### Scope Guardrails (Wave 10 contract)` (per `DELIVERABLE_CONTRACT.md`), and AGENT.md files with `status: deprecated` (their stub language is intentional).

---

## Creating a new agent — and adding skills to existing ones

Two workflows govern the agent ↔ skill relationship; both treat the wiring as a judgment step, not a sweep:

- **New skill** → see [`commands/new-skill.md`](../../commands/new-skill.md), Step 6. After scaffolding the skill, walk the agent roster and decide whether any agent meaningfully needs it. Zero agents is a valid answer, but not a silent one: record it as `runtime_orphan: true` with a reason, because the validator ERRORs on a skill that recorded no decision either way.
- **New run-time agent** → see [`commands/new-agent.md`](../../commands/new-agent.md). After scaffolding the agent, walk the skill library and cite the skills that genuinely change the agent's output. Don't dilute `Mandatory Reads` with adjacent-but-unused skills, and don't fabricate citations to non-existent skills.

The bar in both directions is the same: a citation should answer "the agent's output would be wrong without this skill in this scenario." If you can't name the scenario, drop the citation.

### Mandatory Reads: human-authored, justified, bounded

`## Mandatory Reads Before Starting` is a reading list a human has to defend, not an index of the library. Six normative rules:

1. **Every `skills/<domain>/<slug>` line carries a justification, and a human wrote it.** The justification names the scenario in which this agent's output would be *wrong* without that skill — not what the skill is about. One line is enough.

2. **A description that restates the slug is not a justification — it is an ERROR.** Dashes-to-spaces, any casing, trailing period, all the same defect:

   ```text
   BAD   `skills/admin/fsl-mobile-app-setup` — Fsl mobile app setup
   GOOD  `skills/data/person-accounts` — for any Account-variant design
   ```

   The bad line tells the agent nothing it could not read off the path, so it buys no accuracy and spends context. `scripts/patch_agent_skill.py` refuses to write one (exit code 2, via its exported `is_echo_description()` predicate), and `validate_repo.py` (`_check_agent_citation_quality`) imports the same predicate and raises a per-line ERROR on any Mandatory Reads entry it rejects — so a stub hand-edited straight into an AGENT.md now fails CI too. Know what that predicate does and does not cover: it is an exact match after normalisation, so it catches a re-run of the machine-generated stub wave and nothing subtler — appending one word ("Fsl mobile app setup guidance") clears the gate while leaving the line just as useless. It is a regression guard, not a filler detector. Rule 2 is a rule about writing, and review still has to enforce it; CI only stops the exact shape that produced 555 stubs.

3. **A bare citation — a `skills/…` line with no description at all — is not acceptable in a new or reworked list.** Pre-existing bare lines are tolerated until their agent is next revised; revising a list means justifying what survives it.

4. **The list is bounded.** Two different things, kept apart on purpose:

   - *Convention, enforced by review only.* Design target is **8–25** skill reads per agent. Above 25, the section should open with a one-line note saying why the agent is unusually broad. No code checks either number — treat them as the bar a reviewer holds you to, not as something a build will catch.
   - *Gate, enforced by CI.* `validate_repo.py` (`_check_agent_citation_quality`) emits a **WARN** above **40** skill reads. Advisory, not an ERROR — the ceiling was set from the measured corpus (45/44/44/42, then a drop to 36), so it separates the outliers from the body of the distribution rather than asserting a principled maximum.

   Only `skills/` lines count toward either bound; `agents/_shared/*`, `AGENT_RULES.md`, `standards/decision-trees/*`, `templates/*`, `evals/*` and probe entries are exempt, because they are per-run contracts rather than per-topic reference. The gate counts numbered `skills/…` lines **anywhere in the AGENT.md**, not just inside `## Mandatory Reads Before Starting`. Moving entries under some other heading is not a way to clear it: the agent still opens the same files, so the budget is unchanged. Shortening the list means dropping reads the agent does not need, or splitting the agent in two.

5. **YAML and prose must agree.** Every entry in `dependencies.skills:` has exactly one matching Mandatory Reads line and vice versa. The validator's coverage check reads the YAML block only, so a citation that lives in YAML alone is invisible to every human reviewer — which is precisely where padding hides. The pairing governs the reading list, and only the reading list. A `skills/…` path named elsewhere in the AGENT.md as somewhere to *send the caller* — the Scope Guardrails format-referral to `skills/admin/agent-output-formats` is the standing example — is a pointer, not a read: the agent hands it to the user rather than loading it before starting. Do not back-fill such a pointer into `dependencies.skills:` to make the two "match"; that manufactures exactly the unread citation rule 1 exists to prevent.

6. **Removing a read is a judgment call in both directions.** Be conservative about dropping something the agent plausibly consults on a normal run; be ruthless about vertical- or product-specific skills an agent's own `What This Agent Does` never claims to cover. When a skill is genuinely in scope but the line is an echo stub, the fix is to *write the justification*, not to delete the read.

The matching anti-pattern — citing skills to clear the orphan gate — is listed under [Anti-patterns](#anti-patterns).

---

## Testing an agent

Before a new AGENT.md is merged, it must pass:

1. **Structural gate** — `python3 scripts/validate_repo.py --agents` passes. This enforces frontmatter schema, section order, citation resolution, MCP-tool-name resolution, slash-command resolution, and follow-up-agent resolution.
2. **Citation gate** — every skill / template / decision tree / probe the AGENT.md mentions must exist at the cited path. Enforced by the structural gate.
3. **Dry-run gate** — the maintainer runs the agent's plan against a sample input and checks that the output envelope is well-formed. See [`evals/agents/README.md`](../../evals/agents/README.md) for the snapshot-eval harness.

See [`commands/review.md`](../../commands/review.md) for the review flow.
