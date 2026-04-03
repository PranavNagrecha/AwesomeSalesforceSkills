# Gotchas: Record Types and Page Layouts

---

## Changing a Record's Record Type Can Wipe Picklist Values

**What happens:** An admin bulk-reassigns 5,000 Opportunity records from "New Business" RT to "Renewal" RT (because the company restructured its sales motion). After the reassignment, users report that the Stage field on 3,000 records is now blank. "Prospecting" and "Discovery" exist on New Business RT but not on Renewal RT. When the RT changed, those picklist values were cleared because they're not valid on the new RT.

**When it bites you:** Any bulk Record Type reassignment, any workflow/flow that changes a record's RT, any migration combining business units that used different RTs.

**How to avoid it:**
1. Before ANY RT reassignment: run a SOQL to find all records with picklist values that don't exist on the target RT
2. Map the source picklist values to equivalent target values
3. Update picklist values BEFORE changing the RT, not after
4. Test the entire sequence in sandbox with a representative sample

SOQL to identify at-risk records:
```soql
-- Find Opportunities with "Prospecting" stage that will be affected
SELECT Id, Name, StageName, RecordType.Name
FROM Opportunity
WHERE RecordType.DeveloperName = 'New_Business'
AND ISPICKVAL(StageName, 'Prospecting')
-- Then check: does "Prospecting" exist on the target RT? If not, these records lose their Stage value.
```

---

## Record Types and Person Accounts — Design Them Separately

**What happens:** An org enables Person Accounts. The admin creates Record Types for Business Accounts and assigns them. Later, someone creates a Person Account and gets an error or unexpected RT assignment. The RT model for Person Accounts and Business Accounts is governed by the same object but behaves differently — Person Account RTs must be designed with the Person Account user profile in mind, and Business Account RTs must be hidden from Person Account creation.

**When it bites you:** Any org that enables Person Accounts after the Account RT model is already built. Also: Community portals where external users are Person Accounts.

**How to avoid it:**
- Design RT models for Business and Person Accounts separately, as if they're two different objects
- Use separate Profiles/PSGs to control which users see which Account RT type
- Test Person Account creation with the portal user profile — not the System Administrator profile
- Document explicitly: "Person Account RTs" vs "Business Account RTs" in your permission model

---

## New Profiles Don't Inherit Record Type Assignments

**What happens:** A managed AppExchange package is installed and creates a new custom Profile. Users assigned to that Profile try to create Accounts and can't select any Record Type (or are forced to the Master RT with all picklist values). The admin doesn't know until users report it because no alert fires when a new Profile is created with no RT assignments.

**When it bites you:** Package installations, profile cloning, new onboarding processes that create users with a profile the admin didn't configure.

**How to avoid it:**
- After any package installation, immediately check the profiles it creates and configure RT assignments
- Create a checklist item in your onboarding process: "Verify Record Type assignments on all Profiles used by this user role"
- Run this SOQL periodically to find profiles with users but no RT assignments (for key objects):

```soql
-- Profiles with active users — check if they have RT assignments
SELECT Profile.Name, COUNT(Id) UserCount
FROM User
WHERE IsActive = TRUE
GROUP BY Profile.Name
ORDER BY Profile.Name
-- Then cross-reference with RT assignments in Setup → Record Types
```

---

## Reports Filter by Record Type Label — Labels Are Not Stable

**What happens:** A business analyst builds 20 reports filtered by "Opportunity Type = New Business". An admin renames the Record Type label from "New Business" to "New Logo" (rebranding). Every one of those 20 reports now returns zero results — they're filtering for "New Business" which no longer exists. The analyst doesn't notice immediately. A week later, an executive dashboard shows zero pipeline.

**When it bites you:** Any time a Record Type label is renamed. This is a support ticket waiting to happen.

**How to avoid it:**
- Before renaming a RT label: audit all reports that filter on that RT name
- Consider: only rename the label if necessary; the Developer Name (API name) is what code uses and is stable
- After renaming: search for the old label in report filters and update them
- Communicate RT renames to report owners BEFORE making the change

---

## Page Layouts Are Not Security Controls

**What happens:** An admin hides the `Salary__c` field on the page layout for non-HR users, assuming this restricts access. A power user opens the field in a report or accesses it via the API. The field is visible. The admin says "I hid it on the layout." Yes, but the layout is a UX control — it affects what appears on the record detail page, not what the user can access through other means.

**When it bites you:** Any time a field contains sensitive data (PII, financial, compensation) and the only restriction is a page layout.

**How to avoid it:**
- Use FLS (Field-Level Security) to actually restrict field access — not page layouts
- Page layout: controls what appears on the record page
- FLS: controls whether the user can see or edit the field AT ALL, in any context
- Both are needed: FLS for security, page layout for UX
