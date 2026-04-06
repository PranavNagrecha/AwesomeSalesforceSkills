# Scratch Org Pools — Work Template

Use this template when setting up or troubleshooting scratch org pools for CI.

## Scope

**Skill:** `scratch-org-pools`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Dev Hub edition:** (Developer / Enterprise / Performance / Unlimited / Partner Business Org)
- **Active org limit:** (e.g., 20 for Enterprise)
- **Daily creation limit:** (e.g., 40 for Enterprise)
- **Current active org count:** (result of `SELECT COUNT(Id) FROM ActiveScratchOrg`)
- **Peak parallel CI jobs:** (number of concurrent jobs expected)
- **CumulusCI installed:** (yes / no)
- **CI platform:** (GitHub Actions / Jenkins / Bitbucket Pipelines / other)

## Pool Sizing Calculation

| Factor | Value |
|---|---|
| Peak parallel jobs | ___ |
| Buffer (30%) | ___ |
| Target pool size | ___ |
| Available active slots (limit - current usage) | ___ |
| Available daily creates (limit - current usage) | ___ |
| Pool feasible? | yes / no |

## Approach

Which pattern from SKILL.md applies and why?

- [ ] Pattern 1: Basic Pool Setup
- [ ] Pattern 2: Scheduled Replenishment
- [ ] Pattern 3: CI Job with Pool Fallback

## Replenishment Schedule

| Parameter | Value |
|---|---|
| Frequency | (e.g., daily at 4 AM UTC) |
| Target pool size | ___ |
| Org duration (days) | ___ |
| Weekend handling | (skip / extend duration / extra Friday replenishment) |

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Dev Hub edition supports the planned pool size
- [ ] Pool size accounts for peak concurrency plus 30% buffer
- [ ] CumulusCI is installed and cumulusci.yml has correct org definitions
- [ ] Replenishment schedule runs during off-peak hours
- [ ] CI jobs include fallback logic for empty pools
- [ ] CI jobs delete orgs after use
- [ ] `cci org pool prune` runs before each replenishment
- [ ] Team members know not to manually create orgs that consume pool allocation

## Notes

Record any deviations from the standard pattern and why.
