---
name: visualforce-security-and-modernization
description: "Use when hardening or modernizing legacy Visualforce pages — covers the platform CSRF token model and when disabling it is a security regression, view state encryption guarantees and the 170 KB ceiling, FLS/CRUD enforcement gaps on `<apex:outputField>` and on getters that return sObjects, `<apex:includeScript>` interaction with the org Content Security Policy, hosting LWC inside a VF page via `lightning:container` / `lightning-out`, and the retire-vs-harden-vs-leave-alone decision for an inventory of legacy pages. Triggers: 'should I rewrite this Visualforce page in LWC', 'CSRF protection disabled on Visualforce page is that safe', 'community user sees a field they should not on a Visualforce page', 'view state encryption is that enough for sensitive data', 'how do I host an LWC inside a Visualforce page', 'apex:dynamicComponent and apex:actionFunction safe to keep'. NOT for greenfield Visualforce architecture (use apex/visualforce-fundamentals — controller types, view state pattern selection, PDF rendering); NOT for Visualforce email template authoring (use apex/visualforce-email-templates if/when that skill is authored); NOT for general Apex security review across triggers and async (use apex/soql-security and security/secure-coding-review-checklist)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - visualforce-security-and-modernization
  - visualforce
  - csrf
  - view-state
  - fls-crud-enforcement
  - lwc-vf-interop
  - legacy-modernization
triggers:
  - "we have 80 legacy Visualforce pages and need to decide which to rewrite in LWC"
  - "is it safe to set csrfProtection=false on a Visualforce page that takes URL parameters"
  - "Customer Community user sees a salary field on a Visualforce page that admins do not flag"
  - "Visualforce page works for admins but throws view state exception in production"
  - "how do I embed an LWC inside an existing Visualforce page without rewriting"
  - "navigating from a Visualforce page to an LWC tab in Lightning Experience"
  - "should we keep apex:dynamicComponent or rewrite as conditional rendering"
  - "Visualforce controller without with sharing — does that affect FLS"
  - "apex:outputField on a formula returning a Money custom field — is FLS enforced"
inputs:
  - "Inventory of Visualforce pages in the org with usage telemetry (page views, last-modified, controller name)"
  - "Per-page security context: who can hit it (internal, partner, customer community, guest), what objects are read or written, whether GET-accessible URLs trigger DML"
  - "Org-level Content Security Policy posture (My Domain, Lightning CSP trusted sites)"
  - "Migration appetite: full LWC rewrite, harden in place, or leave alone"
outputs:
  - "Per-page disposition: rewrite to LWC / harden in place / leave alone, with rationale tied to risk × usage × maintenance cost"
  - "Hardening checklist for pages staying on Visualforce: CSRF posture, FLS enforcement on getters, controller sharing keyword, view-state-free patterns where applicable"
  - "LWC interop recipe for pages that should partially modernize (host LWC inside VF, or navigate from VF to LWC pages)"
  - "Retirement plan for pages flagged for rewrite: dependency map, deprecation banner, sunset date"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Visualforce Security And Modernization

Activate this skill when an org has a population of Visualforce pages — usually a mix of legacy admin tools, customer-facing pages on Experience Cloud, and PDF generators — and a security review or LWC migration program is forcing decisions on each one. The skill is about the *retire-vs-harden-vs-leave-alone* choice plus the security baseline for whatever stays on Visualforce. Greenfield Visualforce architecture (controller patterns, PDF, view state strategy) belongs in `apex/visualforce-fundamentals`.

---

## Before Starting

Gather this context before proposing changes to any Visualforce page:

