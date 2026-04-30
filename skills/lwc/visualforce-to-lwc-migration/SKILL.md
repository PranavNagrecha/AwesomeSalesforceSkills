---
name: visualforce-to-lwc-migration
description: "Migrating Visualforce pages and components to Lightning Web Components: controller-to-Apex-method translation, viewstate replacement, custom URL parameter handling, PageReference-to-NavigationMixin mapping, Lightning Out coexistence, and inline VF retention strategy. NOT for new LWC development from scratch (use lwc-fundamentals) or Aura-to-LWC migration (use aura-to-lwc-migration)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "How do I migrate a Visualforce page with a custom controller to LWC?"
  - "What replaces viewstate when moving from VF to LWC?"
  - "How do I keep my VF page available during a phased LWC migration?"
  - "Replace apex:repeat / apex:pageBlockTable in LWC"
  - "Convert PageReference redirects to NavigationMixin"
  - "Pass URL parameters to an LWC the way I did with VF page parameters"
tags:
  - visualforce
  - lwc-migration
  - controller-translation
  - lightning-out
  - navigationmixin
  - pagereference
inputs:
  - "Inventory of Visualforce pages with controller type (standard, custom, extension), URL parameters consumed, and embedded surfaces (Lightning App Builder, button override, embedded list view)"
  - "Whether the page uses viewstate (form posts) or is read-only"
  - "Whether the page renders as PDF, sends email, or has any non-standard `renderAs` / `contentType` attribute"
  - "Required browser surfaces: Lightning Experience, Salesforce mobile app, Experience Cloud, Classic, embedded in another VF page"
outputs:
  - "LWC bundle (`.js`, `.html`, `.css`, `.js-meta.xml`) replacing the Visualforce page"
  - "Apex `@AuraEnabled(cacheable=true|false)` methods replacing controller `getX()` / action methods"
  - "NavigationMixin call sites replacing `PageReference` redirects"
  - "Lightning Out wrapper VF page (transitional) when LWC must run inside a remaining VF context"
  - "Migration checklist documenting every controller method, URL param, and renderAs use"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-29
---

# Visualforce to LWC Migration

This skill activates when a practitioner needs to replace a Visualforce page with a Lightning Web Component, manage coexistence between VF and LWC during phased migration, or translate VF-specific patterns (viewstate, PageReference, renderAs) to LWC equivalents.

---

## Before Starting

Gather this context before working on anything in this domain:

- Audit every URL parameter the VF page consumes from `ApexPages.currentPage().getParameters()` — these become `@api` properties or `CurrentPageReference` query-param reads on the LWC side.
- Confirm the page's render mode. `renderAs="pdf"`, custom `contentType`, or email-template embedding are NOT replaceable by LWC — those VF pages must stay or move to Apex-driven document services.
- List every action method (`<apex:actionFunction>`, `<apex:commandButton>`) and its return type. Action methods that return `PageReference` need the navigation translated; methods that mutate state via viewstate need to be re-architected as imperative Apex calls with explicit DTOs.

---

## Core Concepts

### 1. Visualforce-to-LWC Capability Map

| Visualforce Capability | LWC Equivalent | Migration Notes |
|---|---|---|
| `<apex:page controller="Foo">` | LWC `@AuraEnabled` Apex methods invoked via `@wire` or imperative call | No persistent server-side controller state; every call is stateless |
| Viewstate (form posts) | Client-side reactive state in JS + explicit Apex DML on submit | Eliminate hidden state; design DTOs for the Apex method signature |
| `<apex:repeat>` / `<apex:pageBlockTable>` | Template `for:each` or `<lightning-datatable>` | Use `lightning-datatable` for sortable / inline-edit tables |
| `<apex:inputField>` | `<lightning-input-field>` inside `<lightning-record-edit-form>` | Field-Level Security and validation rules apply automatically |
| `<apex:commandButton action="{!save}">` | Imperative Apex from JS, `try/catch`, refresh wire with `refreshApex` | No automatic page rerender — manage UI state explicitly |
| `<apex:actionFunction>` | Imperative Apex method import + JS call | No more "named JavaScript function that posts the form" |
| `PageReference` redirects | `NavigationMixin.Navigate({ type, attributes })` | URL-based; no controller round-trip |
| `<apex:outputText escape="false">` | Avoid; sanitize and use template binding | LWC sanitizes by default; bypassing is a security risk |
| `renderAs="pdf"` | NOT migratable — keep VF, or move to Apex `Blob.toPdf` / 3rd-party | Document rendering is not an LWC capability |
| `<apex:includeScript>` / `<apex:stylesheet>` | Static Resource via `loadScript` / `loadStyle` from `lightning/platformResourceLoader` | Loaded async; respect Locker/Lightning Web Security |

