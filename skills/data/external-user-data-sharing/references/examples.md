# Examples — External User Data Sharing

## Example 1: Sharing Set for Customer Community Users to Access Their Own Account Cases

**Context:** A B2C support portal built on Experience Cloud uses Customer Community (High-Volume Portal) licenses. Support agents create Cases linked to customer Accounts. The requirement is that a logged-in community user can view and update Cases associated with their Account, but cannot see Cases belonging to other customers.

**Problem:** Without a Sharing Set, the External OWD on Case is Private (correct for isolation), but HVP users get no access to any Case records. Attempts to configure a criteria-based sharing rule to grant access produce a rule that appears valid in Setup but silently has no effect for HVP users.

**Solution:**

```
Setup > Digital Experiences > Settings > Sharing Sets

1. Click "New" to create a Sharing Set.
   Label: Customer Community Case Access
   Profile(s): [Customer Community User profile]

2. Under "Configure Access", click Set Up next to Case.
   Access Based On:
     User.AccountId → Case.AccountId   (maps community user's Account to the Account field on Case)
   Access Level: Read/Write

3. Save. Allow background sharing recalculation to complete.
4. Log in as a test Customer Community user.
   Verify: Cases for the user's Account appear in the portal view.
   Verify: Cases for a different Account are not visible.
```

**Why it works:** The Sharing Set evaluates the relationship at query time for HVP users. Because the community user's `AccountId` matches the `AccountId` on the Case, access is granted. No sharing rules are created or evaluated — the Sharing Set engine handles HVP users exclusively.

---

## Example 2: Criteria-Based Sharing Rule for Customer Community Plus Regional Data Access

**Context:** A B2B portal uses Customer Community Plus licenses for partner accounts. Each Case record has a `Region__c` field (picklist: North, South, East, West). The requirement is that CC Plus users associated with the West region should see all Cases in the West region regardless of which Account owns them.

**Problem:** With External OWD on Case set to Private, CC Plus users can only see Cases they own or that are shared directly with them. A Sharing Set cannot filter on `Region__c` — Sharing Sets are relationship-based only. A Sharing Set would be ineffective here even if CC Plus supported it.

**Solution:**

```
Setup > Security > Sharing Settings > Case Sharing Rules > New

Rule Type: Based on criteria
Rule Name: West Region Case Access for CC Plus Users

Criteria:
  Field: Region__c   Operator: equals   Value: West

Share With:
  Customer Portal Users — [select the West Region community role group or "All Customer Portal Users"]

Access Level: Read Only

Save. Click "Recalculate" if prompted, or wait for the background job.
Verify: Log in as a test CC Plus user. Navigate to Cases. Cases with Region__c = West are visible.
Verify: Cases with Region__c = North are not visible (unless also owned by the user).
```

**Why it works:** Customer Community Plus participates in the full Salesforce sharing model. Criteria-based sharing rules are evaluated for CC Plus users, unlike HVP users. The rule grants Read Only access to all Cases matching the criteria for the specified portal user group.

---

## Anti-Pattern: Applying a Criteria-Based Sharing Rule to Customer Community (HVP) Users

**What practitioners do:** Architects new to the sharing model configure a criteria-based sharing rule intended for all community users, selecting the Customer Community profile as the share target. The rule appears correctly configured in Setup with no warnings.

**What goes wrong:** High-Volume Portal (Customer Community) users are excluded from criteria-based sharing rule evaluation by design. The rule exists but produces no access for HVP users. No error is thrown. Test users get no records and the team spends hours debugging OWD settings, profiles, and permission sets before discovering that HVP users require a Sharing Set.

**Correct approach:** Identify whether the target users are HVP (Customer Community) or CC Plus before choosing a mechanism. HVP always requires a Sharing Set. Criteria-based sharing rules work only for Customer Community Plus and Partner Community users.
