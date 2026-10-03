# Examples — HIPAA Workflow Design

## Example 1: Identifying That Standard Field History Tracking Fails HIPAA Audit Requirements

**Context:** A Health Cloud implementation team is designing the audit trail architecture for a regional health system. The compliance officer asks whether the built-in Field History Tracking is sufficient for HIPAA audit log requirements.

**Problem:** The team planned to enable field history tracking on 15 PHI fields per object without realizing that, without Field Audit Trail, history is kept for only 18 months (24 months through the API). An earlier version of this example called 15 the standard maximum; the Security Guide gives 20 fields per object without Field Audit Trail and 200 with it.

**Solution:**
1. Confirm the retention requirement with counsel. UNVERIFIED (2026-10-03): earlier versions of this example cited HIPAA §164.312(b) for a 6-year log retention rule; the 6-year wording belongs to the documentation retention rule in 45 CFR 164.316(b)(2), and the regulation text did not fetch.
2. Compare standard field history tracking (18 months, 24 via API, up to 20 fields per object) with Field Audit Trail (archived history kept until you delete it, up to 200 fields per object, Shield licence). An earlier version of this example said "up to 10-year retention"; the Summer '26 Security Guide says archived data is kept until deleted.
3. Confirm that Field Audit Trail, with a documented deletion procedure, meets the agreed retention period; standard field history (18 months) does not meet any period longer than that.
4. Document the requirement for Shield Field Audit Trail in the HIPAA controls specification.
5. Identify all PHI fields that need Field Audit Trail coverage (not just a subset).
6. Add the Shield Field Audit Trail license requirement to the project's license procurement checklist.

**Why it works:** Correctly identifying the retention gap between standard field history (18 months) and the agreed retention period (6 years in this program; UNVERIFIED (2026-10-03) as a HIPAA requirement) prevents a compliance failure that would only be discovered during an audit — at which point remediation may be impossible due to lost data.

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

**Why it works:** The HIPAA minimum necessary standard (cited as §164.514(d); UNVERIFIED (2026-10-03): regulation text did not fetch) requires that PHI access be limited to the minimum necessary to accomplish the intended purpose. OWD-Private plus role-specific permission sets implements this at the Salesforce platform level.

---

## Anti-Pattern: Signing the BAA After PHI Is Already Stored

**What practitioners do:** Proceed with Health Cloud configuration, test data setup, and pilot go-live before the Salesforce BAA is fully executed, assuming the BAA can be signed retroactively.

**What goes wrong:** Any PHI stored in Salesforce before the BAA is executed constitutes a potential HIPAA violation. The BAA is a legal agreement that establishes Salesforce as a Business Associate with responsibilities for protecting PHI. There is no retroactive coverage — PHI stored before the BAA was signed may require breach notification analysis.

**Correct approach:** The BAA must be executed before any real PHI (including test records containing actual patient data) is loaded into any Salesforce environment, including sandboxes. Use only fully synthetic test data until the BAA is signed.

---

## Example 3: Proving the PHI Inventory From Metadata

**Context:** An internal auditor asks for the list of PHI fields on the intake object and how each is protected.

**Problem:** The PHI inventory spreadsheet was last updated two releases ago.

**Solution:** Because every PHI field is tagged in its definition (see `metadata-examples.md`), the inventory is a query over field metadata plus a check of the tags in source control:

```bash
# Every field file under the intake object that carries the HIPAA compliance group
grep -l "<complianceGroup>HIPAA</complianceGroup>" force-app/main/default/objects/Patient_Intake__c/fields/*.field-meta.xml

# Any field on the object that is tracked for history but not tagged (review each hit)
for f in force-app/main/default/objects/Patient_Intake__c/fields/*.field-meta.xml; do
  grep -q "<trackHistory>true</trackHistory>" "$f" && ! grep -q "<complianceGroup>" "$f" && echo "REVIEW: $f"
done
```

The org-side view of each field's sensitivity value is the `FieldSecurityClassification` object (API 46.0), which "represents a field's data sensitivity value selected from the SecurityClassification picklist".

**Why it works:** The tags travel with each field through every deployment, so the inventory cannot drift from the org. The second loop catches fields someone tracked for audit but never classified.

