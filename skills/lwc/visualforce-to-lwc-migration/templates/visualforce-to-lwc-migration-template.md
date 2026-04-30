# Visualforce to LWC Migration — Work Template

Use this template when planning and executing the migration of a Visualforce page to LWC.

---

## Scope

**Skill:** `visualforce-to-lwc-migration`

**Visualforce page being migrated:** _(fill in `MyPage.page`)_

**Surface(s) where it lives today:** _(custom tab, App Builder page, button override, embedded VF, etc.)_

**Migration decision:** [ ] Full migration to LWC  [ ] Partial — keep VF for retention reason  [ ] Lightning Out wrapper coexistence

---

## Pre-Migration Audit

Complete this section before writing any LWC code.

### Page-Level Attributes

| `apex:page` Attribute | Value | LWC Implication |
|---|---|---|
| `controller` | | Becomes `@AuraEnabled` Apex service class |
| `extensions` | | Methods merge into the new service class |
| `standardController` | | Replaced by `@api recordId` + Lightning Data Service |
| `renderAs` | | If `pdf` → DO NOT MIGRATE; retain VF |
| `contentType` | | Custom content types are NOT migratable |
| `tabStyle` | | Maps to LWC `js-meta.xml` `targets` |
| `applyHtmlTag` / `applyBodyTag` | | Lightning components define their own root |

### URL Parameters Consumed

| Param Name | Used For | LWC Equivalent |
|---|---|---|
| `id` | Record ID | `@api recordId` (when invoked from record page) OR `pageRef.state.c__id` (App Builder) |
| | | |

### Controller Methods

| Method Name | Return Type | Mutates? | LWC Pattern |
|---|---|---|---|
| `getX()` (property) | | No | `@AuraEnabled(cacheable=true)` + `@wire` |
| `save()` (action) | `PageReference` | Yes | `@AuraEnabled(cacheable=false)` + imperative + NavigationMixin |
| | | | |

### Markup Inventory

| Pattern | Count | LWC Replacement |
|---|---|---|
| `<apex:inputField>` | | `<lightning-input-field>` in `<lightning-record-edit-form>` |
| `<apex:outputField>` | | Template binding or `<lightning-formatted-*>` |
| `<apex:repeat>` | | `for:each` template directive |
| `<apex:pageBlockTable>` | | `<lightning-datatable>` |
| `<apex:commandButton>` | | `<lightning-button>` + JS handler |
| `<apex:actionFunction>` | | Imperative Apex import |
| `<apex:outputText escape="false">` | | MUST sanitize; no direct equivalent |
| `<apex:includeScript>` | | `loadScript` from `lightning/platformResourceLoader` |

### Static Resources

| Resource | Used In | LWS-Compatible? |
|---|---|---|
| | | [ ] Yes  [ ] No  [ ] Untested |

---

## Apex Service Refactor Plan

```apex
// Old: MyPageController (instance class with viewstate)
// New: MyPageService (static @AuraEnabled methods)

public with sharing class MyPageService {
    public class SnapshotDto {
        @AuraEnabled public Account account;
        @AuraEnabled public List<Contact> contacts;
    }

    @AuraEnabled(cacheable=true)
    public static SnapshotDto getSnapshot(Id accountId) {
        // implementation with WITH SECURITY_ENFORCED
    }

    @AuraEnabled
    public static Id save(Account record) {
        // implementation
    }
}
```

---

## LWC Bundle Plan

| File | Notes |
|---|---|
| `myPage.js` | `@api recordId`, `@wire(getSnapshot, ...)` |
| `myPage.html` | Template with conditional rendering (`if:true={snapshot.data}`) |
| `myPage.css` | SLDS-aligned styles (avoid Bootstrap / external CSS frameworks) |
| `myPage.js-meta.xml` | `targets`: `lightning__RecordPage`, `lightning__Tab`, etc. |

---

## Navigation Translation

| Original `PageReference` | Lightning Equivalent |
|---|---|
| `new PageReference('/' + recordId)` | `NavigationMixin.Navigate({type: 'standard__recordPage', attributes: {recordId, actionName: 'view'}})` |
| `new PageReference('/apex/Confirm?id=' + id)` | Quick Action launching the confirmation LWC |
| | |

---

## Test Plan

- [ ] All controller properties have parity in `@wire` results
- [ ] All controller actions have parity in imperative method results
- [ ] FLS enforced (run as a user without field access; verify hidden state matches VF behavior)
- [ ] URL parameters work via `pageRef.state.c__*` for App Builder pages
- [ ] LWS compatibility verified (run in LWS-enabled scratch org)
- [ ] No `<apex:outputText escape="false">` patterns survived
- [ ] Lightning Out wrapper VF page (if used) is documented with removal date

---

## Decommissioning Plan

- [ ] VF page removed from App Builder / tab assignment / button override (or wrapped via Lightning Out)
- [ ] Original VF controller deleted (only after confirming no other VF page uses it)
- [ ] External callers updated to new URL contract (or Lightning Out wrapper retained)
- [ ] Migration audit log entry recorded
