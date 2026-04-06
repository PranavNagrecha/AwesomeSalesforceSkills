# Gotchas — Visualforce Fundamentals

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: View State Is Encrypted and Round-Tripped — Not Just Stored

**What happens:** Every postback (form submit, commandButton click, actionFunction call) sends the entire `__VIEWSTATE` field to the server and back. Even if a user never notices, the 170 KB limit applies per-request, and exceeding it throws a `ViewStateException` that breaks the page entirely.

**When it occurs:** Pages with large non-transient collections, multiple controller extensions each holding their own state, or pages that accumulate data across a multi-step flow. The limit is invisible in developer testing because small data sets rarely trigger it — it surfaces in production with real record volumes.

**How to avoid:** Use the View State Inspector in the Developer Console (enable via the Developer Console menu) to see the exact size contribution of each controller property. Mark display-only lists and maps as `transient`. Use `<apex:actionRegion>` to isolate postbacks to specific components. Consider JavaScript Remoting for read-heavy data that does not need to round-trip.

---

## Gotcha 2: Standard Controller FLS Does Not Extend to Custom Getter Methods

**What happens:** When a standard controller is used, bound fields (e.g., `{!account.Industry}` on `<apex:inputField>`) automatically enforce FLS for the running user. However, if a controller extension queries the same object in a custom getter method (e.g., `[SELECT Industry FROM Account WHERE Id = :recordId]`), that query result does NOT automatically enforce FLS — the extension method runs in Apex and returns the raw data.

**When it occurs:** Pages that mix standard controller bindings with extension methods that perform their own SOQL to enrich the page with additional fields or related data.

**How to avoid:** Add `WITH USER_MODE` to all SOQL in extension and custom controller methods. This ensures the database enforces FLS and CRUD for the running user before returning results. Available from Summer '23 onwards.

---

## Gotcha 3: `renderAs="pdf"` Completely Ignores JavaScript

**What happens:** When `<apex:page renderAs="pdf">` is set, Salesforce renders the page HTML server-side and passes the raw HTML to the Flying Saucer PDF engine. Flying Saucer does not execute JavaScript. Any page behavior that depends on JS (dynamic content, JS-based charting, third-party libraries, jQuery DOM manipulation) will be absent or broken in the PDF output.

**When it occurs:** Developers port an existing Visualforce page to PDF by adding `renderAs="pdf"` without auditing JS dependencies. The preview in a browser looks correct, but the PDF is blank or missing sections.

**How to avoid:** Remove all `<script>` blocks from PDF page variants. Use server-side Apex to populate all data before render. Use inline `<style>` CSS for layout — external stylesheets from `<apex:stylesheet>` referencing static resources work, but CDN URLs are unreliable in the PDF renderer environment.

---

## Gotcha 4: Visualforce Pages in LEX Load in a Cross-Origin iframe

**What happens:** In Lightning Experience, Visualforce pages are served from a `*.visualforce.com` subdomain (or a custom domain if configured), not from the `*.salesforce.com` Lightning host domain. The browser treats these as different origins. Any JavaScript in the VF page that tries to access `window.parent.location`, `window.top.document`, or modify the outer Lightning frame DOM will throw a `SecurityError: Blocked a frame with origin` error.

**When it occurs:** Classic VF pages migrated to LEX that used JavaScript navigation hacks (`window.location = '...'`, `parent.window.location.reload()`), modal overlays that relied on DOM access to the parent frame, or pages that used Salesforce Classic JavaScript APIs (`sforce.connection`).

**How to avoid:** Use the `sforce.one.*` JavaScript API for navigation within LEX from a VF iframe. For example, `sforce.one.navigateToSObject(recordId)` replaces `window.location = '/' + recordId`. Test every JS call in a dedicated LEX sandbox before assuming Classic behavior translates.

---

## Gotcha 5: `<apex:inputField>` Bound to a Formula or Rollup Field Throws on Save

**What happens:** `<apex:inputField>` renders an appropriate HTML input for the field's data type. When bound to a read-only field — formula, rollup summary, or auto-number — the component renders as an input, accepts user input, and then throws a `DmlException: FIELD_INTEGRITY_EXCEPTION` on the save action because the field is not writable at the database level.

**When it occurs:** Pages scaffolded by a developer who included all fields on a page without checking which fields are read-only. This is not a compile-time error and does not surface until a user attempts to save the record.

**How to avoid:** Use `<apex:outputField>` for formula, rollup, auto-number, and system-managed fields. Reserve `<apex:inputField>` for editable fields only. Check `Schema.SObjectField.getDescribe().isUpdateable()` programmatically if you need to toggle input/output dynamically based on field metadata.

---

## Gotcha 6: Page `action` Attribute Fires on Every GET Request

**What happens:** The `action` attribute on `<apex:page>` (e.g., `<apex:page action="{!init}">`) fires the referenced method on every GET request for the page, including when the page is embedded in a list view, loaded in a PDF, or accessed via a direct URL. If `init()` performs DML or has side effects, those side effects fire every time the page loads — including on refreshes.

**When it occurs:** Developers use the page `action` attribute as a one-time initialization hook, not realizing it fires on every load, not once per session. This causes duplicate record creation, repeated callouts, or unintended audit log entries.

**How to avoid:** Guard the `action` method with a check that prevents re-execution (e.g., a `Boolean alreadyRun` flag stored in view state, or a check that the record does not already exist). Better: move side-effect-free data loading to the constructor, and keep DML in response to explicit user actions (form submits) only.

---

## Gotcha 7: Transient Variables Are Null After Every Postback

**What happens:** Variables declared `transient` in Apex are not serialized into view state. This means they are `null` at the start of every request, including postbacks triggered by `<apex:commandButton>`. A transient variable set in the constructor is available on the first render but will be `null` when an action method executes after a form submit.

**When it occurs:** Developers mark a property `transient` to save view state, then try to reference it in an action method assuming it holds the value set on initial load.

**How to avoid:** Always use lazy-loaded getters for transient properties — the getter checks for null and re-queries if needed. Action methods that depend on transient data must re-fetch that data themselves, or the data must be passed via form inputs (which round-trip through view state or URL parameters).