### 2. Where the VF Page Lives Determines the Target Surface

LWC `js-meta.xml` `targets` must match the surface the VF page was used on. Wrong target metadata = component does not appear.

| VF Embedding Surface | Required LWC `target` | Notes |
|---|---|---|
| Custom Tab | `lightning__Tab` | Same UI position as VF custom tab |
| Object record page | `lightning__RecordPage` | Recordpage replacement; expose `@api recordId` |
| App home page | `lightning__HomePage` | App Builder page only |
| Experience Cloud page | `lightningCommunity__Page` + `lightningCommunity__Default` | Site builder page; cookies/guest user constraints differ |
| Quick Action override | `lightning__RecordAction` + actionType `ScreenAction` in `js-meta.xml` | Record context auto-injected |
| Button URL / "View Source" | NOT a direct surface — requires Quick Action wrapping | Old VF buttons need a parallel migration path (see custom-button-to-action-migration) |

### 3. Server Communication Translation

Every VF page communicated with its controller via the form post (`<apex:form>`) or AJAX (`<apex:actionFunction>`). LWC has two patterns and they are not equivalent:

| Pattern | When to use | Cacheable? | Reactive on data change? |
|---|---|---|---|
| `@wire(getData, { recordId: '$recordId' })` | Read-heavy; want automatic refresh on dependency change | Yes (`cacheable=true`) | Yes — wire re-fires when input properties change |
| Imperative `import getData from '@salesforce/apex/X.getData'` then `await getData({ recordId })` | Read on user trigger or write operations | Optional | No — caller must re-invoke |
| `LightningDataService` via `lightning/uiRecordApi` | Standard CRUD on a single record without writing Apex | Yes | Yes — auto-refresh across components |

VF developers tend to write a single `getController()` Apex method that returns a wrapper of everything the page needs. In LWC this is acceptable for one screen, but split if the screen has independently refreshing zones — each zone gets its own wire so refresh is granular.

### 4. Lightning Out as a Transitional Bridge

Lightning Out lets you embed an LWC into a remaining Visualforce page. This is the canonical mechanism for partial migration when the page surface itself cannot move yet (e.g., embedded in an external system iframe, or referenced by a hardcoded button URL).

The reverse — embedding VF inside LWC — is done via `<iframe src="/apex/MyVfPage">` and is a code smell in production. Use it only as a strict transitional measure with a tracked removal date.

---

## Common Patterns

### Pattern 1: Read-Only VF Page → Wired LWC

**When to use:** A VF page renders read-only data computed by the controller (dashboards, account summaries, KPIs).

**How it works:**
1. Convert each controller `get` property into an `@AuraEnabled(cacheable=true)` static method returning a serializable DTO.
2. In the LWC, wire each method: `@wire(getKpiSnapshot, { recordId: '$recordId' }) snapshot;`.
3. Render via template binding (`{snapshot.data.totalRevenue}`).
4. Add `<lightning-spinner>` for the loading state and an error template branch for `snapshot.error`.
5. Replace the VF page with the LWC on the surface (App Builder page, custom tab).

**Why not the alternative:** Calling the controller imperatively defeats the wire's caching and refresh-on-input semantics. Wire is the right primitive for read-only views.

### Pattern 2: Form-Posting VF Page → LightningRecordEditForm

**When to use:** A VF page used `<apex:inputField>` in an `<apex:form>` to create or edit a record.

**How it works:**
1. Replace the VF page with `<lightning-record-edit-form object-api-name="Account">` containing `<lightning-input-field>` for each field.
2. Handle `onsuccess` and `onerror` events instead of a custom `save()` controller method.
3. Use `<lightning-record-form>` (single-line) when the layout follows the page layout assignment exactly — eliminates field listing entirely.
4. Field-Level Security, validation rules, and field-level help text are honored automatically.

**Why not the alternative:** Writing a custom `@AuraEnabled` save method that calls `update record` re-implements features (FLS, validation rules, lookup search UI) that `lightning-record-edit-form` provides for free. Only build a custom Apex save when business logic spans multiple records or requires a transaction boundary the form can't express.

### Pattern 3: PDF / Email VF Page Stays as Visualforce

**When to use:** The VF page uses `renderAs="pdf"`, is the body of `Messaging.SingleEmailMessage.setTemplateId()`, or sets a custom `contentType` for download.

