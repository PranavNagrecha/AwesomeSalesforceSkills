# Org Shape and Scratch Definition -- Work Template

Use this template when authoring or debugging a scratch org definition file.

## Scope

**Skill:** `org-shape-and-scratch-definition`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Dev Hub edition:** (Developer / Enterprise / Performance / Unlimited / Partner)
- **Org Shape available?** (Yes if Dev Hub is Enterprise+ and source org is connected)
- **Source org ID (if using Org Shape):**
- **Required features beyond base edition:**
- **Required settings (Translation Workbench, Chatter, etc.):**
- **Release pinning needed?** (Yes for CI stability / No for development)
- **Any legacy orgPreferences to migrate?** (Yes / No)

## Sourcing Strategy

Choose one:
- [ ] **Org Shape** -- sourceOrg with explicit overrides for excluded features
- [ ] **Manual declaration** -- edition + features + settings, no sourceOrg dependency

**Rationale:** (explain why this strategy was chosen)

## Definition File Draft

```json
{
  "orgName": "",
  "edition": "",
  "features": [],
  "settings": {},
  "release": ""
}
```

## Validation Checklist

- [ ] JSON syntax is valid
- [ ] Edition is appropriate for declared features
- [ ] No deprecated `orgPreferences` block present
- [ ] If using Org Shape, `edition` is not set alongside `sourceOrg`
- [ ] If using Org Shape, excluded features (MultiCurrency, PersonAccounts) are declared explicitly where needed
- [ ] Feature names match official documentation exactly (case-sensitive)
- [ ] Settings keys use correct Metadata API type names
- [ ] `release` field is set intentionally (or omission is deliberate)
- [ ] Scratch org creation succeeds with this definition file
- [ ] Target features verified in the running scratch org

## Verification Commands

```bash
# Create scratch org with the definition file
sf org create scratch --definition-file config/project-scratch-def.json --target-dev-hub <HubOrg> --alias <alias> --duration-days 7

# Verify org details
sf org display --target-org <alias>

# Check specific feature availability (open org and inspect Setup)
sf org open --target-org <alias>
```

## Notes

(Record any deviations from the standard pattern and why.)
