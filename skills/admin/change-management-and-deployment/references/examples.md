# Examples: Change Management and Deployment

---

## Example: Small Admin Hotfix

**Scenario:** A validation rule typo is blocking Case creation in production. The admin team has connected sandboxes but no source-driven release process yet.

**Decision:** Use a tightly scoped Change Set for the hotfix, document the change, and update source afterward.

**Why this is acceptable:** The release is small, urgent, and low in dependency complexity.

**What would be wrong:** treating that success as proof that weekly multi-feature releases should stay on Change Sets forever.

---

## Example: Moving from Change Sets to DevOps Center

**Scenario:** An admin team deploys page layouts, fields, flows, and permission sets every sprint. Releases are manual and regression-prone.

**Decision:** Move to DevOps Center with source-tracked Developer sandboxes and a simple Sandbox -> Production promotion path.

**Why:** The team needs Git-backed promotion discipline and review, but not a fully custom CI/CD program on day one.

---

## Example: Metadata Release Coupled to Data Cutover

**Scenario:** A release adds new Opportunity stages, validation rules, and a bulk update to open Opportunities.

**Release handling:**
1. deploy metadata to lower environments
2. rehearse data load and reconciliation
3. define production sequence explicitly
4. keep data rollback separate from metadata rollback

**Lesson:** one release window can contain both metadata and data, but they must not share one vague rollback sentence.
