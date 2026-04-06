# Agent Script DSL — Work Template

Use this template when authoring, editing, or troubleshooting Agentforce agent metadata through the declarative Agent Script DSL.

## Scope

**Skill:** `agentforce/agent-script-dsl`

**Request summary:** (fill in what the user asked for — e.g., "author a new agent for X use case", "debug routing failure in Y agent", "set up CI pipeline agent tests")

---

## Context Gathered

Answer these before proceeding:

- **Target org API version:** (e.g., 64.0 for Spring '26 — determines GenAiPlannerBundle vs GenAiPlanner)
- **DX project `apiVersion` in sfdx-project.json:** (must match or exceed target org release)
- **VS Code + Agentforce extension installed:** Yes / No
- **Agent already exists in source control:** Yes / No — if Yes, retrieve before editing
- **Agent already exists in org:** Yes / No — if Yes, retrieve before editing
- **CI pipeline tool:** (GitHub Actions / Bitbucket / Jenkins / other)

---

## Metadata Bundle Members

List all metadata types that must be deployed together for this agent:

| Metadata Type | API Name | File Path |
|---|---|---|
| Bot | | |
| BotVersion | | |
| GenAiPlannerBundle (v64+) or GenAiPlanner (v60–v63) | | |
| GenAiPlugin | | (one row per topic) |
| GenAiFunction | | (one row per action, if editing action definitions) |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Pattern 1: Source-Control-First Agent Development** — building a new agent
- [ ] **Pattern 2: Retrieve-Before-Edit** — syncing org state back to source control
- [ ] **Pattern 3: Debugging Routing Failures** — investigating LLM topic misrouting

---

## Authoring Checklist

- [ ] API version confirmed in `sfdx-project.json` (64.0+ for GenAiPlannerBundle)
- [ ] Latest agent state retrieved from target org before making changes
- [ ] `.agent` file opened in VS Code with Agentforce extension — zero LSP diagnostics
- [ ] Topic descriptions reviewed: specific, non-overlapping, at least 1 sentence per topic
- [ ] `spec.plannerInstructions` contains specific persona, constraints, and fallback behavior
- [ ] Agent API name finalized — confirm it will not need to change (immutable after first deploy)
- [ ] Full metadata bundle listed in deploy command or `package.xml` manifest
- [ ] Full metadata bundle deployed atomically (not piece-by-piece)
- [ ] Agent activated manually in target org after deploy
- [ ] `sf agent test run` passes with exit code 0
- [ ] All metadata files committed to version control before promoting to next environment
- [ ] Activation step documented in deployment runbook for each environment

---

## Deploy Commands

```bash
# Option A: explicit metadata list
sf project deploy start \
  --metadata Bot:<AgentApiName> \
  --metadata "BotVersion:<AgentApiName>.v1" \
  --metadata "GenAiPlannerBundle:<AgentApiName>" \
  --metadata "GenAiPlugin:<AgentApiName>_<TopicName>" \
  --target-org <OrgAlias> \
  --wait 10

# Option B: manifest-based (recommended for CI)
sf project deploy start \
  --manifest manifest/agent-bundle.xml \
  --target-org <OrgAlias> \
  --wait 10
```

---

## Test Commands

```bash
sf agent test run \
  --spec force-app/main/default/aiTests/<TestFileName>.aiTest-meta.xml \
  --target-org <OrgAlias> \
  --wait 10
# Exit code 0 = all assertions passed
# Exit code 1 = failure or timeout
```

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Using GenAiPlanner instead of GenAiPlannerBundle because production org is on Winter '26 / API v63")
- (e.g., "Topic X and Topic Y have intentionally overlapping scope — documented in SKILL.md gotchas")
