# Gotchas — Visualforce Security And Modernization

Non-obvious Salesforce platform behaviors that bite teams during Visualforce hardening or modernization.

---

## Gotcha 1: View state has a 170 KB ceiling that fires only at certain user data scales

**What happens:** A page works for the developer, works for QA users, works for most production users — then suddenly throws `Maximum view state size limit (170KB) exceeded` for a specific user with a large data set or a specific record with many related items. Users without view-state-heavy data never see the issue.

**When it occurs:** The 170 KB limit is per page request. Page-state size scales with the underlying record's children, picklist values cached in the controller, and the user's custom permissions / sharing footprint (which can pull more rows into a list controller). A user with 800 child records vs the dev's 10 will hit the ceiling that the developer never saw.

**How to avoid:** Mark display-only collections `transient` (they are not serialized to view state). Restrict SOQL to fields actually used. For genuinely heavy pages, skip view state entirely — use `<apex:remoteAction>` or JavaScript Remoting and let the client fetch data on demand. Verify with the View State Inspector in Developer Console (Setup → Developer Console → Debug → View State).

---

## Gotcha 2: FLS is not auto-enforced on `<apex:outputField>` when the field is a formula referring to FLS-restricted source fields

**What happens:** A formula field `Margin__c` is defined as `Revenue__c - Cost__c`. The user has FLS read access to `Margin__c` but not to `Cost__c`. An `<apex:outputField value="{!opp.Margin__c}"/>` happily renders the computed margin even though the user cannot see one of the inputs. The user effectively sees a value derived from data they have no access to.

**When it occurs:** Any formula field that references FLS-restricted source fields. Common with cost/margin formulas, salary band formulas, and any computed sensitive metric.

**How to avoid:** Treat formulas referencing sensitive fields as themselves sensitive — restrict FLS on the formula field itself, not just the source fields. The platform does not propagate FLS through formulas. This is documented behavior; review the FLS posture of all formula fields during the audit.

---

## Gotcha 3: CSRF protection covers form POSTs, not the page-level `action` attribute

**What happens:** A page has `<apex:page action="{!processSubmission}">` where `processSubmission()` performs DML. The team assumes "Salesforce has anti-CSRF, we're fine." An attacker creates a page on their own site with `<img src="https://victim.my.salesforce.com/apex/MyPage?id=X">`. A logged-in user visits the attacker's page; their browser auto-loads the VF page; `processSubmission()` fires and mutates data.

**When it occurs:** Whenever a VF page uses the `action` attribute on `<apex:page>` to perform any state-changing operation. The platform's automatic CSRF token works for `<apex:form>` POST submissions only — page-action attributes execute on every GET to the URL.

**How to avoid:** Reserve `<apex:page action>` for read-only data loading (initialize cached state, redirect logic). Move every DML or state-changing call into a `<apex:commandButton>` action inside `<apex:form>`. Audit the codebase for `<apex:page` with `action="{!..}"` and inspect each method for DML.

---

## Gotcha 4: `with sharing` does not enforce FLS or CRUD — only record visibility

**What happens:** A controller class is annotated `with sharing`. Code review marks it secure. The class queries `[SELECT Salary__c FROM Employee__c]` and a community user sees the field even though their FLS permission removes read access to `Salary__c`. The reviewer assumed `with sharing` covered FLS — it does not.

**When it occurs:** Whenever a code reviewer treats `with sharing` / `without sharing` as the security keyword. The keyword only governs which *records* the user can see (sharing rules, role hierarchy, OWD); FLS and CRUD on *fields and objects* are separate enforcement layers.

