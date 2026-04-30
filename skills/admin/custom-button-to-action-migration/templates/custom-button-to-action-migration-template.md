# Custom Button to Action Migration — Work Template

Use this template when migrating Classic custom buttons (especially JavaScript buttons) to Lightning Quick Actions / Screen Flows / LWC Quick Actions.

---

## Scope

**Skill:** `custom-button-to-action-migration`

**Object:** _(target object)_

**Button count:**

```bash
sf data query --use-tooling-api --query \
  "SELECT BehaviorType, ContentSource, COUNT(Id) FROM WebLink WHERE EntityDefinition.QualifiedApiName='Account' GROUP BY BehaviorType, ContentSource"
```

| BehaviorType | ContentSource | Count |
|---|---|---|
| Detail | OnClickJavaScript | |
| Detail | URL | |
| List | OnClickJavaScript | |
| Mass | OnClickJavaScript | |

---

## Per-Button Decision Matrix

| Button Name | Type | JS / URL Body Summary | Replacement Pattern | Notes |
|---|---|---|---|---|
| MarkHotProspect | Detail | Calls Apex, alerts, reloads | Headless LWC Quick Action (Pattern 1) | |
| OpenLinkedInLookup | Detail URL | External URL | URL Quick Action (Pattern 4) | |
| MassMarkAsKey | Mass | getRecordIds + Apex | Mass Quick Action with LWC (Pattern 3) | |
| | | | | |

Patterns: `1=Headless LWC`, `2=Screen Flow`, `3=Mass Quick Action`, `4=URL Action`, `5=Coexistence (retain Classic)`, `Retire=No replacement`.

---

## Apex Service Refactor

| Original Apex Method | Becomes | Visibility |
|---|---|---|
| (existing class).markAsHotProspect | `@AuraEnabled` static (cacheable=false) with `with sharing` + `WITH SECURITY_ENFORCED` | Public to LWC |
| | | |

---

## Coexistence Tracking

Add `Last_Action_Source__c` (Picklist) to the object:

| Source | Description |
|---|---|
| Classic Button | JS button invocation |
| Lightning Action | New Lightning Quick Action / LWC / Flow |

Update both Classic JS button code and the new Apex method to write this field.

---

## Adoption Goal

Retire the Classic button when:

- [ ] Adoption metric: ≥ 95% of invocations from "Lightning Action" over rolling 30 days
- [ ] OR fixed retirement date: _(YYYY-MM-DD)_

---

## Test Plan

For each migrated button:

- [ ] Functional parity in sandbox
- [ ] User acceptance: representative user from each affected profile confirms action is discoverable and works
- [ ] Mobile (iOS Salesforce App)
- [ ] Mobile (Android Salesforce App)
- [ ] Service Console subtab navigation (if applicable)
- [ ] Mass Action: tested with selection > 200 (verify chunking or user notification)

---

## Sign-Off Checklist

- [ ] Every Classic button has a documented decision: replaced, retained for Classic, or retired
- [ ] LWS-incompatible patterns removed (no `alert()`, no `confirm()`, no `sforce.*`)
- [ ] No Apex method called from LWC returns `PageReference`
- [ ] Mass Action 200-record limit handled explicitly in code/UX
- [ ] Coexistence tracking field deployed and being populated
- [ ] Mobile testing completed
- [ ] Migration audit log persisted (Custom_Button_Migration_Log__c)
- [ ] Retirement criterion documented and being measured
