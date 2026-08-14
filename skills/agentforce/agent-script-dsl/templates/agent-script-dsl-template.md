# Agent Script DSL — Work Template

Use this template when authoring, editing, or troubleshooting Agentforce agent metadata through the declarative Agent Script DSL.

## Scope

**Skill:** `agentforce/agent-script-dsl`

**Request summary:** (fill in what the user asked for — e.g., "author a new agent for X use case", "debug routing failure in Y agent", "set up CI pipeline agent tests")

---

## Context Gathered

Answer these before proceeding:

- **DX project `sourceApiVersion` in sfdx-project.json:** (this is what selects the metadata types, not the org's release — GenAiPlanner at 60.0–63.0, GenAiPlannerBundle at 64.0+ / Summer '25, AiAuthoringBundle at 65.0+ / Winter '26)
- **Target org release:** (record it, but note every supported org already clears both floors)
- **Authored in the new Agentforce Builder (Agent Script)?** Yes / No — if Yes, `AiAuthoringBundle` is mandatory in the manifest
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
| GenAiPlannerBundle (v64.0+) or GenAiPlanner (v60.0–63.0) | | |
| GenAiPlugin | | (one row per topic/subagent — the type name never renamed) |
| GenAiFunction | | (one row per action, if editing action definitions) |
| AiAuthoringBundle (v65.0+) | | `aiAuthoringBundles/<Name>/<Name>.agent` + `<Name>.bundle-meta.xml` — required for Builder-authored agents |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Pattern 1: Source-Control-First Agent Development** — building a new agent
- [ ] **Pattern 2: Retrieve-Before-Edit** — syncing org state back to source control
- [ ] **Pattern 3: Debugging Routing Failures** — investigating LLM topic misrouting

---

## Authoring Checklist

- [ ] API version confirmed in `sfdx-project.json` (64.0+ for GenAiPlannerBundle; 65.0+ if any AiAuthoringBundle is in scope)
- [ ] `.agent` Agent Script source is in the repo, not just the compiled GenAiPlugin/GenAiPlannerBundle output
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

- (e.g., "Using GenAiPlanner instead of GenAiPlannerBundle because the project is still pinned to sourceApiVersion 63.0 — upgrade to 64.0 is scheduled for release N")
- (e.g., "Topic X and Topic Y have intentionally overlapping scope — documented in SKILL.md gotchas")