- **Visualforce is not deprecated.** Salesforce has not announced a sunset date. Pages continue to be supported and CSRF / view state / iframe-in-LEX behaviors continue to receive platform-level fixes. Do not migrate to LWC just because LWC is newer — migrate when there is a real reason (security finding, broken UX in LEX, unmaintainable controller, performance regression). The default for a working page is *leave alone*.
- **Who hits the page matters more than what it does.** A page accessible only to System Administrators with a sharing-aware controller is low risk. The same page accessible to Customer Community users is a different security profile entirely — guest and external users get no implicit record access, and FLS gaps that would never trip an admin trip them on first load.
- **The CSRF token is on by default and you almost never want to turn it off.** Salesforce automatically embeds an anti-CSRF token in `<apex:form>` POST submissions. The `csrfProtection` page attribute exists, but disabling it is a security regression that needs a documented justification. If the team is "just trying to make a callback work," 95% of the time the right answer is to fix the callback to use POST, not to disable CSRF.
- **`with sharing` does not enforce FLS or CRUD.** It only enforces record-level sharing. A `with sharing` controller class still happily reads and returns fields the user has no FLS access to. FLS must be enforced separately — either by binding to standard-controller `<apex:inputField>` / `<apex:outputField>`, or by calling `Schema.sObjectType.X.fields.Y.isAccessible()` / using `WITH USER_MODE`.
- **View state is encrypted, but encryption is not access control.** Salesforce encrypts the `__VIEWSTATE` payload before sending it to the browser. The user cannot read or tamper with it, but anything you put in a non-transient controller property is round-tripped to that user's browser on every postback. "Encrypted" does not mean "safe to put a list of all customer SSNs in a controller property."

---

## Core Concepts

### Concept 1 — The CSRF protection model and when disabling it is a regression

Visualforce ships with anti-CSRF token protection enabled at the platform level for `<apex:form>` POST submissions. The token is automatically generated per session and verified on submit; a third-party site cannot forge a POST that performs DML on behalf of a logged-in user without the token.

What the protection does NOT cover:

- **GET-triggered actions.** A page with `<apex:page action="{!doSomething}">` where `doSomething()` performs DML is CSRF-vulnerable regardless of the form token. The action fires on a simple GET to the page URL — an attacker just embeds the URL in an `<img src>` tag on a malicious site. **Reserve the page-level `action` attribute for read-only data loading. DML belongs inside `<apex:commandButton>` actions in a form.**
- **JavaScript Remoting and `<apex:remoteAction>` calls.** These do not use the form token. They have their own session-based protection but bypass the standard CSRF flow. Treat them like any authenticated AJAX endpoint and validate inputs server-side.
- **Custom URL parameters.** If a controller reads `ApexPages.currentPage().getParameters().get('id')` and uses it to mutate data on page load, the form token is irrelevant — there is no form involved.

The `csrfProtection` page attribute on `<apex:page>` can disable the token. The defensible reasons to do so are extremely rare (e.g., a legacy page that *must* accept third-party POST submissions and uses an alternative authentication model). The non-defensible reasons that show up in real codebases include "we couldn't get an external system to send the token" — fix the integration to send the token (or move it off Visualforce) instead.

### Concept 2 — FLS enforcement on `<apex:outputField>`, `<apex:inputField>`, and getter-returned sObjects

Salesforce automatically enforces FLS on certain Visualforce bindings, but the rules are not symmetric and the gaps are where bugs live.

| Binding pattern | FLS enforced? | Notes |
|---|---|---|
| `<apex:inputField value="{!account.Name}"/>` bound to a standard controller's record | Yes | Hidden if no read access; read-only if no edit access. |
| `<apex:outputField value="{!account.Name}"/>` bound to a standard controller's record | Yes | Field is hidden if user has no read access. Empty string is rendered. |
| `<apex:outputText value="{!account.Name}"/>` | **No** | `outputText` does not check FLS. The field value is rendered regardless. |
| `<apex:outputField value="{!myCustomGetter}"/>` where the getter returns an sObject from a custom query | **No** | If the controller queries the record without `WITH USER_MODE` or explicit `isAccessible()` checks, the field is rendered regardless of FLS. |
| `<apex:repeat var="r" value="{!myList}">` then `<apex:outputField value="{!r.SensitiveField__c}"/>` | **Partial** | FLS is enforced on the *outputField* binding only if the underlying SOQL was executed with FLS enforcement. If the controller used a permissive query, the field renders even though `outputField` is the binding. |
| Formula field referenced via `<apex:outputField>` | Yes for the formula's read access, **but not for the underlying fields** | If the formula references `Salary__c` and the user has no FLS access to `Salary__c` but does have access to the formula, the formula's computed value is shown. This is documented platform behavior and a frequent surprise. |

