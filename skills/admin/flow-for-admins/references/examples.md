# Examples: Flow for Admins

---

## Example: Record-Triggered Flow — Update Parent When Child Changes (Bulkification Pattern)

**Requirement:** When a Case is closed, update the parent Account's Last_Case_Closed_Date__c field.

**Flow type:** Record-Triggered Flow (After Save — needs DML on a different object)

**Entry criteria:** `{!$Record.Status} = "Closed"` AND `{!$Record.Status} <> {!$Record__Prior.Status}` (only when Status changes TO Closed)

**Structure:**

```
[TRIGGER: Case After Save — when Status changes to "Closed"]
          ↓
[GET RECORDS: Account where Id = {!$Record.AccountId}]
  ├── fault → [SEND EMAIL: Fault on Get Account] → [END]
  └── success ↓
[UPDATE RECORDS: Account — set Last_Case_Closed_Date__c = TODAY()]
  ├── fault → [SEND EMAIL: Fault on Update Account] → [END]
  └── success ↓
[END]
```

**Why the entry criteria matters:** Without `{!$Record.Status} <> {!$Record__Prior.Status}`, this flow fires every time ANY field on a Closed Case is edited — adding a comment, changing the owner, anything. The delta check (`<> Prior`) ensures it only fires when Status transitions to Closed.

**Bulkification note:** This flow is already bulk-safe. "Update Records" with a single record variable (not a loop) is one DML statement regardless of how many Cases are in the transaction.

---

## Example: Screen Flow — Multi-Step Data Entry with Validation

**Requirement:** Guided screen for converting a Lead to a Contact with custom qualification questions.

**Flow type:** Screen Flow (user-initiated, guided process)

**Structure:**

```
[SCREEN 1: Qualification Questions]
  - Lead Interest Level (picklist — required)
  - Budget Confirmed (checkbox)
  - Decision Timeline (text — required)
  Next button → validates required fields
          ↓
[DECISION: Is Budget Confirmed?]
  ├── Yes → [SCREEN 2A: Budget Details]
  └── No  → [SCREEN 2B: Budget Discovery]
          ↓
[CREATE RECORDS: Create Qualified_Lead_Response__c]
  ├── fault → [SCREEN: Error — "We couldn't save your response. Contact your admin."]
  └── success ↓
[SCREEN: Confirmation — "Lead qualified. Next steps: [...]"]
          ↓
[END]
```

**Error screen pattern:** The fault path for DML in a Screen Flow should show the user a human-readable screen, not a Salesforce system error. Always capture `{!$Flow.FaultMessage}` in the error screen for admin debugging.

```
Error Screen content:
"We encountered an issue saving this record.
Error details: {!$Flow.FaultMessage}
Please contact [Admin Email] and reference Lead ID: {!$Record.Id}"
```

---

## Example: Scheduled Flow — Weekly Cleanup with Batch-Safe Patterns

**Requirement:** Every Monday at 6am, find all Leads that haven't been contacted in 30+ days and set Status to "Unresponsive".

**Flow type:** Scheduled Flow

**Key consideration:** Scheduled Flows have a limit of 250,000 interviews per run, and each record processed is one interview. For large datasets, consider Batch Apex instead.

**Structure:**

```
[SCHEDULE: Monday 6:00 AM]
          ↓
[GET RECORDS: Lead where LastActivityDate < (TODAY - 30)
              AND Status NOT IN ("Converted", "Unresponsive", "Closed")
              LIMIT: 2000]  ← always set a practical limit
  ├── fault → [SEND EMAIL: Fault getting leads] → [END]
  └── success ↓
[LOOP: through Lead collection]
          ↓
  [ASSIGNMENT: set loopLead.Status = "Unresponsive"]
  [ADD to updateLeadCollection]
          ↓
[END LOOP]
          ↓
[UPDATE RECORDS: updateLeadCollection]  ← single DML, not in loop
  ├── fault → [SEND EMAIL: Fault updating leads]
  └── success ↓
[END]
```

**Why the LIMIT:** Without a LIMIT, if 50,000 Leads match the criteria, the Scheduled Flow tries to process all of them. For very large volumes, use Batch Apex. The LIMIT makes the behaviour predictable.

---

## Example: Autolaunched Flow — Called from Apex with Input/Output Variables

**Requirement:** Complex pricing logic managed by Admins, called from Apex during Opportunity save.

**Flow type:** Autolaunched Flow (no trigger — called programmatically)

**Flow variables to configure:**
- `inputOpportunityId` (Text, Input) — passed from Apex
- `inputProductFamily` (Text, Input) — passed from Apex
- `outputDiscountPercent` (Number, Output) — returned to Apex

**Apex call pattern:**
```apex
Map<String, Object> inputs = new Map<String, Object>{
    'inputOpportunityId' => opp.Id,
    'inputProductFamily' => opp.Product_Family__c
};

Flow.Interview interview = Flow.Interview.createInterview(
    'Calculate_Opportunity_Discount',  // Flow API name
    inputs
);
interview.start();

Decimal discount = (Decimal) interview.getVariableValue('outputDiscountPercent');
```

**Why use a Flow here instead of Apex:** Business users can modify pricing rules in Flow Builder without a code deployment. The Apex caller doesn't change — only the Flow logic changes. This is the "configurable logic" pattern.

**Governor limit warning:** This Flow runs in the same transaction as the Apex call. Any SOQL in the Flow counts against the transaction's SOQL limit. Design the Flow to be SOQL-minimal.
