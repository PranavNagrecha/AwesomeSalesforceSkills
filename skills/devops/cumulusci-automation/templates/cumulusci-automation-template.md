# CumulusCI Automation — Work Template

Use this template when authoring or debugging CumulusCI task/flow configuration, Robot Framework integration, or CI pipeline automation for a Salesforce project.

---

## Scope

**Skill:** `cumulusci-automation`

**Request summary:** (fill in what the user asked for — e.g., "Add a custom configuration step to dev_org", "Wire Robot tests into CI", "Authenticate CI pipeline with JWT")

---

## Context Gathered

Answer these before writing any cumulusci.yml:

- **CumulusCI version** (`cci version`): _______________
- **Project type** (`project.package.type` in cumulusci.yml): [ ] managed  [ ] unlocked  [ ] unpackaged
- **Target org type**: [ ] scratch org  [ ] sandbox  [ ] production
- **CI platform**: [ ] GitHub Actions  [ ] CircleCI  [ ] Jenkins  [ ] Bitbucket Pipelines  [ ] other: ___
- **Authentication method available**: [ ] JWT (Connected App + certificate)  [ ] SFDX auth URL (local dev only)  [ ] interactive (local dev only)
- **What is being configured**: [ ] new task  [ ] extend existing flow  [ ] new flow  [ ] Robot Framework  [ ] cross-project sources

---

## Flow/Task Being Extended or Created

Run this before writing anything:

```bash
# If extending an existing flow, always check the current step list first:
cci flow info <flow-name>

# If configuring a task, check available options:
cci task info <task-name>
```

**Existing step numbers in the target flow** (copy from `cci flow info` output):

| Step # | Task | Notes |
|--------|------|-------|
| (fill in) | | |

**New step numbers planned** (must not collide with existing):

| New Step # | Task | Purpose |
|------------|------|---------|
| (fill in) | | |

---

## cumulusci.yml Changes

### Task declarations (if new tasks are needed)

```yaml
tasks:
  task_name_here:
    description: One-line description of what this task does
    class_path: cumulusci.tasks.REPLACE_WITH_FULL_CLASS_PATH
    options:
      option_key: option_value
```

### Flow declarations (extension or new flow)

```yaml
flows:
  flow_name_here:
    description: What this flow does
    steps:
      STEP_NUMBER:
        task: task_name_here
        options:
          # step-level option overrides (optional)
        when: "OPTIONAL_PYTHON_EXPRESSION"  # omit if always-run
```

---

## CI Pipeline Changes

```yaml
# Add to your CI workflow YAML (GitHub Actions example)
- name: Authenticate Dev Hub via JWT
  run: |
    printf '%s' "${{ secrets.DEVHUB_JWT_KEY }}" > /tmp/server.key
    chmod 600 /tmp/server.key
    sf org login jwt \
      --client-id "${{ secrets.DEVHUB_CLIENT_ID }}" \
      --jwt-key-file /tmp/server.key \
      --username "${{ secrets.DEVHUB_USERNAME }}" \
      --alias DevHub \
      --set-default-dev-hub
    rm /tmp/server.key

- name: Run CumulusCI flow
  run: cci flow run FLOW_NAME_HERE --org ORG_ALIAS_HERE
```

---

## Validation Checklist

Before marking work complete:

- [ ] `cci flow info <flow-name>` shows the correct merged step order (no collisions)
- [ ] `cci task info <task-name>` resolves without error for every new task
- [ ] All `class_path` values are fully qualified Python dotted paths (contain at least one `.`)
- [ ] No `options:` block placed at the flow level — options are nested inside step declarations
- [ ] Cross-project `sources:` entries are pinned to a specific `tag:` (not `release: latest`)
- [ ] CI pipeline uses JWT auth; no SFDX auth URLs or interactive auth commands present
- [ ] `when:` expressions tested locally with `cci flow run --debug`; no silent skips
- [ ] Robot Framework `suites:` path exists in the repository
- [ ] Checker script passes: `python3 skills/devops/cumulusci-automation/scripts/check_cumulusci_automation.py --project-dir .`

---

## Notes

Record any deviations from the standard pattern and the reason:

- Deviation: _______________ Reason: _______________
