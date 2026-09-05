# Sandbox Strategy Template

Use this to define environment purpose, cadence, and refresh controls.

Replace every `<angle-bracket>` placeholder. The example rows are a worked mid-size
delivery team — keep the ones that fit, delete the ones that don't, and justify every row
you add. A row you cannot fill in completely is a row whose environment has no owner.

Lint the finished document with:

```bash
python3 ../scripts/check_sandbox_plan.py sandbox-strategy.md
```

---

## Environment Inventory

Every environment gets a type justified by its purpose, and an owner who is a person.

| Environment | Type | Purpose | Owner | Users |
|-------------|------|---------|-------|-------|
| DEV-`<initials>` | Developer | Individual build work, source-tracked, one per builder | the builder | 1 |
| SIT | Developer Pro | Shared integration branch; synthetic seed data, no production records | release manager | 6–10 |
| QA | Partial Copy | Regression against a sampled production dataset | QA lead | 4–8 |
| UAT | Full | Business validation and production rehearsal | release manager | 15–40 |
| TRAIN | Developer Pro | Training and enablement; curated demo data | enablement lead | varies per cohort |

Justify any deviation here:

- Second Full sandbox: `<why a Partial Copy or a clone of UAT does not serve this need>`
- Any environment with no named owner: `<remove it, or name the owner>`
- Any environment not in the release path below: `<what it is for, and when it is retired>`

## Refresh Cadence

Cadence must respect the platform refresh floor for the type (Developer and Developer Pro:
1 day; Partial Copy: 5 days; Full: 29 days — see SKILL.md, "Type Capacities and Refresh
Windows"). A cadence shorter than the floor is not a plan.

| Environment | Floor | Cadence | Approval Needed | Planned Window |
|-------------|-------|---------|-----------------|----------------|
| DEV-`<initials>` | 1 day | On demand | No | any time; builder's own risk |
| SIT | 1 day | First Monday of each sprint | No | `<day/time, off-hours>` |
| QA | 5 days | Sprint open | Yes — QA lead | `<day/time, off-hours>` |
| UAT | 29 days | Release week −4 | Yes — release manager | `<day/time, off-hours>` |
| TRAIN | 1 day | Per training cohort | Yes — enablement lead | `<day/time, off-hours>` |

Concurrent refresh requests are processed in series, one at a time. If two rows above land in
the same window, record which one runs first: `<environment>`, then `<environment>`.

## Masking and Data Policy

Only Partial Copy and Full sandboxes copy production records. Every row that answers "Yes" to
production data present needs a post-copy class, not a note.

| Environment | Production Data Present | Masking Required | Seeding Needed | Post-Copy Class | Notes |
|-------------|-------------------------|------------------|----------------|-----------------|-------|
| DEV-`<initials>` | No | No | Yes — synthetic | `PrepareSandbox` | metadata only; class still resets endpoints |
| SIT | No | No | Yes — `<seed source>` | `PrepareSandbox` | integration stubs, never live endpoints |
| QA | Yes | Yes | Partial — `<reference data>` | `PrepareSandbox` | template objects: `<Account, Contact, …>` |
| UAT | Yes | Yes | No | `PrepareSandbox` | full production copy incl. PII; access review required |
| TRAIN | No | No | Yes — curated demo | `PrepareSandbox` | demo data must not resemble real customers |

Sandbox template owner (required before a Partial Copy can be created): `<name>`
Objects selected by the template: `<list>`
Data classification of the copied objects: `<classification, and who signed it off>`

## Post-Refresh Tasks

Runs to completion before the environment is handed back. A copy that finished is not a
refresh that finished.

- [ ] Confirm the post-copy class completed — verify by data, not by copy status
- [ ] Verify email deliverability level in Setup → Deliverability (cannot be set from Apex)
- [ ] Reset integration endpoints and Named Credentials to non-production targets
- [ ] Verify user access and test accounts (usernames carry the sandbox-name suffix)
- [ ] Re-enable or reconfigure scheduled jobs; disable any that would reach a live system
- [ ] Re-seed test data
- [ ] Validate masking completion on every object the template selected
- [ ] Run the access review for any environment holding production records
- [ ] Notify teams that the environment is ready

Owner of this runbook: `<name>`
Where it is executed from: `<runbook location or automation job>`

## Release Path

1. Build in: DEV-`<initials>` (source-tracked, one branch per builder)
2. Integrate/test in: SIT, then QA for regression
3. Validate with business in: UAT
4. Promote to production using: `<sf project deploy start with an explicit --test-level, DevOps Center, or the named CI pipeline>`

Deploys into non-production run no tests unless a test level is set explicitly — record the
level used at each hop so the sandbox rehearsal matches the production deploy:

| Hop | Test level used |
|---|---|
| DEV → SIT | `<e.g. NoTestRun>` |
| SIT → QA | `<e.g. RunLocalTests>` |
| QA → UAT | `RunLocalTests` |
| UAT → Production | `RunLocalTests` |

## Deviations Register

Anything above that breaks a rule, with the reason and the person who accepted it.

| Deviation | Reason | Accepted by | Review date |
|---|---|---|---|
| `<e.g. two Full sandboxes>` | `<why no cheaper type serves it>` | `<name>` | `<date>` |
