# Validation gates index

Single source of truth for every gate the validators enforce. Generated
by `scripts/generate_validation_index.py`. **Do not hand-edit.** The
drift check in `scripts/validate_repo.py` catches stale copies.


- total gates: **79**  ·  errors: **61**  ·  warnings: **15**  ·  other: **3**

Each gate links to its source line. The intent line is the first line of
the enclosing function's docstring — read it for *why* the gate exists,
not just what it checks.

## `pipelines/validators.py`

| Line | Level | Function | Intent | Message |
|---|---|---|---|---|
| [162](pipelines/validators.py#L162) | **ERROR** | `validate_frontmatter` | — | missing frontmatter key `{…}` |
| [165](pipelines/validators.py#L165) | **ERROR** | `validate_frontmatter` | — | invalid category |
| [169](pipelines/validators.py#L169) | **ERROR** | `validate_frontmatter` | — | `{…}` must be a list |
| [174](pipelines/validators.py#L174) | **ERROR** | `validate_frontmatter` | — | `name` frontmatter `{…}` does not match folder name `{…}` |
| [179](pipelines/validators.py#L179) | **ERROR** | `validate_frontmatter` | — | `category` frontmatter `{…}` does not match parent domain folder `{…}` |
| [185](pipelines/validators.py#L185) | **ERROR** | `validate_frontmatter` | — | `description` must include a scope exclusion (e.g. 'NOT for ...') |
| [191](pipelines/validators.py#L191) | **ERROR** | `validate_frontmatter` | — | `{…}` contains an unfilled TODO marker; replace with real content |
| [195](pipelines/validators.py#L195) | **ERROR** | `validate_frontmatter` | — | `{…}` contains an unfilled TODO marker; replace with real content |
| [201](pipelines/validators.py#L201) | **ERROR** | `validate_frontmatter` | — | SKILL.md body has {…} words; minimum is {…} |
| [206](pipelines/validators.py#L206) | **ERROR** | `validate_frontmatter` | — | SKILL.md body contains {…} unfilled TODO marker(s); replace all TODOs with real content before syncing |
| [210](pipelines/validators.py#L210) | **ERROR** | `validate_frontmatter` | — | — |
| [235](pipelines/validators.py#L235) | _WARN_ | `_validate_checker_script_content` | Detect always-pass stubs in skill checker scripts. | checker script has only {…} meaningful lines — may be a stub; implement real validation logic |
| [251](pipelines/validators.py#L251) | _WARN_ | `_validate_checker_script_content` | Detect always-pass stubs in skill checker scripts. | checker script has no conditional branches (`if`); it will always produce the same output regardless of input |
| [257](pipelines/validators.py#L257) | _WARN_ | `_validate_checker_script_content` | Detect always-pass stubs in skill checker scripts. | checker script has no error-output path (sys.exit(1), raise, or ERROR/ISSUE/WARN print); it may never report problems |
| [270](pipelines/validators.py#L270) | **ERROR** | `validate_skill_structure` | — | missing required file `{…}` |
| [275](pipelines/validators.py#L275) | **ERROR** | `validate_skill_structure` | — | templates/ must contain at least one file |
| [277](pipelines/validators.py#L277) | **ERROR** | `validate_skill_structure` | — | scripts/ must contain at least one Python file |
| [286](pipelines/validators.py#L286) | **ERROR** | `validate_skill_structure` | — | missing `references/llm-anti-patterns.md` — add LLM-specific anti-patterns for this skill |
| [291](pipelines/validators.py#L291) | **ERROR** | `validate_skill_structure` | — | llm-anti-patterns.md contains {…} unfilled TODO marker(s) |
| [300](pipelines/validators.py#L300) | _WARN_ | `validate_skill_structure` | — | llm-anti-patterns.md has only {…} anti-pattern(s); CLAUDE.md requires 5+ (any heading or numbered-list format). |
| [314](pipelines/validators.py#L314) | _WARN_ | `validate_skill_structure` | — | llm-anti-patterns.md is {…} bytes, under the {…}-byte depth floor. For scale, the corpus 10th percentile is 3365 bytes and the median is 68… |
| [335](pipelines/validators.py#L335) | _WARN_ | `validate_skill_structure` | — | examples.md has no fenced block — add at least one worked artifact (code, YAML, JSON, metadata XML, or a concrete payload/table), not a pro… |
| [348](pipelines/validators.py#L348) | _WARN_ | `validate_skill_structure` | — | SKILL.md has no `## Recommended Workflow` section — add step-by-step agent instructions |
| [356](pipelines/validators.py#L356) | _WARN_ | `validate_skill_structure` | — | SKILL.md has no `## Questions to Ask Before Configuring` section — every skill updated on/after 2026-09-04 must tell the reader what to ask… |
| [367](pipelines/validators.py#L367) | **ERROR** | `validate_skill_structure` | — | missing `## Official Sources Used` section |
| [373](pipelines/validators.py#L373) | **ERROR** | `validate_skill_structure` | — | `## Official Sources Used` section is empty; list at least one source |
| [464](pipelines/validators.py#L464) | **ERROR** | `validate_depth_gate` | NEW skill: score >= DEPTH_BAR and a real Questions table. EXISTING skill | new skill scores {…}/{…} on scripts/score_skill_depth.py; the bar is {…}. Missing signals: {…} |
| [471](pipelines/validators.py#L471) | **ERROR** | `validate_depth_gate` | NEW skill: score >= DEPTH_BAR and a real Questions table. EXISTING skill | new skill: {…} |
| [478](pipelines/validators.py#L478) | **ERROR** | `validate_depth_gate` | NEW skill: score >= DEPTH_BAR and a real Questions table. EXISTING skill | depth score regressed {…} -> {…} vs HEAD (lost signals: {…}) |
| [530](pipelines/validators.py#L530) | **ERROR** | `validate_skill_authoring_style` | Style-level checks against `standards/skill-authoring-style.md`. | body has `{…}` section — frontmatter `description` is the canonical trigger surface; remove the body section or fold it into the descriptio… |
| [555](pipelines/validators.py#L555) | **ERROR** | `validate_skill_authoring_style` | Style-level checks against `standards/skill-authoring-style.md`. | body has `{…}` section while `references/well-architected.md` already covers it — keep pillar mapping in references/well-architected.md onl… |
| [600](pipelines/validators.py#L600) | **ERROR** | `validate_skill_authoring_style` | Style-level checks against `standards/skill-authoring-style.md`. | {…} paragraph(s) appear verbatim in both SKILL.md and references/gotchas.md (e.g. "{…}…") — keep the deep version in references/gotchas.md,… |
| [691](pipelines/validators.py#L691) | _WARN_ | `flush` | — | L{…}–L{…}: {…} consecutive `- **X** — ...` bullets should be a table (see standards/skill-authoring-style.md § 6.2) |
| [738](pipelines/validators.py#L738) | **ERROR** | `validate_skill_registry_record` | — | — |
| [745](pipelines/validators.py#L745) | **ERROR** | `validate_knowledge_source` | — | — |
| [826](pipelines/validators.py#L826) | _WARN_ | `validate_skill_similarity` | Flag near-duplicate skills as WARN. | near-duplicate of `{…}` (score {…}, description {…}, tags {…}, triggers {…}); review with `python3 scripts/audit_duplicates.py` or merge/re… |
| [906](pipelines/validators.py#L906) | _WARN_ | `validate_official_sources_uniqueness` | Flag skills in the same domain sharing a byte-identical Official Sources block. | `## Official Sources Used` is byte-identical to {…} other `{…}` skill(s): {…}. A shared per-domain source list is not grounding for this sk… |

## `pipelines/agent_validators.py`

| Line | Level | Function | Intent | Message |
|---|---|---|---|---|
| [136](pipelines/agent_validators.py#L136) | **ERROR** | `_parse_agent` | — | frontmatter: {…} |
| [139](pipelines/agent_validators.py#L139) | **ERROR** | `_parse_agent` | — | unable to parse frontmatter: {…} |
| [155](pipelines/agent_validators.py#L155) | **ERROR** | `_validate_frontmatter` | — | missing agent frontmatter schema — run `git pull` or restore agents/_shared/schemas/ |
| [165](pipelines/agent_validators.py#L165) | **ERROR** | `_validate_frontmatter` | — | frontmatter: {…} |
| [170](pipelines/agent_validators.py#L170) | **ERROR** | `_validate_frontmatter` | — | frontmatter `id: {…}` does not match folder name `{…}` |
| [205](pipelines/agent_validators.py#L205) | **ERROR** | `_validate_sections` | — | missing required section `## {…}`{…} |
| [216](pipelines/agent_validators.py#L216) | **ERROR** | `_validate_sections` | — | required sections are present but not in the canonical order defined by AGENT_CONTRACT.md |
| [279](pipelines/agent_validators.py#L279) | **ERROR** | `_validate_citations` | — | citation `skills/{…}/{…}` does not resolve to a skill folder |
| [293](pipelines/agent_validators.py#L293) | **ERROR** | `_validate_citations` | — | citation `{…}/{…}` does not resolve to skills/{…}/{…}/ |
| [305](pipelines/agent_validators.py#L305) | **ERROR** | `_validate_citations` | — | citation `templates/{…}` does not resolve to a real file/folder |
| [317](pipelines/agent_validators.py#L317) | **ERROR** | `_validate_citations` | — | citation `standards/{…}` does not resolve to a real file |
| [329](pipelines/agent_validators.py#L329) | **ERROR** | `_validate_citations` | — | citation `agents/_shared/probes/{…}` does not resolve to a probe md file |
| [344](pipelines/agent_validators.py#L344) | **ERROR** | `_validate_citations` | — | follow-up reference `agents/{…}` does not resolve to a real agent folder |
| [356](pipelines/agent_validators.py#L356) | **ERROR** | `_validate_citations` | — | slash command `/{…}` does not resolve to commands/{…}.md |
| [377](pipelines/agent_validators.py#L377) | **ERROR** | `_validate_citations` | — | MCP tool `{…}` cited but not registered in mcp/sfskills-mcp/src/sfskills_mcp/server.py |
| [402](pipelines/agent_validators.py#L402) | **ERROR** | `_validate_inputs_schema` | — | inputs.schema.json: invalid JSON ({…}) |
| [404](pipelines/agent_validators.py#L404) | **ERROR** | `_validate_inputs_schema` | — | inputs.schema.json must be a JSON Schema object |
| [406](pipelines/agent_validators.py#L406) | **ERROR** | `_validate_inputs_schema` | — | inputs.schema.json must define `properties` with at least one input |
| [436](pipelines/agent_validators.py#L436) | **ERROR** | `_validate_harness` | Enforce shape requirements for agents that declare a shared harness. | declares `harness: {…}` but {…} does not exist |
| [451](pipelines/agent_validators.py#L451) | **ERROR** | `_validate_harness` | Enforce shape requirements for agents that declare a shared harness. | harness=designer_base requires modes subset of {…}; unknown modes: {…} |
| [466](pipelines/agent_validators.py#L466) | **ERROR** | `_validate_harness` | Enforce shape requirements for agents that declare a shared harness. | harness=designer_base requires an `## Escalation / Refusal Rules` section (or `## Escalation Rules` alias) per refusal_patterns.md |
| [555](pipelines/agent_validators.py#L555) | **ERROR** | `_validate_no_cross_agent_duplication` | Flag prose paragraphs that appear verbatim across ≥2 non-deprecated AGENT.md files. | prose paragraph appears verbatim in {…} other AGENT.md file(s) ({…}). Move the canonical version into agents/_shared/ and link to it instea… |
| [601](pipelines/agent_validators.py#L601) | **ERROR** | `validate_agents` | Run every agent check against the repo. | duplicate agent id `{…}` — also declared at {…} |
| [625](pipelines/agent_validators.py#L625) | **ERROR** | `validate_agents` | Run every agent check against the repo. | agents.py lists runtime agent `{…}` but agents/{…}/AGENT.md does not exist |
| [661](pipelines/agent_validators.py#L661) | **ERROR** | `validate_agents` | Run every agent check against the repo. | runtime agent `{…}` has no matching slash-command — add commands/<slug>.md whose body links agents/{…}/AGENT.md |

## `scripts/validate_repo.py`

| Line | Level | Function | Intent | Message |
|---|---|---|---|---|
| [105](scripts/validate_repo.py#L105) | **ERROR** | `_check_skill_local_script` | py_compile + ``--help`` smoke for a single skill-local helper script. | py_compile failed: {…} |
| [115](scripts/validate_repo.py#L115) | **ERROR** | `_check_skill_local_script` | py_compile + ``--help`` smoke for a single skill-local helper script. | --help exited non-zero |
| [140](scripts/validate_repo.py#L140) | **ERROR** | `validate_one_skill` | Validate a single skill's structure + frontmatter. Does NOT run the | unable to parse frontmatter: {…} |
| [315](scripts/validate_repo.py#L315) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | duplicate skill id `{…}` also seen in {…} |
| [324](scripts/validate_repo.py#L324) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | duplicate skill name `{…}` also seen in {…} |
| [366](scripts/validate_repo.py#L366) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | skill `{…}` has no query fixture — add at least one entry |
| [386](scripts/validate_repo.py#L386) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | query `{…}` did not return `{…}` in top {…} |
| [397](scripts/validate_repo.py#L397) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | generated artifact is stale; run `python3 scripts/skill_sync.py --all` |
| [477](scripts/validate_repo.py#L477) | _WARN_ | `_check_orphan_skills` | Emit a WARN for each filtered skill no run-time agent cites (advisory). | skill `{…}` is cited by no run-time agent (advisory). Wire it only if some agent's output would be wrong without it — a citation an agent w… |
| [605](scripts/validate_repo.py#L605) | **ERROR** | `_check_agent_citation_quality` | Gate the quality and size of each run-time agent's reading list. | Mandatory Reads entry for `skills/{…}` is an echo stub — its description ({…}) restates the slug and tells the agent nothing the path did n… |
| [628](scripts/validate_repo.py#L628) | _WARN_ | `_check_agent_citation_quality` | Gate the quality and size of each run-time agent's reading list. | {…} Mandatory Reads entr(ies) carry no justification at all: {…}. A bare path tells the agent what to open but not why, so it cannot decide… |
| [637](scripts/validate_repo.py#L637) | _WARN_ | `_check_agent_citation_quality` | Gate the quality and size of each run-time agent's reading list. | {…} Mandatory Reads entr(ies) restate the slug behind a bucketing label: {…}. Stripping the label leaves a description identical to the ski… |
| [646](scripts/validate_repo.py#L646) | _WARN_ | `_check_agent_citation_quality` | Gate the quality and size of each run-time agent's reading list. | {…} numbered skill reads in this AGENT.md, over the advisory ceiling of {…}. Past that, the list stops being a reading list and becomes a c… |
| [751](scripts/validate_repo.py#L751) | ? | `main` | — | — |
| [761](scripts/validate_repo.py#L761) | **ERROR** | `main` | — | — |
| [780](scripts/validate_repo.py#L780) | ? | `main` | — | — |
| [791](scripts/validate_repo.py#L791) | ? | `main` | — | — |
