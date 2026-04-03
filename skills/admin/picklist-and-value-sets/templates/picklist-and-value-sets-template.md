# Picklist Design Document

**Object:** ___________________
**Field Name (Label):** ___________________
**Field API Name:** ___________________
**Prepared by:** ___________________ | **Date:** ___________________

---

## 1. Value Set Decision

| Question | Answer |
|---|---|
| Are these same values needed on 2+ objects? | Yes / No |
| Do values need to stay in sync across objects? | Yes / No |
| Does each object's lifecycle require different values long-term? | Yes / No |

**Decision:** ☐ Global Value Set — GVS Name: ___________________ ☐ Object-Local Picklist

**Reason for decision:** ___________________

---

## 2. Value List

| Value (API / stored) | Display Label | Active? | Notes |
|---|---|---|---|
| | | ☐ Yes ☐ No | |
| | | ☐ Yes ☐ No | |
| | | ☐ Yes ☐ No | |
| | | ☐ Yes ☐ No | |
| | | ☐ Yes ☐ No | |

*(Add rows as needed. Remember: 1,000 value max for standard picklists; 500 active for multi-select.)*

**Default value (if any):** ___________________

---

## 3. Controlling / Dependent Relationship

| Question | Answer |
|---|---|
| Does this field control another field? | Yes / No → Dependent field: ___________________ |
| Is this field controlled by another field? | Yes / No → Controlling field: ___________________ |
| Controlling field type | Picklist / Checkbox / N/A |

**Dependency matrix summary** (list which controlling values map to which dependent values):

| Controlling Value | Allowed Dependent Values |
|---|---|
| | |
| | |

**Validation Rule required for API enforcement?** ☐ Yes ☐ No — Rule name: ___________________

---

## 4. Data Replacement Plan

*(Complete this section if existing records need to be updated.)*

| Old Value | New Value | Estimated Record Count | Replace Job Scheduled? | Verified? |
|---|---|---|---|---|
| | | | ☐ Yes | ☐ Yes |
| | | | ☐ Yes | ☐ Yes |

**Post-replace actions (flows, validation rules, Apex, SOQL to update):**

- ___________________
- ___________________

---

## 5. Downstream Impact Checklist

- [ ] Validation rules referencing this field's values — reviewed and updated
- [ ] Flows and Process Builder automations — value strings verified
- [ ] Apex code using ISPICKVAL, picklist comparisons — reviewed
- [ ] Reports and dashboards with picklist filters — field/value alignment confirmed
- [ ] Page layouts and record types — picklist value visibility configured
- [ ] FLS confirmed for all relevant profiles/permission sets

---

## 6. Review Sign-off

| Step | Done | Notes |
|---|---|---|
| Values configured in Setup | ☐ | |
| Dependency matrix configured (if applicable) | ☐ | |
| Replace job(s) completed and verified | ☐ | |
| Old values deactivated (not deleted) | ☐ | |
| Downstream references updated | ☐ | |
| Tested in sandbox before production deployment | ☐ | |
