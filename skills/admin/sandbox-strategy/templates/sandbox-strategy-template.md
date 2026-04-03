# Sandbox Strategy Template

Use this to define environment purpose, cadence, and refresh controls.

---

## Environment Inventory

| Environment | Type | Purpose | Owner | Users |
|-------------|------|---------|-------|-------|
| DEV-1 | Developer / Developer Pro / Partial Copy / Full | TODO | TODO | TODO |
| QA | Developer / Developer Pro / Partial Copy / Full | TODO | TODO | TODO |
| UAT | Developer / Developer Pro / Partial Copy / Full | TODO | TODO | TODO |

## Refresh Cadence

| Environment | Cadence | Approval Needed | Planned Window |
|-------------|---------|-----------------|----------------|
| DEV-1 | TODO | Yes / No | TODO |
| QA | TODO | Yes / No | TODO |
| UAT | TODO | Yes / No | TODO |

## Masking and Data Policy

| Environment | Production Data Present | Masking Required | Seeding Needed | Notes |
|-------------|-------------------------|------------------|----------------|------|
| DEV-1 | Yes / No | Yes / No | Yes / No | TODO |
| QA | Yes / No | Yes / No | Yes / No | TODO |
| UAT | Yes / No | Yes / No | Yes / No | TODO |

## Post-Refresh Tasks

- [ ] Reset integration endpoints and Named Credentials as needed
- [ ] Verify user access and test accounts
- [ ] Re-enable or reconfigure scheduled jobs if appropriate
- [ ] Re-seed test data
- [ ] Validate masking completion
- [ ] Notify teams that the environment is ready

## Release Path

1. Build in: TODO
2. Integrate/test in: TODO
3. Validate with business in: TODO
4. Promote to production using: TODO
