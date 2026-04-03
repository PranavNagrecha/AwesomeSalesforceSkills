# Examples: Sandbox Strategy

---

## Example: Small Admin Team

**Scenario:** Two admins manage Sales Cloud and basic automation. They need a safe place to build and one place for stakeholder testing.

**Recommended setup:**
- `Developer Sandbox` per admin for build work
- `Full Sandbox` or `Partial Copy` for UAT, depending on data realism needs

**Why this works:** It keeps daily config work isolated while preserving one controlled validation environment.

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
