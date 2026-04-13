# Gotchas — Analytics Embedded Components

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `wave-wave-dashboard-lwc` and `wave-community-dashboard` Are NOT Interchangeable

**What happens:** Using `wave-community-dashboard` on a Lightning App Builder page (record page, app page, home page) causes the component to either not appear in the component palette or render as a blank area with no visible error. The inverse — attempting to use `wave-wave-dashboard-lwc` on an Experience Cloud page — results in the component not appearing in Experience Builder's component panel.

**When it occurs:** Any time the wrong component is used for the surface type. The two components look nearly identical in documentation and share similar attributes, making it easy to use the wrong one. This surfaces immediately at design time if the component is missing from the palette, or at runtime if a custom LWC wraps the wrong component.

**How to avoid:** Match the component to the surface — not to the dashboard type or Analytics app. Lightning App Builder pages (lightning__RecordPage, lightning__AppPage, lightning__HomePage) require `wave-wave-dashboard-lwc`. Experience Builder pages require `wave-community-dashboard`. Enforce this in code review and in LWC js-meta.xml target declarations.

---

## Gotcha 2: `dashboard` (18-char ID) and `developer-name` Are Mutually Exclusive

**What happens:** Setting both the `dashboard` attribute (the 18-character 0FK... record ID) and the `developer-name` attribute on the same `wave-wave-dashboard-lwc` component does not throw an error. The component silently uses `dashboard` (the ID) and ignores `developer-name`. The dashboard appears to load correctly, masking the configuration error.

**When it occurs:** This becomes a production problem when a dashboard is built in a sandbox (where the ID is one value) and deployed to production (where the ID differs). If the developer mistakenly set both attributes and assumed `developer-name` was active, the component in production will try to load a dashboard by the sandbox ID — which does not exist in production — and fail.

**How to avoid:** Always use exactly one identifier. For org-portable configurations (the recommended approach for anything that moves between sandbox and production), use `developer-name` only. Reserve the `dashboard` ID approach for quick prototyping or when the developer name is not known. Treat having both attributes set as a configuration error and flag it in code review.

---

## Gotcha 3: Invalid `state` JSON Causes Silent Failure

**What happens:** The `state` attribute on `wave-wave-dashboard-lwc` and `wave-community-dashboard` accepts a JSON string that encodes dashboard filter and selection state. If the JSON string is malformed (unclosed bracket, trailing comma, unquoted key, etc.), the dashboard loads in its default state — ignoring the entire `state` value — with no error in the UI or browser console.

**When it occurs:** Most commonly when the JSON state string is built by string concatenation in JavaScript rather than via `JSON.stringify()`. Also occurs when the state string is hardcoded and contains a syntax error that goes undetected until runtime.

**How to avoid:** Always build state objects as JavaScript objects and serialize them with `JSON.stringify()` before passing to the `state` attribute. If the state string is received from an external source, validate it with `JSON.parse()` inside a try/catch before passing it to the component. Never concatenate JSON strings manually.

```javascript
// Correct pattern
const stateObj = {
    myFilterStep: { selections: [this.selectedAccountId] }
};
this.dashboardState = JSON.stringify(stateObj);
```

---

## Gotcha 4: `record-id` Passes Context — It Does NOT Auto-Filter

**What happens:** Setting the `record-id` attribute with the current record's 18-character ID does not automatically scope the dashboard data to that record. The dashboard loads and shows its default global data view unless the dashboard designer has explicitly added filter bindings or step configurations in Analytics Studio that consume the passed record ID.

**When it occurs:** This is a common assumption mismatch. The dashboard embedding component delivers the record ID to the dashboard runtime; the dashboard itself must be configured to use it. If the dashboard was not designed with that binding, the `record-id` attribute is silently ignored.

**How to avoid:** Before embedding, confirm with the dashboard designer that the dashboard has a filter or binding that reads the incoming `record-id` value. Document this dependency in the embedding component's README or comments. When building both the embedding LWC and the dashboard, validate the binding end-to-end with a test record that has distinct data.

---

## Gotcha 5: Embedding Direction Confusion — Dashboard-in-Page vs LWC-in-Dashboard

**What happens:** The two embedding directions — embedding a dashboard into a Lightning/Experience page (Pattern A) and embedding a custom LWC inside a dashboard canvas (Pattern B) — share no setup steps. Practitioners who confuse the two directions waste significant time trying to use `analytics__Dashboard` js-meta.xml targets to get a dashboard onto a record page, or trying to drag `wave-wave-dashboard-lwc` into the Analytics dashboard widget picker (where it does not appear).

**When it occurs:** Most often when a requirement is described loosely — "I need to embed analytics into this page" vs "I need to embed this component into the analytics dashboard." Both use the word "embed" but are entirely different implementation paths.

**How to avoid:** Clarify the direction before writing any code. Ask: "Is the Analytics dashboard the content being placed on a Salesforce page, or is a custom LWC the content being placed inside an Analytics dashboard?" The answer determines whether to use `wave-wave-dashboard-lwc`/`wave-community-dashboard` (Pattern A) or the `analytics__Dashboard` js-meta.xml target (Pattern B).
