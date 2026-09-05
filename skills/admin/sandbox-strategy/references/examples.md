# Examples: Sandbox Strategy

---

## Example: Small Admin Team

**Scenario:** Two admins manage Sales Cloud and basic automation. They need a safe place to build and one place for stakeholder testing.

**Recommended setup:**
- `Developer Sandbox` per admin for build work
- `Full Sandbox` or `Partial Copy` for UAT, depending on data realism needs

**Why this works:** It keeps daily config work isolated while preserving one controlled validation environment.

**The allocation check that decides it.** On Enterprise Edition this team owns no Full sandbox by default, so the UAT row is a Partial Copy unless someone has already bought a Full licence. Write the answer down before designing:

```
Setup > Sandboxes > Sandbox Licenses          Owned   Used   Free
  Developer                                      25      2     23
  Developer Pro                                   0      0      0   <- add-on, not owned
  Partial Copy                                    1      0      1
  Full                                            0      0      0   <- add-on, not owned

Decision: UAT = Partial Copy (the only production-data licence owned).
Consequence: a Sandbox Template must exist before the Create action appears.
Template owner: <name>.  Objects selected: Account, Contact, Opportunity, Case.
```

---

## Example: DevOps Center Rollout

**Scenario:** A team is moving from change sets to DevOps Center and wants to use its existing Partial Copy sandbox for source-tracked work.

**Recommendation:** Use `Developer Sandboxes` for source-tracked development and keep `Partial Copy` for integration and QA.

**Why:** DevOps Center patterns work best when development happens in source-tracked Developer sandboxes, while Partial Copy supports realistic testing.

---

## Example: Regulated Program

**Scenario:** A public-sector implementation needs realistic UAT data, but copied citizen data cannot remain unmasked in non-production.

**Recommendation:**
- use `Full Sandbox` only where parity is justified
- automate masking immediately after refresh
- document post-refresh compliance checks and access review

**Why:** The environment strategy is part of the compliance story, not just a delivery convenience.

**The ladder, written as a reviewable record.** Auditors ask what the control was, not what the intention was, so the ladder is checked in beside the code:

```yaml
# config/environment-ladder.yaml — reviewed each release, cited in the control evidence pack
environments:
  - name: DEV-*
    type: Developer
    production_data: false
    post_copy_class: null          # no copied records, nothing to scrub
    refresh_approval: self-service
  - name: SIT
    type: Developer Pro
    production_data: false
    seeded_from: config/seed-data/  # synthetic citizens only
    post_copy_class: PrepareSandbox
    refresh_approval: release-manager
  - name: UAT
    type: Full
    production_data: true
    justification: >-
      Parity required for the annual benefits-calculation rehearsal; no lower
      type reproduces the volume the calculation is certified against.
    post_copy_class: PrepareSandbox   # mandatory: this row copies real citizen data
    refresh_approval: [release-manager, data-protection-officer]
    access_review: within 2 business days of activation
```

**The check that proves the control ran**, in the refreshed environment, before anyone is granted access:

```sql
SELECT COUNT() FROM Lead WHERE Email != null AND (NOT Email LIKE '%.invalid')
```

A non-zero result means the post-copy scrub did not finish, regardless of what the copy status says — and the environment stays closed until it is zero. Every row above with `production_data: true` and a null `post_copy_class` is a finding, not a configuration.
