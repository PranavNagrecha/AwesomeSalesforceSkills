---
name: visualforce-fundamentals
description: "Designing and debugging Visualforce pages: standard/custom controllers, view state management, CSRF and SOQL injection security, PDF rendering, Visualforce email templates. Use when building custom UI pages or PDF outputs on the Salesforce platform. NOT for hardening or rewriting legacy VF in LWC — use security/visualforce-security-and-modernization. NOT for migrating Classic VF email templates — use admin/classic-email-template-migration."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
tags:
  - visualforce
  - view-state
  - custom-controller
  - pdf-rendering
  - csrf
  - vf-email-templates
triggers:
  - "how to reduce view state size on a Visualforce page"
  - "Visualforce page throws too many SOQL queries error"
  - "custom controller not enforcing field-level security"
  - "generate PDF from Visualforce page in Salesforce"
  - "CSRF token mismatch on Visualforce page action"
  - "Visualforce page behaves differently in Lightning Experience"
inputs:
  - "page requirements: object(s), fields, action types (read, edit, create, PDF)"
  - "controller type decision: standard, standard list, or custom/extension"
  - "whether the page is consumer-facing (Experience Cloud) or internal"
outputs:
  - "Visualforce page markup (.page) with correct apex:* component usage"
  - "Apex controller or extension class enforcing FLS/CRUD and safe SOQL"
  - "view state analysis and transient variable recommendations"
  - "security hardening checklist (CSRF, SOQL injection, FLS)"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Visualforce Fundamentals

This skill activates when designing, building, or debugging Visualforce pages and their Apex controllers on the Salesforce platform. It covers controller architecture, view state optimization, security hardening (CSRF, SOQL injection, FLS/CRUD), PDF rendering, and Lightning Experience compatibility.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Page purpose:** Is this a data-entry form, a read-only display, a PDF output, or an email template preview?
- **Controller type needed:** Does the page operate on a single record (standard or custom controller), a list (standard list controller), or custom business logic (custom controller or extension)?
- **Lightning Experience context:** Will this page appear in LEX as a tab, record action, or override? If yes, it will run inside an iframe — classic JavaScript DOM assumptions break.
- **Security context:** Is this accessible to unauthenticated users, Experience Cloud guests, or internal employees? Guest users get no implicit record access.
- **View state budget:** Complex pages easily exceed the 170 KB limit (app_limits 264 L748). Identify large collections, binary fields, or render-dependent state early.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| How many rows and fields does the page hold between postbacks? | Gotcha 1: 170 KB view state | Which properties must be `transient` |
| Does an extension or custom controller run its own SOQL? | Gotcha 2: access mode depends on the class API version | `WITH USER_MODE` or reliance on the 67.0+ default |
| Will the page be rendered as PDF? | Gotcha 3: no JavaScript in PDF | Server-side data loading only |
| Will it run inside Lightning Experience? | Gotcha 4: separate Visualforce host | `sforce.one` navigation, no parent-frame DOM |
| Are formula, roll-up or auto-number fields on the form? | Gotcha 5: read-only fields | `<apex:outputField>` for them |
| Does `<apex:page action>` do DML or callouts? | Gotcha 6: fires on every GET | Side effects moved to POST actions |
| Do action methods read transient properties? | Gotcha 7: transient is rebuilt each request | Lazy getters that re-query |

A proper configuration sizes view state and access mode before the page ships, where "just doing it" works for an admin on ten rows and breaks for real users.

---

## Core Concepts

### Concept 1: Controller Types

Visualforce offers three controller patterns. Choosing the wrong one forces workarounds later.

| Controller Type | Use When | What You Get |
|---|---|---|
| Standard Controller | Single-record pages tied to a specific sObject | Auto data binding, standard actions (save, edit, delete, cancel), FLS enforcement on bound fields |
| Standard List Controller | Set-based pages (mass-update, list views, pagination) | `getSelected()`, `first()`, `next()`, `previous()`, `last()`, built-in pagination state |
| Custom Controller / Extension | Business logic beyond standard CRUD, cross-object data, custom actions | Full Apex control; access enforcement follows the class API version (see below) |

Extensions complement a standard controller and inherit its record context automatically. Corrected 2026-10-20: the Apex guide now says "both standard and custom controllers execute entirely in user mode, in which the object and field-level permissions of the current user are enforced" (apexdev 264 L19443-19444); classes saved at API 67.0+ run in user context by default, while at 66.0 and earlier "system mode is the default" (L11928-11929). So a custom controller saved at ≤66.0 still needs explicit `WITH USER_MODE` / `AccessLevel.USER_MODE`.

### Concept 2: View State

