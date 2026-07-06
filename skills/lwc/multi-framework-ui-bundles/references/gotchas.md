# Gotchas — Multi-Framework UI Bundles

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The beta wall is org-shaped

**What happens:** the app works perfectly through the whole sandbox pilot, then the
production rollout is blocked outright — beta apps cannot be deployed to production orgs.

**When it occurs:** any plan that treats the Multi-Framework open beta as "GA with an
asterisk." The beta is restricted to **scratch orgs and sandboxes that use English as the
org default language**; non-English-default orgs are excluded even for pilots.

**How to avoid:** state the beta boundary in the first estimate. If the requirement is a
production app on a fixed date, build it as LWC (`lwc/*` skills) and treat the React version
as a forward-looking spike.

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
