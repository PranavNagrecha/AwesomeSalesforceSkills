# Scratch Org Management — Work Template

Use this template when the user needs help with scratch org definition, lifecycle, allocation limits, or CI automation.

---

## Scope

**Skill:** `scratch-org-management`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before proceeding:

- **Dev Hub edition:** [ Developer | Enterprise | Performance | Unlimited | Partner ]
- **Daily limit / active limit:** (e.g., 6 / 3 for Developer Edition)
- **Target scratch org edition:** [ Developer | Enterprise | Group | Professional | Partner Developer | Partner Enterprise ]
- **Required features:** (list features the org must have; e.g., Communities, LightningServiceConsole)
- **Desired duration:** _____ days (max 30; CI default 1, developer default 7)
- **CI platform:** (GitHub Actions / Jenkins / other, or N/A for local dev)
- **Using Org Shape?** [ Yes — source org alias: _____ | No ]

---

## Definition File

```json
{
  "edition": "FILL_IN",
  "description": "FILL_IN",
  "duration": 7,
  "hasSampleData": false,
  "language": "en_US",
  "country": "US",
  "features": [
    "FEATURE_1",
    "FEATURE_2"
  ],
  "settings": {
    "SETTING_OBJECT": {
      "SETTING_KEY": true
    }
  }
}
```

Save as `config/project-scratch-def.json` and commit to source control.

---

## Create Command

```bash
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --alias ALIAS \
  --duration-days DURATION \
  --set-default \
  --target-dev-hub DEV_HUB_ALIAS
```

---

## CI Pipeline Snippet (if applicable)

```yaml
- name: Create scratch org
  run: sf org create scratch \
       --definition-file config/project-scratch-def.json \
       --alias ci-org-${{ github.run_id }} \
       --duration-days 1 \
       --target-dev-hub DevHub

- name: Deploy and test
  run: |
    sf project deploy start --target-org ci-org-${{ github.run_id }}
    sf apex run test --target-org ci-org-${{ github.run_id }} --result-format tap --code-coverage

- name: Delete scratch org
  if: always()
  run: sf org delete scratch --target-org ci-org-${{ github.run_id }} --no-prompt
```

---

## Allocation Audit (run in Dev Hub if limit errors occur)

```bash
# Check active orgs
sf data query \
  --target-org DEV_HUB_ALIAS \
  --query "SELECT OrgName, ExpirationDate, CreatedBy.Name FROM ActiveScratchOrg ORDER BY ExpirationDate ASC"

# Check orgs expiring within 2 days
sf data query \
  --target-org DEV_HUB_ALIAS \
  --query "SELECT OrgName, ExpirationDate, CreatedBy.Name FROM ActiveScratchOrg WHERE ExpirationDate <= NEXT_N_DAYS:2"

# Delete a specific stale org
sf org delete scratch --target-org STALE_ALIAS --no-prompt
```

---

## Review Checklist

- [ ] `edition` matches production or target deployment environment
- [ ] All required `features` declared in definition file
- [ ] `duration` set appropriately (1 day CI, ≤14 days developer work)
- [ ] CI pipeline has unconditional delete step (`if: always()`)
- [ ] Dev Hub edition supports required active org count (Developer Edition max 3)
- [ ] `hasSampleData: false` unless sample data is explicitly needed
- [ ] Definition file committed to `config/` in source control
- [ ] `settings` used (not deprecated `orgPreferences`)

---

## Notes

(Record deviations from the standard pattern and their reasons here.)