Every Visualforce page that uses `<apex:form>` carries a hidden `__VIEWSTATE` field on every postback. This field is encrypted and contains the serialized state of all non-transient, non-static instance variables in the controller and its extensions (transient and static variables are not transmitted, apexdev 264 L4777, L4788; "encrypted" is UNVERIFIED (2026-10-20)).

Key limits (from Salesforce Limits Quick Reference):
- **Maximum view state size: 170KB** (app_limits 264 L748). The exception name `ViewStateException` is UNVERIFIED (2026-10-20). Maximum response size is under 15 MB (L746).
- View state is round-tripped on every postback, adding latency proportional to payload size.

To control view state:
- Mark display-only collections (`List<Account>`, `List<SelectOption>`) as `transient` — they are rebuilt on the next request anyway.
- Restrict SOQL field lists to only fields the page actually renders.
- Use `<apex:actionRegion>` to limit which components participate in a postback.
- Consider JavaScript remoting (`@RemoteAction`, apexdev 264 L6245-6246) to avoid view state for read-heavy operations. Corrected 2026-10-20: there is no `<apex:remoteAction>` component.

### Concept 3: Expression Language and Component Model

Visualforce uses `{! }` expression language to bind controller data to page markup. The built-in `apex:*` components ("approximately 150" is UNVERIFIED (2026-10-20)) (input, output, form, datatable, pageBlock, etc.) handle HTML rendering, state management, and action dispatch.

Important behaviors:
- `{!fieldName}` on an `<apex:inputField>` bound to the standard controller automatically respects the field's FLS for the running user.
- Custom controller properties accessed via `{!myProperty}` show whatever the controller queried — at API ≤66.0 that query runs in system mode (apexdev 264 L11928-11929), so the author is responsible for enforcement.
- The `rendered` attribute is evaluated server-side at render time; a component with `rendered="false"` is not sent to the browser at all.
- `action` attributes on `<apex:commandButton>` and `<apex:commandLink>` must return `null` or a `PageReference` — void methods cause a page reload to the current URL.

### Concept 4: Lightning Experience Compatibility

Visualforce pages in Lightning Experience load inside an iframe with a separate domain. This means:
- `window.parent` access is blocked by the browser's same-origin policy.
- Classic JavaScript that modifies `window.location` or `parent.document` does not work.
- Salesforce provides `sforce.one.*` JavaScript APIs for LEX navigation from within VF iframes.
- CSS and SLDS styling must be added explicitly — Classic styles do not apply inside the VF iframe.

---

## Common Patterns

### Pattern 1: Custom Controller with FLS Enforcement

**When to use:** You need custom business logic and SOQL beyond what the standard controller provides.

**How it works:** Use `WITH USER_MODE` on SOQL queries ("Summer '23+" is UNVERIFIED (2026-10-20)) to enforce FLS and CRUD; at API 67.0+ user mode is already the default (apexdev 264 L11928-11929). For DML, use `Database.insert(records, AccessLevel.USER_MODE)`.

**Why not the alternative:** Omitting FLS enforcement in a custom controller is a security-review failure and exposes data to users who should not see it. The standard controller enforces FLS on bound fields automatically — custom controllers do not inherit this.

### Pattern 2: Transient Variables for Large Collections

**When to use:** Any controller property that is a list used only for display (not submitted back to the server).

**How it works:** Declare the variable `transient` in Apex. The value is recomputed each time the page loads or re-renders via a getter method, and is never serialized into view state.

**Why not the alternative:** A non-transient `List<SObject>` with 200 records can easily consume 50–80 KB of view state alone (estimate, UNVERIFIED (2026-10-20)). On complex pages with multiple lists this rapidly exceeds the 170 KB limit and the page fails in production.

### Pattern 3: PDF Rendering

**When to use:** You need to produce a formatted PDF document (invoices, contracts, reports) from Salesforce data.

**How it works:** Add `renderAs="pdf"` to the `<apex:page>` tag. Salesforce converts the HTML output to PDF (the "Flying Saucer" engine name is UNVERIFIED (2026-10-20)). Use inline CSS for layout — external stylesheets must be hosted at a public URL and are often unreliable. Use `<apex:stylesheet>` only for static resources.