**How to avoid:** Pair `with sharing` with `WITH USER_MODE` on every SOQL query. `WITH USER_MODE` (Summer '23+) enforces both FLS and CRUD; the older `WITH SECURITY_ENFORCED` is an acceptable alternative. For DML, use `Database.insert(records, AccessLevel.USER_MODE)`. Treat `with sharing` alone as record-level only — never as a complete security posture.

---

## Gotcha 5: `<apex:includeScript>` and `<apex:stylesheet>` are subject to the org-level Content Security Policy

**What happens:** A VF page uses `<apex:includeScript value="https://cdn.example.com/lib.js"/>` and the script silently fails to load. The console shows a CSP violation: `Refused to load the script 'https://cdn.example.com/lib.js' because it violates the following Content Security Policy directive`.

**When it occurs:** Any time a Visualforce page loads JS or CSS from a host that is not in the org's CSP Trusted Sites allowlist. The default CSP for Visualforce in modern orgs is restrictive; CDNs need explicit allowlisting via Setup → Security → CSP Trusted Sites.

**How to avoid:** Add the CDN host (and any other external resource origin) to CSP Trusted Sites. Better yet, host the JS/CSS as a Static Resource — `<apex:includeScript value="{!URLFOR($Resource.MyLib)}"/>` is always allowed because the resource is served from the same Salesforce origin. CDN-hosted libraries also create a supply-chain risk; static resources are versioned and reviewed.

---

## Gotcha 6: `<apex:dynamicComponent>` can render permission-restricted UI based on values that are tampered client-side

**What happens:** A page uses `<apex:dynamicComponent componentValue="{!getDynamicSection}"/>` where `getDynamicSection()` returns one of several `Component.Apex.OutputPanel` trees based on user permissions. The team thinks "the controller decides which component to render, so it's secure." But a related pattern that bases the dynamic component on a URL parameter or a request-time controller property opens a path where an attacker can manipulate inputs to render UI they should not see.

**When it occurs:** Any dynamic component branch that depends on values not exclusively derived from the running user's identity (`UserInfo.getUserId()`, permission set membership). If the branch depends on URL params or POST data, a tampered request can change the branch.

**How to avoid:** Two routes. (1) Replace `<apex:dynamicComponent>` with conditional rendering using `rendered="{!hasPermission}"` on static components — easier to reason about for security review. (2) Migrate the page to LWC where conditional rendering is `<template if:true={hasPermission}>` and the branch is explicit. Either way, never let request-supplied values determine which UI tree renders for permission-protected sections.

---

## Gotcha 7: `<apex:actionFunction>` rerender side effects can refresh the wrong region

**What happens:** A VF page has `<apex:actionFunction name="refreshOpps" rerender="oppList"/>` and a `commandButton` with `rerender="accountSummary"`. JS calls `refreshOpps()` after an action; the team assumes the targeted opps list updates. In practice, view state is shared, the controller property backing `accountSummary` mutates as a side effect of the action, and on the next button press the summary shows stale data.

**When it occurs:** Pages with multiple rerender targets that share controller state. The platform serializes view state on every postback; a partial rerender refreshes the visible markup but the underlying controller properties still mutate based on whatever the action method did.

**How to avoid:** Treat rerender as a UI-paint hint, not a state isolation mechanism. Audit action methods to ensure they only mutate the state that the rerendered region depends on. For complex pages, this is a common reason to migrate to LWC, where component boundaries are real isolation rather than DOM hints.

---

## Gotcha 8: Controller extension visibility — extension classes inherit the standard controller's record context but not its FLS guarantees

**What happens:** A page declares `<apex:page standardController="Account" extensions="MyExtension">`. The team assumes "standard controller enforces FLS, the extension inherits that." The extension queries Account fields directly (`[SELECT Hidden_Field__c FROM Account WHERE Id = :stdCtrl.getId()]`) and returns them via getters bound to `<apex:outputText>`. FLS is not enforced.

**When it occurs:** Whenever an extension performs its own SOQL rather than relying on the standard controller's automatic field binding. The standard controller enforces FLS only on fields it manages directly (those bound via `<apex:inputField>` / `<apex:outputField>`). Extension queries are independent Apex and need their own enforcement.

**How to avoid:** In every extension, use `WITH USER_MODE` on extension SOQL. Treat the extension as a separate security boundary — the standard controller's protections do not transitively cover extension code paths. Static analysis tools can flag this; the bundled checker script catches the most common variants.
