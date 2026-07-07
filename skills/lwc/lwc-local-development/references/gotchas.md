# Gotchas — LWC Local Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `@api`, `@wire`, and `.js-meta.xml` edits don't hot-reload

**What happens:** you add a public property or change a `@wire` and save, but the preview shows
no change — it looks like your edit did nothing or the component is broken.

**When it occurs:** the change falls in the manual-reload category — new `@api` properties or
methods, wire adapter modifications (config, imports, `@wire` decorator, GraphQL queries), a
newly imported `@salesforce` scoped module, or any `.js-meta.xml` update.

**How to avoid:** for single-component preview, refresh the browser page; for app/site preview,
run `sf project deploy start` for the changed metadata and restart the server. Template, CSS,
and non-API JS-method edits do hot-reload — but these categories don't.

---

## Gotcha 2: Aura components silently don't preview

**What happens:** a component doesn't appear in the preview and there's no obvious error.

**When it occurs:** the component is an Aura component, or the app/site mixes Aura and LWC.
"Live Preview only lets you preview Lightning web components. You can't use it to test Aura
components in your app or site preview." Live Preview renders the LWC parts and omits Aura.

**How to avoid:** don't reach for Live Preview to iterate on Aura — deploy and test it in the
org. Migrating the component to LWC is the durable fix.

---

## Gotcha 3: Mobile preview fails without the native SDK

**What happens:** `sf lightning dev app --device-type ios` (or `android`) errors or can't launch
a simulator.

**When it occurs:** Xcode (iOS) or Android Studio (Android) isn't installed. Mobile app preview
depends on the native mobile SDKs; the CLI also prompts to install the Salesforce mobile app if
it's missing.

**How to avoid:** install Xcode from the Mac App Store (iOS) or Android Studio from
developer.android.com/studio (Android) before using `--device-type`. Experience LWR sites
preview on desktop only — there's no mobile site preview.

---

## Gotcha 4: Previewing against production

**What happens:** you point Live Preview at a production org and it works — but you've pulled
production data and metadata into a local server.

**When it occurs:** the `--target-org` is a production org. Live Preview technically supports
production, sandbox, and scratch orgs, but Salesforce recommends sandbox/scratch only.

**How to avoid:** target a sandbox or scratch org. Treat a production `-o` as a review red flag.

---

## Gotcha 5: Assuming single-component preview is GA everywhere / conflating it with testing APIs

**What happens:** a plan states "Local Dev single-component preview is GA" for a Winter '26 org,
or bundles it with the "unified testing API."

**When it occurs:** single-component preview (`sf lightning dev component`) was **Beta as of
Winter '26** (the release that added platform-module access) and reached **GA as "Single
Component Live Preview" the week of April 13, 2026**. The Winter '26 "unified testing" work
(Test Discovery / Test Runner APIs) is a **separate** capability scoped to Apex and Flow tests —
it has nothing to do with LWC preview.

**How to avoid:** state the single-component maturity precisely per the target release, and keep
the Apex/Flow testing APIs out of any LWC local-development guidance.
