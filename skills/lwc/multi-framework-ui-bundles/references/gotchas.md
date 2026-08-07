# Gotchas — Multi-Framework UI Bundles

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The gate is the release, not the org type — and the beta-era rules are gone

**What happens:** a team is told (by an assistant, a stale blog post, or an internal doc
written during the beta) that Multi-Framework cannot ship to production, and rewrites the app
in LWC or postpones the release. Multi-Framework went **GA in July 2026** and deploys to
production, sandbox, Developer Edition, and scratch orgs.

**When it occurs:** any plan sourced from the April 2026 beta announcement rather than the
July 2026 GA announcement. The beta restrictions — sandboxes/scratch orgs only, English
default language only, no production deploys — **no longer apply**.

**How to avoid:** check the **release** of the target org, which is the actual gate:
Summer '26 (API 67.0) or later. Also check the SDK package name, because the same staleness
usually travels with it (`@salesforce/sdk-data` is the beta package; `@salesforce/platform-sdk`
is GA). Keep the qualifiers that survived GA: the ACC Web SDK is still Beta, and Lightning-page
micro-frontend embedding is still a pilot.

---

## Gotcha 2: Deploy succeeds only after the Setup toggle

**What happens:** the UIBundle deploy or app load fails in an org where the same source
worked elsewhere.

**When it occurs:** the target org never had the Salesforce app domain enabled under
**React Development with Salesforce Multi-Framework** in Setup. The Metadata API reference
calls this out as an explicit prerequisite for using the type.

**How to avoid:** make the Setup enablement step one of the environment-preparation tasks for
every org (each scratch org definition, every sandbox refresh), not a one-time action.

---

## Gotcha 3: `AppLauncher` target silently aged out at 67.0

**What happens:** metadata copied from an early sample deploys but targets a deprecated path,
and behavior differs from a fresh scaffold.

**When it occurs:** the `.uibundle-meta.xml` sets `target=AppLauncher`, which is **deprecated
in API version 67.0**. From 67.0, `CustomApplication` is the documented replacement and the
default when `target` is omitted.

**How to avoid:** on any bundle review, flag `AppLauncher` and move to `CustomApplication`
(or `Experience` for external-facing sites, which surfaces the app in the Digital Experiences
app).

---

## Gotcha 4: The 2,500-file cap meets `node_modules`

**What happens:** the deploy fails on component size, or the bundle balloons with dependency
source and dev artifacts.

**When it occurs:** the React project's *source tree* (including `node_modules/`, `.env`,
source maps) is placed inside `uiBundles/<app>/` instead of only the built output. A UIBundle
component can contain **up to 2,500 files** — a typical `node_modules` alone is an order of
magnitude past that.

**How to avoid:** deploy built output only. Run
`scripts/check_multi_framework_ui_bundles.py --manifest-dir force-app/main/default` before
deploying; it counts files per bundle and flags `node_modules` and dotenv files.

---

## Gotcha 5: Micro-frontend embedding is a *narrower* maturity than the beta

**What happens:** a design commits to "React components on our Lightning record pages," then
discovers that piece isn't at the same maturity as the rest of the capability.

**When it occurs:** the announcement is read as one uniform beta. In fact embedding React
components directly into Lightning pages as micro-frontends is in **closed pilot** for
Spring 2026, Lightning App Builder drag-and-drop placement is not supported for React
components in the beta, and some platform APIs are unavailable in the beta runtime.

**How to avoid:** scope beta commitments to the standalone-app path (App Launcher /
Experience). Treat Lightning-page embedding as exploratory until the docs promote it.