The reliable pattern: query with `WITH USER_MODE` (Summer '23+) or `WITH SECURITY_ENFORCED` (older), bind to `<apex:inputField>` / `<apex:outputField>`, and treat `<apex:outputText>` as user-supplied display text — never use it for sObject-field output.

### Concept 3 — Modernization decision: retire vs harden vs leave alone

The default for a working page is *leave alone*. Modernization work is justified by one of these signals:

| Signal | Disposition | Rationale |
|---|---|---|
| Page is broken in Lightning Experience (cross-frame JS, classic-only CSS) and used by internal users daily | Rewrite to LWC | LEX iframe issues compound over time; a working LWC is a one-time cost. |
| Page is exposed to external users (guest, customer community) AND has FLS gaps OR uses `<apex:dynamicComponent>` for permission-driven UI | Rewrite to LWC | LWC has a stronger security default (`Lightning Locker`, manifest-declared permissions). Hardening VF for external surfaces is high-effort and easy to get wrong. |
| Page is admin-only, internal-network, low-traffic, controller is sharing-aware, no security findings | Leave alone | The migration ROI is negative. |
| Page is a PDF generator using `renderAs="pdf"` | Leave alone | LWC has no PDF rendering equivalent — a rewrite either keeps the VF page or introduces an external PDF service. |
| Page uses `<apex:actionFunction>` to call a controller method from JS, doing DML | Harden in place | The pattern is dated but the security model is sound if FLS and CSRF are correct. Migrating the pattern alone is not worth a rewrite. |
| Page uses `<apex:dynamicComponent>` for permission-driven branching | Rewrite to LWC | `<apex:dynamicComponent>` is hard to reason about for security review and has been overtaken by simple conditional rendering in LWC. |

The output of this decision pass is a per-page label — `rewrite-lwc`, `harden-in-place`, or `leave-alone` — plus a sunset date for the rewrite candidates. Implement in batches; do not attempt a full-org migration in one quarter.

### Concept 4 — Visualforce + LWC interop

Two interop directions matter, and they have different mechanics:

- **Hosting an LWC inside a Visualforce page.** Use `<apex:includeLightning/>` once on the page, then a `<div id="container"/>` placeholder, then call `$Lightning.use("c:MyApp", function() { $Lightning.createComponent("c:myLwc", {...}, "container", function(cmp) { ... }); })` from JS. This is the documented "Lightning Out" pattern and works for both internal users and Experience Cloud sites with the right configuration. The LWC runs inside Locker / Lightning Web Security and gets its own session.
- **Navigating from a Visualforce page to an LWC tab.** The navigation API is `sforce.one.navigateToURL()` for relative URLs and `sforce.one.navigateToSObject()` for record pages. These are LEX-only — they do not work in Salesforce Classic. From within a VF page in LEX, `window.location` does not behave correctly (the iframe origin is `*.visualforce.com`, not the Lightning host), so always prefer the `sforce.one` API for navigation.

The interop pattern that does NOT work cleanly: passing complex objects between the host VF controller and an embedded LWC. The bridge is JS-side; serialize at the boundary, do not assume Apex-typed objects survive.

---

## Common Patterns

### Pattern 1 — Hardening a CSRF-disabled page back to default

**When to use:** Audit finds `csrfProtection="false"` on a page and the original justification is "needed for the integration." 95% of the time the integration can be fixed.

**How it works:**
1. Identify what the page is doing on POST. If it is taking submissions from a third-party system, capture the integration spec.
2. Re-enable CSRF protection (remove `csrfProtection="false"` or set it to `"true"`). Verify the third-party submission now fails.
3. Make the third-party system either (a) hit a Salesforce REST endpoint with proper OAuth instead of the VF page, or (b) load the VF page first via GET to obtain the form token, then submit. Option (a) is almost always the right answer for any submission newer than 2018.
4. If neither is feasible, the next-best option is moving the endpoint to an Apex REST class (`@RestResource`) with explicit authentication — VF pages are not a good integration surface in 2026.

**Why not the alternative:** Leaving CSRF disabled means an attacker who can convince a logged-in user to load a malicious page can submit arbitrary DML on their behalf. The risk is real and the remediation is documentation-bounded.

### Pattern 2 — Adding FLS guards to a custom-controller getter

**When to use:** Audit finds a VF page where `{!myCustomMethod}` returns an sObject and the underlying controller does `[SELECT Salary__c FROM Employee WHERE Id = :id]` without `WITH USER_MODE`. External users see the field.

**How it works:** Switch the SOQL to `WITH USER_MODE`:

```apex
public Employee__c getEmployee() {
    if (this.cachedEmployee != null) return this.cachedEmployee;
    this.cachedEmployee = [
        SELECT Id, Name, Salary__c
        FROM Employee__c
        WHERE Id = :this.empId
        WITH USER_MODE
        LIMIT 1
    ];
    return this.cachedEmployee;
}
```

`WITH USER_MODE` enforces both CRUD and FLS for the running user — fields the user cannot read are returned as `null`. Combined with `<apex:outputField>` binding, the field will not render at all for users without read access.

**Why not the alternative:** A `with sharing` class still returns FLS-restricted fields; the keyword only governs records. `Schema.sObjectType.X.fields.Y.isAccessible()` works but is verbose and easy to miss for the 17th field.

### Pattern 3 — Hosting an LWC inside an existing Visualforce page (incremental modernization)

**When to use:** A 2,000-line VF page does one thing well that the team needs to modernize incrementally — e.g., the data table at the top — without rewriting the whole page.

**How it works:**

```html
<apex:page sidebar="false">
    <apex:includeLightning/>
    <div id="lwc-container"></div>
    <script>
        $Lightning.use("c:MyEmbedApp", function() {
            $Lightning.createComponent(
                "c:myDataTable",
                { recordIds: "{!recordIdsJson}" },
                "lwc-container",
                function(cmp) { /* component ready */ }
            );
        });
    </script>
</apex:page>
```

Where `c:MyEmbedApp` is a Lightning Out app (`.app` file with `<aura:application access="GLOBAL" extends="ltng:outApp">`), and `c:myDataTable` is the LWC. The LWC runs under Lightning Web Security; Apex calls from inside it use `@AuraEnabled` methods, not the host VF controller.

**Why not the alternative:** Rewriting a 2,000-line VF page in one shot is high-risk and high-cost. Lightning Out lets you replace one component at a time. Eventually the VF shell is empty and can be retired.

---

## Recommended Workflow

1. **Inventory.** Enumerate every Visualforce page in the org with: usage count (last 90 days), last-modified date, controller name, audience (internal / partner / community / guest), and whether it is `renderAs="pdf"`. Run the bundled `scripts/check_visualforce_security_and_modernization.py` against your retrieved metadata to flag the structural risks (CSRF disabled, controller without `with sharing`, getter returning sObject in a non-USER_MODE class).
2. **Triage.** Apply the decision table in Core Concept 3. Tag every page `rewrite-lwc`, `harden-in-place`, or `leave-alone`. Most should be `leave-alone` — modernization work is justified per page, not orgwide.
3. **Harden the `harden-in-place` set.** For each: re-enable CSRF if disabled, verify FLS enforcement on every getter that returns an sObject, confirm controller is `with sharing`, audit `<apex:page action>` for DML, replace `<apex:outputText>` with `<apex:outputField>` for sObject fields. Run the checker after each round.
4. **Plan the `rewrite-lwc` set.** Map LWC equivalents for each VF feature (component decomposition). For pages doing PDF, decide whether the rewrite keeps a slim VF wrapper just for `renderAs="pdf"`. Set sunset dates 3–6 months out and add a deprecation banner to the existing page (`<apex:outputPanel>` with a notice).
5. **Implement Lightning Out interop where helpful.** If a page is too big to rewrite at once, embed LWCs incrementally using the pattern in Common Pattern 3. Track the proportion of the page that is now LWC vs legacy VF; the page is ready to retire when the VF shell is empty.
6. **Retire and remove.** Once the LWC equivalent is live and adopted (verify via login/usage metrics), set the original VF page to `availableInTouch="false"` and remove from any quick action / button references. Wait one release, then delete.
7. **Re-measure.** Re-run the inventory and checker quarterly. The set of `leave-alone` pages will shift over time as audiences change (e.g., a page suddenly exposed to a new community license type joins the harden-or-rewrite list).

---

## Related Skills

- `apex/visualforce-fundamentals` — controller architecture, view state optimization, PDF rendering, LEX iframe basics. Use that skill for greenfield VF and basic security; use *this* skill when the question is about an existing page's disposition.
- `apex/soql-security` — SOQL injection, `WITH USER_MODE` semantics, FLS/CRUD enforcement at the query layer. Direct dependency for hardening custom-controller queries.
- `security/secure-coding-review-checklist` — broader Apex security review including open-redirect, IDOR, and CSRF context for non-VF endpoints.
- `lwc/lwc-security` (if/when authored) — LWC-side security model that the rewrite targets land in.
- `security/my-domain-and-session-security` — My Domain configuration that affects VF iframe origin, session sharing, and CSP behavior.