**How it works:**
1. Do NOT migrate. LWC has no equivalent for these capabilities.
2. If the LWC ecosystem needs to trigger the PDF, build an Apex `@AuraEnabled` method that calls `Blob result = pageRef.getContentAsPDF()` or `getContent()` and returns a Base64 string the LWC can save via the browser.
3. Document the retained VF page in the migration log with rationale "renderAs not portable."
4. Apply Visualforce Security Best Practices (CRUD/FLS checks, escaping) — these pages remain a security surface even when the rest of the org moves to LWC.

**Why not the alternative:** Re-implementing PDF generation in JavaScript (jsPDF, html2pdf) loses Salesforce's server-side rendering, breaks Locker/LWS compatibility, and inflates bundle size. Server-side `getContentAsPDF()` is the right primitive.

### Pattern 4: Lightning Out Coexistence for Hardcoded VF URLs

**When to use:** Buttons, email links, or external systems link to a VF page URL that cannot be changed in the migration window.

**How it works:**
1. Build the LWC.
2. Create a thin VF page that uses `$Lightning.use()` and `$Lightning.createComponent()` to mount the LWC inside Lightning Out.
3. The original VF URL now serves the LWC inside a Lightning Out container.
4. Track the wrapper as transitional debt with a removal date when the upstream caller is updated to navigate directly.

**Why not the alternative:** Rewriting every external caller to a new URL is often blocked by external system release cycles. Lightning Out preserves the contract while modernizing the implementation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| VF page is read-only and lives on App Builder page | Direct rewrite to wired LWC | Wire pattern matches read-only nature; no viewstate to translate |
| VF page is a CRUD form on one object | Replace with `lightning-record-form` or `lightning-record-edit-form` | Page layout / FLS / validation handled natively |
| VF page uses `renderAs="pdf"` | Keep as VF; do not migrate | LWC has no PDF rendering capability |
| VF page is the body of an email template | Keep as VF; address as separate email migration | Email rendering surface is not LWC-eligible |
| VF page is invoked by a hardcoded URL from outside the org | Lightning Out wrapper VF page that mounts the new LWC | Preserves URL contract |
| VF page has heavy custom JavaScript with jQuery / Bootstrap | Audit JS first; many libs violate LWS — refactor before migrating | Lightning Web Security restrictions can block libs that worked in VF |
| VF page is a button override for a standard action | Replace with Quick Action launching the LWC | See `admin/custom-button-to-action-migration` |
| VF page uses inline `<apex:outputText escape="false">` | Re-architect to render via template binding (sanitized) | Bypassing escaping in VF is a known XSS surface; do not preserve |
| VF page sets viewstate via `<apex:inputHidden>` for tracking | Move tracking to a transient client-side property in the LWC | Viewstate has no LWC equivalent and is not needed |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory the VF page surface.** List the `apex:page` attributes (`controller`, `extensions`, `standardController`, `renderAs`, `contentType`, `tabStyle`), every `apex:` markup tag in use, every controller method (its return type and DML behavior), every URL parameter consumed, and every static resource referenced.
2. **Decide migrate vs retain.** Apply the Decision Guidance table. PDF, email-body, custom-content-type, and externally-linked URL pages are migration *partial* candidates; everything else is a full migration target.
3. **Translate controller to `@AuraEnabled` methods.** For each `get` property, expose a `@AuraEnabled(cacheable=true)` static method. For each action method, expose an `@AuraEnabled(cacheable=false)` method that returns explicit DTOs (no `PageReference`). Include `with sharing` and explicit FLS checks (`Security.stripInaccessible` or `WITH SECURITY_ENFORCED` in SOQL).
4. **Scaffold the LWC bundle.** Create `<componentName>.js`, `.html`, `.css`, and `.js-meta.xml`. Set `targets` to match the original VF surface. Expose `@api` properties for any URL parameter the VF page received.
5. **Wire data + handle navigation.** Use `@wire` for read-only data, imperative for writes. Replace `PageReference` returns with `this[NavigationMixin.Navigate]({ type, attributes })`. Replace `apex:commandButton` action calls with JS event handlers that invoke the imperative method and then `refreshApex(this.wiredHandle)` on success.
6. **Verify parity.** Diff the rendered output against the VF page on identical data. Confirm FLS behavior (a user without field access must see the same hidden state). Test all URL parameter entry points.
7. **Decommission the VF page.** Once stable, remove the VF page from the App Builder / tab / button override. Delete the controller class only after confirming no other VF page still uses it. Keep a Lightning Out wrapper if external callers still hit the URL.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every VF controller `get` property has a corresponding `@AuraEnabled(cacheable=true)` method
- [ ] Every controller action method has been re-architected as an imperative `@AuraEnabled` method returning a serializable DTO (no `PageReference`)
- [ ] All `with sharing`, CRUD, and FLS enforcement is explicit in the new Apex (`Security.stripInaccessible` or `WITH SECURITY_ENFORCED`)
- [ ] LWC `js-meta.xml` `targets` match every original VF surface (App Builder, Experience, Tab, etc.)
- [ ] All `PageReference` redirects are translated to `NavigationMixin.Navigate` calls with the correct `type` and `attributes`
- [ ] No `<apex:outputText escape="false">` patterns survived (template binding sanitizes by default)
- [ ] `renderAs="pdf"`, `contentType=...`, and email-body VF pages are explicitly retained, not migrated
- [ ] Lightning Out wrapper VF pages are documented with a removal date if any are deployed
- [ ] Loaded JS libraries pass Lightning Web Security validation (run in LWS-enabled scratch org)
- [ ] Static resources are loaded via `loadScript` / `loadStyle`, not via `<apex:includeScript>` references that no longer apply

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Viewstate is not a feature you replace — it's a coupling you eliminate.** Visualforce viewstate persists controller member variables across postbacks transparently. LWC has no server-side persistence between Apex method calls; every call is stateless. Code that depended on viewstate for tracking which row was edited, which step a wizard was on, or what the user just typed must be re-architected as explicit client-side state passed in DTOs. There is no "LWC viewstate flag" to flip.

