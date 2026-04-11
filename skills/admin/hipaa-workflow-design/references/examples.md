# Examples — HIPAA Workflow Design

## Example 1: Identifying That Standard Field History Tracking Fails HIPAA Audit Requirements

**Context:** A Health Cloud implementation team is designing the audit trail architecture for a regional health system. The compliance officer asks whether the built-in Field History Tracking is sufficient for HIPAA audit log requirements.

**Problem:** The team was planning to enable Field History Tracking on 15 PHI fields per object — the standard Salesforce maximum — without realizing that standard Field History Tracking retains data for only 18 months.

**Solution:**
1. Review HIPAA Security Rule §164.312(b): Audit Controls require retention of activity logs for 6 years from date of creation or last effective date.
2. Compare standard Field History Tracking (18-month retention, max 20 fields/object) vs. Shield Field Audit Trail (up to 10-year retention, broader field coverage, required Shield license).
3. Confirm that Shield Field Audit Trail satisfies HIPAA's 6-year requirement; standard Field History Tracking does not.
4. Document the requirement for Shield Field Audit Trail in the HIPAA controls specification.
5. Identify all PHI fields that need Field Audit Trail coverage (not just a subset).
6. Add the Shield Field Audit Trail license requirement to the project's license procurement checklist.

**Why it works:** Correctly identifying the retention gap between standard Field History Tracking (18 months) and HIPAA requirements (6 years) prevents a compliance failure that would only be discovered during an audit — at which point remediation may be impossible due to lost data.

---

## Example 2: Designing Minimum Necessary Access for a Multi-Role Health Cloud Org

**Context:** A large integrated health system is implementing Health Cloud with five distinct user roles: primary care physicians, specialists, care coordinators, front desk administrative staff, and billing specialists. Each role needs different levels of PHI access.

**Problem:** The initial design used a single "Health Cloud User" permission set for all clinical staff and a separate "Admin User" permission set for administrative staff, giving all clinical staff access to all PHI fields including detailed clinical notes, diagnoses, and medication histories.

**Solution:**
1. Define minimum necessary access per role:
   - Primary care physicians: full clinical record access for their own patients only
   - Specialists: clinical record access for referred patients only (for the referral episode)
   - Care coordinators: care plan, referral, and care program fields; limited clinical diagnosis access
   - Front desk staff: demographic PHI (name, DOB, contact info, insurance); no clinical PHI
   - Billing specialists: billing codes, insurance IDs, claim data; no clinical notes or diagnosis codes
2. Set OWD = Private for Account and all clinical objects.
3. Configure care team role-based sharing for physicians and specialists.
4. Create role-specific permission sets with field-level security restricting access to clinical PHI fields for non-clinical roles.
5. Document the access matrix as part of the HIPAA compliance record.

**Why it works:** The HIPAA minimum necessary standard (§164.514(d)) requires that PHI access be limited to the minimum necessary to accomplish the intended purpose. OWD-Private plus role-specific permission sets implements this at the Salesforce platform level.

---

## Anti-Pattern: Signing the BAA After PHI Is Already Stored

**What practitioners do:** Proceed with Health Cloud configuration, test data setup, and pilot go-live before the Salesforce BAA is fully executed, assuming the BAA can be signed retroactively.

**What goes wrong:** Any PHI stored in Salesforce before the BAA is executed constitutes a potential HIPAA violation. The BAA is a legal agreement that establishes Salesforce as a Business Associate with responsibilities for protecting PHI. There is no retroactive coverage — PHI stored before the BAA was signed may require breach notification analysis.

**Correct approach:** The BAA must be executed before any real PHI (including test records containing actual patient data) is loaded into any Salesforce environment, including sandboxes. Use only fully synthetic test data until the BAA is signed.
