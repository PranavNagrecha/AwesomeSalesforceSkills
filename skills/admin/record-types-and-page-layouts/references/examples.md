# Examples: Record Types and Page Layouts

---

## Example: Opportunity Record Types — New Business vs Renewal vs Upsell

**Context:** A SaaS company has three distinct sales motions with different stages, fields, and team assignments.

### Record Type Design

| Property | New Business | Renewal | Upsell |
|----------|-------------|---------|--------|
| **RT Developer Name** | `New_Business` | `Renewal` | `Upsell` |
| **Assigned to** | `AE_Core` PSG | `CSM_Core` PSG | `AE_Core` + `CSM_Core` PSG |
| **Page Layout** | `Opportunity_NewBusiness` | `Opportunity_Renewal` | `Opportunity_Upsell` |

### Stage Picklist Values per Record Type

| Stage | New Business | Renewal | Upsell |
|-------|:-----------:|:-------:|:------:|
| Prospecting | ✅ | ❌ | ❌ |
| Discovery | ✅ | ❌ | ✅ |
| Renewal Review | ❌ | ✅ | ❌ |
| Proposal | ✅ | ✅ | ✅ |
| Negotiation | ✅ | ✅ | ✅ |
| Closed Won | ✅ | ✅ | ✅ |
| Closed Lost | ✅ | ✅ | ✅ |

### Key Page Layout Differences

**New Business layout:** Lead Source (prominent), Competitor__c, Why_Won_Lost__c, AE owner
**Renewal layout:** Contract_End_Date__c, Health_Score__c, Renewal_Risk__c, CSM owner field
**Upsell layout:** Existing_MRR__c, Upsell_Opportunity_Type__c (picklist: Expansion / Cross-sell), AE + CSM dual owners

### What this solves:
- Renewals don't see "Prospecting" stage (doesn't apply to their process)
- New Business doesn't see "Renewal Review" stage
- Each team sees only the fields relevant to their sales motion
- Reports can filter by Record Type to get accurate pipeline by motion

---

## Example: Case Record Types — Internal vs Customer-Facing

**Context:** A support team handles both internal IT tickets and customer-facing support cases in the same Case object.

### Record Type Design

| Property | Internal IT | Customer Support |
|----------|------------|-----------------|
| **RT Developer Name** | `Internal_IT` | `Customer_Support` |
| **Assigned to** | `Employee_Self_Service` PSG | `ExternalUser_Support` profile (Community) |
| **Page Layout** | `Case_Internal` | `Case_Customer` |
| **Community visibility** | Hidden | Visible |

### Picklist Value Differences

**Priority (Internal IT):** Low, Medium, High, P1 (Emergency)
**Priority (Customer Support):** Standard, Expedited, Critical

**Category (Internal IT):** Hardware, Software, Access, Network, Other
**Category (Customer Support):** Billing, Technical, General, Feature Request

### Validation Rule Scoped by Record Type

```
// Close Date required for Customer Support cases only
AND(
  RecordType.DeveloperName = "Customer_Support",
  ISPICKVAL(Status, "Closed"),
  ISBLANK(Resolved_Date__c)
)
```

---

## Example: When Dynamic Forms Replaces Multiple Page Layouts

**Context:** An org has 6 Account Record Types that all have the same picklist values. The only difference is which fields appear on the layout. This is a Dynamic Forms candidate.

**Before:** 6 Record Types × 6 Page Layouts = 6 layouts to maintain

**After:** 1 Record Type + Dynamic Forms with field visibility rules

### Dynamic Forms visibility rules (examples)

| Field | Visible When |
|-------|-------------|
| `Credit_Limit__c` | `Account.Type = "Customer"` |
| `Partner_Tier__c` | `Account.Type = "Partner"` |
| `Government_Entity_Type__c` | `Account.Industry = "Government"` |
| `Support_Contract_Level__c` | `Account.Active_Support_Contract__c = TRUE` |

**Result:** One RT, one layout, fields show/hide based on field values — no RT proliferation.

**When this doesn't work:**
- Picklist values differ by process → Must use Record Types
- Classic orgs → Dynamic Forms not available
- Mobile app with full offline → Limited Dynamic Forms support
