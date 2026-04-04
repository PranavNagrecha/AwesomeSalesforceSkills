# Source Tracking and Conflict Resolution — Work Template

Use this template when diagnosing or resolving a source tracking conflict for a Salesforce DX project.

---

## Scope

**Skill:** `source-tracking-and-conflict-resolution`

**Request summary:** (fill in what the user asked for — e.g., "resolve conflict on retrieve from QA sandbox" or "enable source tracking in a new Full sandbox")

---

## Context Gathered

Answer these before proceeding:

- **Org type:** [ ] Scratch org  [ ] Developer sandbox  [ ] Partial Copy sandbox  [ ] Full sandbox  [ ] Production
- **Source tracking enabled?:** [ ] Yes  [ ] No  [ ] Unknown — need to check
- **Error message or `sf project deploy start --dry-run` output:** (paste here)
- **Which version is authoritative?:** [ ] Org version (admin made changes in Setup)  [ ] Local version (developer made the correct fix locally)  [ ] Both need manual merge
- **Sandbox recently refreshed?:** [ ] Yes (org ID may have changed)  [ ] No

---

## Conflict Resolution Mode

Select the applicable resolution mode from SKILL.md:

- [ ] **Mode 1 — Org wins:** `sf project retrieve start --ignore-conflicts`
- [ ] **Mode 2 — Local wins:** `sf project deploy start --ignore-conflicts`
- [ ] **Mode 3 — Manual merge:** Retrieve with `--ignore-conflicts`, merge manually, deploy
- [ ] **Recovery — Corrupted tracking:** Delete `.sf/orgs/<orgId>/`, run full retrieve

---

## Commands to Execute

```bash
# Step 1: Preview (always run first)
sf project deploy start --dry-run --target-org <alias>

# Step 2: If sandbox tracking needs enabling, instruct the user to:
# Setup > Sandboxes > Sandbox Settings > Enable Source Tracking in Sandboxes
# Then refresh the sandbox.

# Step 3: Resolution command (fill in based on mode above)
# Mode 1:
sf project retrieve start --ignore-conflicts --target-org <alias>

# Mode 2:
sf project deploy start --ignore-conflicts --target-org <alias>

# Recovery (corrupted tracking):
rm -rf .sf/orgs/<orgId>/
sf project retrieve start --target-org <alias>

# Step 4: Confirm clean state
sf project deploy start --dry-run --target-org <alias>
```

---

## Checklist

- [ ] `sf project deploy start --dry-run` shows zero conflicts before resolution
- [ ] Local changes stashed or committed to Git before running `--ignore-conflicts` on retrieve
- [ ] Sandbox source-tracking preference confirmed enabled (if applicable)
- [ ] No manual edits made to `.sf/orgs/<orgId>/maxRevision.json`
- [ ] If sandbox was refreshed: old tracking directory deleted, fresh retrieve completed
- [ ] `.sf/` is in `.gitignore` — tracking files not committed to Git
- [ ] Post-resolution dry-run confirms clean state

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, and why a specific resolution mode was chosen.)
