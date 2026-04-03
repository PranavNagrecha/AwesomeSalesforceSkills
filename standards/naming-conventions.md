# Salesforce Naming Conventions

These are the naming conventions enforced in this library's templates and skills. Apply them in every project unless the org has documented existing conventions that would make migration impractical.

---

## General Principles

1. **Clarity over brevity.** `AccountCreditLimitService` beats `AccCrLimSvc`.
2. **No abbreviations unless universal.** `Id`, `API`, `URL`, `HTTP`, `DML`, `SOQL` are fine. `Svc`, `Mgr`, `Util` are not.
3. **Prefix custom metadata with the org's namespace or project prefix.** Prevents clutter in package installs. e.g. `MYS_` for "My Services" project.
4. **Salesforce uses PascalCase for types, camelCase for members.** Follow this — don't invent a new convention.

---

## Apex

| Artifact | Convention | Example |
|----------|-----------|---------|
| Class | `PascalCase` + descriptive noun | `AccountCreditLimitService` |
| Test class | `[ClassName]Test` | `AccountCreditLimitServiceTest` |
| Trigger | `[ObjectName]Trigger` | `AccountTrigger` |
| Trigger handler | `[ObjectName]TriggerHandler` | `AccountTriggerHandler` |
| Interface | `I[Name]` | `IAccountService` |
| Abstract class | `Abstract[Name]` | `AbstractTriggerHandler` |
| Exception | `[Name]Exception` | `CreditLimitException` |
| Batch class | `[Name]Batch` | `AccountSyncBatch` |
| Queueable | `[Name]Queueable` | `CreditScoreUpdateQueueable` |
| Schedulable | `[Name]Scheduler` | `NightlyAccountSyncScheduler` |
| Method | `camelCase` verb + noun | `getCreditLimit()`, `updateAccountStatus()` |
| Variable | `camelCase` | `creditLimit`, `accountList` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_CREDIT_LIMIT`, `DEFAULT_TIMEOUT` |
| Test method | `methodName_scenario_expectedResult` | `getCreditLimit_noAccount_returnsZero` |

**Never:**
- `MyClass1`, `NewClass`, `TempHandler` — context-free names
- `util`, `helper`, `manager` as standalone class names — too vague
- Single-letter variables outside of for-loop counters

---

## Lightning Web Components

| Artifact | Convention | Example |
|----------|-----------|---------|
| Component folder | `camelCase` | `accountCreditLimit` |
| JS file | Same as folder | `accountCreditLimit.js` |
| HTML file | Same as folder | `accountCreditLimit.html` |
| CSS file | Same as folder | `accountCreditLimit.css` |
| Public property | `camelCase` | `accountId`, `showDetails` |
| Private property | `_camelCase` (leading underscore) | `_creditData`, `_isLoading` |
| Event name | `kebab-case` | `credit-limit-updated`, `account-selected` |
| Custom event (dispatched) | `on` + camelCase in handler | `onCreditLimitUpdated` |
| Wire property | `camelCase` + result pattern | `accountData`, `creditLimitResult` |

**Never:**
- PascalCase component names — they don't work in Salesforce's LWC router
- Generic names: `myComponent`, `testLWC`, `component1`
- Abbreviations: `acctCrdLmt` — meaningless without context

---

## Custom Objects and Fields

| Artifact | Convention | Example |
|----------|-----------|---------|
| Custom object | `PascalCase_Singular__c` | `Credit_Application__c` |
| Custom field | `PascalCase__c` | `Credit_Limit__c` |
| Lookup/master-detail | `[Related Object]__c` | `Account__c`, `Opportunity__c` |
| Junction object | `[ObjectA]_[ObjectB]__c` | `Contact_Campaign__c` |
| Checkbox | Start with `Is_` or `Has_` | `Is_Active__c`, `Has_Signed_NDA__c` |
| Currency/Number | Noun describing the value | `Annual_Revenue__c`, `Credit_Score__c` |
| Formula | Suffix `_Formula` is optional but helpful | `Full_Name_Formula__c` |

**Never:**
- Spaces in API names (Salesforce allows labels to have spaces, API names must use underscores)
- Generic labels: `Custom Field 1`, `Test Object`
- Re-using standard field names: never create `Name__c` on a custom object

---

## Flows

| Artifact | Convention | Example |
|----------|-----------|---------|
| Flow API name | `PascalCase` verb + object + qualifier | `UpdateAccountCreditStatus_OnChange` |
| Screen Flow | `[Process Name]_Screen` | `CreditApplication_Screen` |
| Autolaunched Flow | `[Process Name]_Auto` | `AccountSync_Auto` |
| Scheduled Flow | `[Process Name]_Scheduled` | `NightlyInvoiceUpdate_Scheduled` |
| Subflow | `[Process Name]_Sub` | `ValidateCreditLimit_Sub` |
| Variable | `camelCase`, descriptive | `accountId`, `creditLimitThreshold` |
| Collection variable | `camelCase` + `List` suffix | `accountList`, `opportunityList` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_CREDIT_LIMIT` |

**Never:**
- Spaces in Flow API names
- `Flow1`, `MyFlow`, `Test_Flow` — no context
- Single flows doing more than one logical process — split into subflows

---

## Validation Rules

| Artifact | Convention | Example |
|----------|-----------|---------|
| Validation rule | `[Object]_[What it validates]` | `Account_CreditLimit_Required` |
| Error message | Full sentence. Explain what went wrong AND what to do. | "Credit Limit is required for accounts in the Enterprise segment. Enter a value greater than 0." |

---

## Custom Labels

| Artifact | Convention | Example |
|----------|-----------|---------|
| Custom label | `[Object/Feature]_[Description]` | `Account_CreditLimitExceeded`, `Error_RequiredField` |

---

## Permission Sets

| Artifact | Convention | Example |
|----------|-----------|---------|
| Permission set | `[Role/Audience]_[What it grants]` | `Sales_CreditReview_Read`, `Admin_FullAccess` |
| Permission set group | `[Role]_[Feature set]` | `SalesRep_CreditManagement` |

**Never:**
- Profile-based access control for new features — use permission sets
- "Admin" permission sets that grant everything — granular is better

---

## Custom Metadata Types

| Artifact | Convention | Example |
|----------|-----------|---------|
| CMT API name | `[Feature]_Config__mdt` | `Credit_Limit_Config__mdt` |
| CMT record | `[Context]_[Variant]` | `Enterprise_Standard`, `SMB_Reduced` |

---

## Integration (Named Credentials, External Services)

| Artifact | Convention | Example |
|----------|-----------|---------|
| Named credential | `[System]_[Environment]` | `PaymentGateway_Production`, `CRM_Sandbox` |
| External credential | `[System]_[Auth method]` | `PaymentGateway_OAuth` |
| Remote site | `[System]_[Environment]` | `PaymentGateway_Production` |