2. **`apex:actionFunction` JavaScript names don't exist anymore.** Existing client JS that calls `myActionFn()` (auto-generated from `<apex:actionFunction name="myActionFn">`) breaks completely in LWC. There is no global JS namespace for component methods. Migration must rewrite every JS caller to import the Apex method directly and call it via async/await.

3. **`renderAs="pdf"` and email-template VF pages cannot be migrated.** These rely on the Visualforce server-side renderer (Apex `getContentAsPDF`, `Messaging.SingleEmailMessage.setTemplateId`). LWC has no equivalent. Attempting to "migrate" them leads to broken PDFs or unsendable emails. The correct outcome is to keep the VF page and document the retention.

4. **Lightning Web Security blocks JS libraries that worked under Locker.** Lightning Web Security (LWS) is the new client-side security architecture. Some third-party libraries that worked under Locker Service in Aura/VF break under LWS — particularly those that touch `window` directly, use `eval`, or manipulate cross-origin iframes. Migration must include an LWS compatibility test pass before declaring the LWC complete.

5. **`<apex:outputText escape="false">` patterns are a security trap.** VF allowed bypassing HTML escaping with `escape="false"`. Many existing pages used this for trivial reasons (rendering a `<br>` from a text area). Translating this verbatim to LWC by using `lwc:dom="manual"` or `innerHTML` recreates the XSS surface. The migration must sanitize inputs explicitly or re-render the data with safe primitives (`<lightning-formatted-text>` for line-break preservation).

6. **URL parameter access changes from `ApexPages.currentPage()` to `CurrentPageReference`.** VF reads URL parameters server-side via `ApexPages.currentPage().getParameters().get('id')`. LWC reads them client-side via `@wire(CurrentPageReference)` and accesses `pageRef.state.c__id`. The parameter name is also rewritten to add a `c__` prefix when used in App Builder pages — a hardcoded URL like `?id=123` arriving at an LWC page becomes `?c__id=123`. External callers must be updated.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC component bundle | `.js`, `.html`, `.css`, `.js-meta.xml` files replacing the Visualforce page |
| `@AuraEnabled` Apex class | Stateless service methods replacing the VF controller; `with sharing` + explicit FLS |
| Lightning Out wrapper VF page | Transitional shell that mounts the new LWC into the original VF URL |
| Migration audit log | Per-page record of every controller method, URL parameter, and renderAs use mapped to its LWC outcome (migrated / retained / refactored) |
| Updated button / tab / App Builder page | Surface configuration switched from VF to LWC reference |

---

## Related Skills

- `lwc/aura-to-lwc-migration` — Use when the source is Aura, not Visualforce; many event-translation patterns overlap
- `lwc/lwc-imperative-apex` — Use when porting `apex:actionFunction` patterns to LWC imperative calls
- `apex/apex-rest-and-aura-enabled` — Use when designing the `@AuraEnabled` service layer that replaces the VF controller
- `admin/custom-button-to-action-migration` — Use when the VF page was a button override; the button itself also needs migration
- `security/secure-coding-visualforce` — Use when the retained VF pages need a security review before sign-off
