# Examples: Permission Sets vs Profiles

---

## Example: Migrating 5 Profiles to 3 Permission Set Groups

**Context:** A mid-size org has grown to 5 custom profiles — `Sales_Rep`, `Sales_Manager`, `Service_Agent`, `Service_Manager`, and `ReadOnly_User`. The ops team is making manual profile swaps weekly as people change roles. Goal: migrate to Permission Set Groups.

### Step 1: Audit what each profile actually grants (SOQL)

```soql
-- Run in Developer Console or Query Tool
-- Profile user distribution
SELECT Profile.Name, COUNT(Id) UserCount
FROM User
WHERE IsActive = TRUE
GROUP BY Profile.Name
ORDER BY COUNT(Id) DESC

-- Permission Sets assigned per user
SELECT AssigneeId, Assignee.Name, PermissionSet.Name, PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE Assignee.IsActive = TRUE
AND PermissionSet.IsOwnedByProfile = FALSE
ORDER BY Assignee.Name
```

### Step 2: Map profiles to Permission Set Groups

| Old Profile | Base Profile | Permission Set Group |
|-------------|-------------|---------------------|
| `Sales_Rep` | `SFUser_MinimumAccess` | `SalesRep_Core` |
| `Sales_Manager` | `SFUser_MinimumAccess` | `SalesRep_Core` + `SalesManager_Elevated` |
| `Service_Agent` | `SFUser_MinimumAccess` | `ServiceAgent_Core` |
| `Service_Manager` | `SFUser_MinimumAccess` | `ServiceAgent_Core` + `ServiceManager_Elevated` |
| `ReadOnly_User` | `SFUser_ReadOnly` | *(no PSG needed — base profile is sufficient)* |

### Step 3: Design Permission Sets for SalesRep_Core PSG

```
SalesRep_Core (Permission Set Group)
├── Account_ReadEditCreate          [Object: Account CRUD=REC, FLS: standard sales fields]
├── Opportunity_ReadEditCreate      [Object: Opportunity CRUD=REC, FLS: all standard fields]
├── Contact_ReadEditCreate          [Object: Contact CRUD=REC, FLS: standard contact fields]
├── Lead_ReadEditCreate             [Object: Lead CRUD=REC, FLS: standard lead fields]
└── Reports_Dashboards_Access       [Custom Permission: View_Reports]
```

### Step 4: Test before migrating

1. Create a test user with `SFUser_MinimumAccess` profile + `SalesRep_Core` PSG
2. Log in as the test user (use "Login as User" or create a sandbox test user)
3. Verify: Can see Accounts, Opportunities, Contacts, Leads ✓
4. Verify: Cannot see objects not in the PSG ✓
5. Verify: Login hours and IP restrictions from the Minimum Access profile apply ✓

### Step 5: Migrate in batches

```
Week 1: Migrate Sales_Rep users (lowest risk — most users)
Week 2: Migrate Service_Agent users
Week 3: Migrate managers (smaller group — easier to verify)
Week 4: Decommission old profiles (don't delete immediately — wait 30 days)
```

---

## Example: SOQL to Audit Profile and Permission Set Usage

**Purpose:** Before any permission redesign, understand the current state.

```soql
-- Profiles with user counts (find candidates to merge or retire)
SELECT Profile.Name, Profile.UserLicense.Name, COUNT(Id) cnt
FROM User
WHERE IsActive = TRUE
GROUP BY Profile.Name, Profile.UserLicense.Name
ORDER BY COUNT(Id) DESC

-- Users with more than 5 Permission Sets (possible over-permission signal)
SELECT AssigneeId, Assignee.Name, COUNT(Id) PsCount
FROM PermissionSetAssignment
WHERE Assignee.IsActive = TRUE
AND PermissionSet.IsOwnedByProfile = FALSE
GROUP BY AssigneeId, Assignee.Name
HAVING COUNT(Id) > 5
ORDER BY COUNT(Id) DESC

-- Permission Sets with no assignments (candidates for cleanup)
SELECT Id, Name, Label, IsOwnedByProfile
FROM PermissionSet
WHERE IsOwnedByProfile = FALSE
AND Id NOT IN (SELECT PermissionSetId FROM PermissionSetAssignment)
ORDER BY Name

-- Find all users assigned a specific Permission Set
SELECT Assignee.Name, Assignee.Profile.Name, PermissionSet.Name
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Account_Edit_SalesRep'
AND Assignee.IsActive = TRUE
ORDER BY Assignee.Name
```

---

## Example: Naming Convention Applied — Permission Set Design

**Scenario:** Designing access for a new "Credit Review" feature on the Account object.

```
Feature: Credit Review
Objects involved: Account (read credit fields), Credit_Application__c (create, edit, read)
Users: Credit Analysts (read + create), Credit Managers (read + create + approve + delete)

Permission Sets to create:
├── Account_CreditFields_Read
│   Object: Account
│   FLS: Credit_Limit__c (Read), Credit_Score__c (Read), Credit_Status__c (Read)
│
├── CreditApplication_ReadCreate
│   Object: Credit_Application__c
│   CRUD: Read, Create, Edit
│   FLS: All fields (Read + Edit)
│
├── CreditApplication_Approve
│   Object: Credit_Application__c
│   FLS: Approval_Status__c (Edit), Approved_By__c (Edit), Approval_Date__c (Edit)
│   Custom Permission: Approve_Credit_Application
│
└── CreditApplication_Delete
    Object: Credit_Application__c
    CRUD: Delete

Permission Set Groups:
├── CreditAnalyst_Core
│   Contains: Account_CreditFields_Read + CreditApplication_ReadCreate
│
└── CreditManager_Full
    Contains: Account_CreditFields_Read + CreditApplication_ReadCreate
              + CreditApplication_Approve + CreditApplication_Delete
```

This design means:
- Adding a new Credit Analyst = assign `CreditAnalyst_Core` PSG. Done. No profile change.
- Promoting to Credit Manager = reassign PSG. One operation.
- Revoking credit access = remove PSG. Audit trail via PSG assignment log.
