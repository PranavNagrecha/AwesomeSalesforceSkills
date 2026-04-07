# Gotchas — Headless vs Standard Experience

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LWR Site Changes Are Invisible Until Explicitly Published

**What happens:** Any modification to an LWR Experience Cloud site — component updates, theme changes, page additions, content edits — is saved as a draft and does NOT become visible to site visitors until an administrator clicks Publish in Experience Builder (or triggers publish via the Sites REST API). The saved draft state is entirely invisible to end users. This is categorically different from Aura, where many changes reflect without a publish step.

**When it occurs:** Every time any change is saved to an LWR site. It applies universally: custom component deployments via Salesforce CLI, Experience Builder admin edits, and theme changes all follow the same publish-gated model.

**How to avoid:** Treat "Publish Site" as a mandatory post-deploy step in every CI/CD pipeline and release runbook. Add it explicitly to deployment checklists. Teams migrating from Aura are most at risk because they carry the assumption that saved = live. The publish action can be automated via the `POST /connect/communities/{communityId}/publish` REST endpoint for pipeline use.

---

## Gotcha 2: Aura Components Cannot Be Used on LWR Sites — No Compatibility Layer Exists

**What happens:** When a team migrates an Aura site to LWR and brings their existing Aura component library, those components simply do not render on the LWR page. There is no runtime wrapper, adapter, or compatibility shim. The components are silently absent or throw framework errors. This is not a configuration problem — it is an architectural incompatibility.

**When it occurs:** During any Aura-to-LWR migration where custom Aura components (including Aura-based AppExchange components) are used on the current site.

**How to avoid:** Before committing to an LWR migration, enumerate every Aura component in use. Each one must be rewritten as an LWC before the LWR site can be launched. Treat Aura component count as the primary migration effort multiplier. AppExchange components that are Aura-only have no LWR equivalent until the ISV ships an LWC version — check with the ISV before planning the migration.

---

## Gotcha 3: Lightning Web Security (LWS) Breaks Libraries That Worked Under Locker Service

**What happens:** LWR sites use Lightning Web Security (LWS) instead of Locker Service. LWS enforces component isolation at module import time, not at runtime API wrapping. Libraries that relied on Locker Service's runtime DOM shims or used JavaScript features Locker patched (e.g., `eval()`, `Function()` constructor, `window.__proto__` manipulation) will fail under LWS in ways that are difficult to debug — often silent failures or cryptic type errors rather than clear Locker-style blocked-API messages.

**When it occurs:** When any third-party JavaScript library used in LWC components running on an LWR site uses `eval()`, `new Function(string)`, direct prototype chain manipulation, or relies on Locker's polyfilled DOM APIs.

**How to avoid:** Before migrating to LWR, test every third-party library in an LWR-enabled sandbox. Pay special attention to: date/time pickers, rich text editors, drag-and-drop libraries, and charting libraries — these categories most frequently use `eval` or `Function()`. Replace incompatible libraries with Salesforce-compatible alternatives (SLDS-based or explicitly LWS-tested). Check the Salesforce GitHub LWS compatibility list for known statuses.

---

## Gotcha 4: Headless Does Not Inherit Experience Builder Site Access Controls

**What happens:** A headless frontend connecting to Salesforce APIs does not automatically enforce Experience Cloud guest user profiles, sharing rules, or audience-based visibility configured in Experience Builder. Access is controlled purely by the Connected App OAuth scopes and the running user's profile/permission sets. Teams often assume that "it's an Experience Cloud headless site" means Experience Cloud security configuration applies — it does not.

**When it occurs:** When a headless frontend is positioned as an "Experience Cloud site" in requirements but the implementation uses only Connected App + Apex REST without explicitly replicating Experience Cloud guest/member access controls in Apex and sharing rules.

**How to avoid:** Treat headless as a standalone API integration, not an Experience Builder site with a different frontend. Explicitly design the access control model at the API layer — enforce object-level and record-level access in every Apex REST endpoint using `with sharing`. Never expose a global describe or unfiltered SOQL result from a headless endpoint.

---

## Gotcha 5: LWR Static Cache Means CDN-Cached Assets May Not Update Immediately After Publish

**What happens:** After publishing an LWR site, the CDN-cached static assets (JS bundles, CSS) propagate to Akamai edge nodes. During propagation (which typically takes a few minutes but can be longer under high load), some users may receive the old cached version while others get the new one. This creates a brief inconsistent state window that does not exist with Aura.

**When it occurs:** Immediately after publishing an LWR site, particularly for global deployments where edge nodes are geographically distributed.

**How to avoid:** Account for the CDN propagation window in release planning — do not schedule LWR site publishes immediately before high-traffic events. For critical production fixes, inform stakeholders that full propagation takes a few minutes. Salesforce cache-busts asset URLs on publish, so repeated hard refreshes will pull the new version; the issue is purely propagation lag, not a permanent cache problem.