**Why not the alternative:** Trying to use JavaScript PDF libraries in a VF page does not work because JS runs after the server renders the page — `renderAs="pdf"` bypasses JavaScript entirely.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard record form (edit/view) | Standard Controller + extension for custom logic | Automatic FLS, standard actions, minimal boilerplate |
| Mass-update or paginated list | Standard List Controller | Built-in pagination state, selection handling |
| Complex multi-step wizard | Custom Controller | Standard controller does not support cross-step state management |
| Read-heavy display page | JavaScript Remoting (`@RemoteAction`) | Avoids view state overhead entirely |
| PDF generation | `<apex:page renderAs="pdf">` | Native platform PDF rendering, no external dependency |
| Page in Lightning Experience | Test in LEX iframe, use `sforce.one.*` for navigation | Classic JS DOM assumptions break in iframe |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the controller type** — Confirm whether the page is single-record (standard controller), list-based (standard list controller), or custom logic (custom controller or extension). Choose the simplest option that meets the requirements.
2. **Audit SOQL in the controller** — Every query must use bind variables (not string concatenation). For custom controllers, add `WITH USER_MODE` to enforce FLS automatically, or call `Schema.sObjectType.Account.fields.Name.isAccessible()` for field-by-field checks.
3. **Audit view state** — Identify every non-transient collection or object property in the controller. Mark display-only properties `transient`. Limit SOQL field lists to only what the page renders.
4. **Harden against CSRF** — State-changing actions (DML, delete) must be triggered via POST (use `<apex:commandButton>` inside `<apex:form>`). Never invoke DML from a GET-accessible method or URL parameter action.
5. **Test in Lightning Experience** — Load the page inside LEX and verify navigation, CSS rendering, and any JavaScript calls. Replace `window.parent` DOM access with `sforce.one.*` API calls.
6. **Validate with a low-privilege user** — Run the page as a user without admin privileges. Confirm that hidden fields are not exposed via the controller and that SOQL results respect the user's record access.
7. **Run the checker script** — Execute `python3 scripts/check_visualforce_fundamentals.py --manifest-dir <metadata-path>` (add `--strict` in CI) to catch common issues automatically before deployment.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Controller SOQL uses bind variables — no string concatenation of user-controlled values
- [ ] Custom controller enforces FLS/CRUD via `WITH USER_MODE` or explicit `Schema` checks
- [ ] Display-only collections and properties are marked `transient` in Apex
- [ ] State-changing actions are POST-only (inside `<apex:form>` with `<apex:commandButton>`)
- [ ] Page tested in Lightning Experience iframe — no broken JS, navigation uses `sforce.one.*`
- [ ] Tested with a low-privilege user to confirm data is not over-exposed
- [ ] View state size verified under 170 KB (check View State Inspector in Developer Console)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **View state persists across partial postbacks** — `<apex:actionRegion>` limits which components are re-rendered, but the entire controller state is still serialized. A large non-transient property in a component outside the region still consumes view state.
2. **Standard controller FLS applies only to bound fields** — Fields accessed via `{!account.Name}` on a standard controller enforce FLS. Fields read via a custom getter that queries `Account.Name` directly do NOT enforce FLS when the class is saved at API 66.0 or earlier, where system mode is the default (apexdev 264 L11928-11929) — the Apex author must check.
3. **`renderAs="pdf"` ignores JavaScript entirely** — The PDF rendering engine does not execute JS (engine name UNVERIFIED (2026-10-20)). Pages relying on JS for layout or data loading produce blank or broken PDFs.
4. **VF iframes in LEX have a different origin** — Salesforce serves VF pages from a separate Visualforce host, in production `MyDomainName--PackageName.vf.force.com` (apexref 262 L226384-226385); corrected 2026-10-20 from "a `visualforce.com` subdomain" (that form applies only with stabilized hostnames, api_meta 264 L125879-125885). Cross-origin restrictions apply; `window.parent.location` access will throw a security error.
5. **`<apex:inputField>` on a formula field** — Formula fields are read-only; the claim that binding them to `<apex:inputField>` produces a DML exception on save is UNVERIFIED (2026-10-20). Use `<apex:outputField>`.
6. **Transient variables are null on initial page load** — The first render always reconstructs transient values via their getter. If the getter relies on view-state variables not yet populated (e.g., a record ID passed via URL), initialize defensively with null checks.
7. **Page actions on GET are CSRF-vulnerable** — If a page's `action` attribute on `<apex:page>` triggers DML (e.g., `action="{!doSomething}"`), a crafted URL can trigger that DML without a form submission. Reserve DML for form-submitted actions only.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Visualforce page markup | `.page` file with correct `apex:*` component structure, `renderAs` if PDF |
| Apex controller or extension | Class with FLS-safe SOQL, transient declarations, POST-only action methods |
| View state analysis | List of non-transient properties with estimated sizes and `transient` recommendations |
| Security findings | CSRF risk points, SOQL injection paths, FLS gaps with recommended fixes |

---

## Related Skills

- `apex/soql-security` — SOQL injection and FLS/CRUD enforcement patterns that apply directly to Visualforce custom controllers
- `apex/governor-limits` — Bulkification and query limits for controller queries that execute on page load or postback
- `apex/continuation-callouts` — Long-running HTTP callouts from Visualforce action methods using the Continuation pattern
