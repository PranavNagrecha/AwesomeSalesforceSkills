# Validation gates index

Single source of truth for every gate the validators enforce. Generated
by `scripts/generate_validation_index.py`. **Do not hand-edit.** The
drift check in `scripts/validate_repo.py` catches stale copies.


- total gates: **63**  ·  errors: **57**  ·  warnings: **6**

Each gate links to its source line. The intent line is the first line of
the enclosing function's docstring — read it for *why* the gate exists,
not just what it checks.

## `pipelines/validators.py`

| Line | Level | Function | Intent | Message |
|---|---|---|---|---|
| [141](pipelines/validators.py#L141) | **ERROR** | `validate_frontmatter` | — | missing frontmatter key `{…}` |
| [144](pipelines/validators.py#L144) | **ERROR** | `validate_frontmatter` | — | invalid category |
| [148](pipelines/validators.py#L148) | **ERROR** | `validate_frontmatter` | — | `{…}` must be a list |
| [153](pipelines/validators.py#L153) | **ERROR** | `validate_frontmatter` | — | `name` frontmatter `{…}` does not match folder name `{…}` |
| [158](pipelines/validators.py#L158) | **ERROR** | `validate_frontmatter` | — | `category` frontmatter `{…}` does not match parent domain folder `{…}` |
| [164](pipelines/validators.py#L164) | **ERROR** | `validate_frontmatter` | — | `description` must include a scope exclusion (e.g. 'NOT for ...') |
| [170](pipelines/validators.py#L170) | **ERROR** | `validate_frontmatter` | — | `{…}` contains an unfilled TODO marker; replace with real content |
| [174](pipelines/validators.py#L174) | **ERROR** | `validate_frontmatter` | — | `{…}` contains an unfilled TODO marker; replace with real content |
| [180](pipelines/validators.py#L180) | **ERROR** | `validate_frontmatter` | — | SKILL.md body has {…} words; minimum is {…} |
| [185](pipelines/validators.py#L185) | **ERROR** | `validate_frontmatter` | — | SKILL.md body contains {…} unfilled TODO marker(s); replace all TODOs with real content before syncing |
| [189](pipelines/validators.py#L189) | **ERROR** | `validate_frontmatter` | — | — |
| [214](pipelines/validators.py#L214) | _WARN_ | `_validate_checker_script_content` | Detect always-pass stubs in skill checker scripts. | checker script has only {…} meaningful lines — may be a stub; implement real validation logic |
| [230](pipelines/validators.py#L230) | _WARN_ | `_validate_checker_script_content` | Detect always-pass stubs in skill checker scripts. | checker script has no conditional branches (`if`); it will always produce the same output regardless of input |
| [236](pipelines/validators.py#L236) | _WARN_ | `_validate_checker_script_content` | Detect always-pass stubs in skill checker scripts. | checker script has no error-output path (sys.exit(1), raise, or ERROR/ISSUE/WARN print); it may never report problems |
| [249](pipelines/validators.py#L249) | **ERROR** | `validate_skill_structure` | — | missing required file `{…}` |
| [254](pipelines/validators.py#L254) | **ERROR** | `validate_skill_structure` | — | templates/ must contain at least one file |
| [256](pipelines/validators.py#L256) | **ERROR** | `validate_skill_structure` | — | scripts/ must contain at least one Python file |
| [265](pipelines/validators.py#L265) | **ERROR** | `validate_skill_structure` | — | missing `references/llm-anti-patterns.md` — add LLM-specific anti-patterns for this skill |
| [270](pipelines/validators.py#L270) | **ERROR** | `validate_skill_structure` | — | llm-anti-patterns.md contains {…} unfilled TODO marker(s) |
| [277](pipelines/validators.py#L277) | _WARN_ | `validate_skill_structure` | — | SKILL.md has no `## Recommended Workflow` section — add step-by-step agent instructions |
| [283](pipelines/validators.py#L283) | **ERROR** | `validate_skill_structure` | — | missing `## Official Sources Used` section |
| [289](pipelines/validators.py#L289) | **ERROR** | `validate_skill_structure` | — | `## Official Sources Used` section is empty; list at least one source |
| [337](pipelines/validators.py#L337) | **ERROR** | `validate_skill_authoring_style` | Style-level checks against `standards/skill-authoring-style.md`. | body has `{…}` section — frontmatter `description` is the canonical trigger surface; remove the body section or fold it into the descriptio… |
| [362](pipelines/validators.py#L362) | **ERROR** | `validate_skill_authoring_style` | Style-level checks against `standards/skill-authoring-style.md`. | body has `{…}` section while `references/well-architected.md` already covers it — keep pillar mapping in references/well-architected.md onl… |
| [407](pipelines/validators.py#L407) | **ERROR** | `validate_skill_authoring_style` | Style-level checks against `standards/skill-authoring-style.md`. | {…} paragraph(s) appear verbatim in both SKILL.md and references/gotchas.md (e.g. "{…}…") — keep the deep version in references/gotchas.md,… |
| [466](pipelines/validators.py#L466) | _WARN_ | `flush` | — | L{…}–L{…}: {…} consecutive `- **X** — ...` bullets should be a table (see standards/skill-authoring-style.md § 6.2) |
| [513](pipelines/validators.py#L513) | **ERROR** | `validate_skill_registry_record` | — | — |
| [520](pipelines/validators.py#L520) | **ERROR** | `validate_knowledge_source` | — | — |
| [601](pipelines/validators.py#L601) | _WARN_ | `validate_skill_similarity` | Flag near-duplicate skills as WARN. | near-duplicate of `{…}` (score {…}, description {…}, tags {…}, triggers {…}); review with `python3 scripts/audit_duplicates.py` or merge/re… |

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
| [94](scripts/validate_repo.py#L94) | **ERROR** | `_check_skill_local_script` | py_compile + ``--help`` smoke for a single skill-local helper script. | py_compile failed: {…} |
| [104](scripts/validate_repo.py#L104) | **ERROR** | `_check_skill_local_script` | py_compile + ``--help`` smoke for a single skill-local helper script. | --help exited non-zero |
| [128](scripts/validate_repo.py#L128) | **ERROR** | `validate_one_skill` | Validate a single skill's structure + frontmatter. Does NOT run the | unable to parse frontmatter: {…} |
| [287](scripts/validate_repo.py#L287) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | duplicate skill id `{…}` also seen in {…} |
| [296](scripts/validate_repo.py#L296) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | duplicate skill name `{…}` also seen in {…} |
| [336](scripts/validate_repo.py#L336) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | skill `{…}` has no query fixture — add at least one entry |
| [356](scripts/validate_repo.py#L356) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | query `{…}` did not return `{…}` in top {…} |
| [367](scripts/validate_repo.py#L367) | **ERROR** | `run_skill_validation` | Validate skills with optional partitioning. Returns (issues, count). | generated artifact is stale; run `python3 scripts/skill_sync.py --all` |
| [430](scripts/validate_repo.py#L430) | **ERROR** | `_check_orphan_skills` | Emit an ERROR for each filtered skill with no agent decision recorded. | skill `{…}` has no agent decision — wire it to a run-time agent via `python3 scripts/patch_agent_skill.py <agent_id> {…} "### Mandatory Rea… |
