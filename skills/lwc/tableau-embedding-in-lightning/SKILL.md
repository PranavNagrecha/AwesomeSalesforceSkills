---
name: tableau-embedding-in-lightning
description: "Embedding Tableau dashboards (and Tableau Pulse insights) inside Lightning App / Record / Home pages — Tableau Embedding API v3 in an LWC, the connected-app + JWT trust pattern for SSO from Salesforce to Tableau, row-level security so a Salesforce user only sees their data in Tableau, CSP / Trusted Sites configuration for the Tableau host, and the Tableau Viz Lightning Web Component (drag-and-drop alternative to a custom LWC). NOT for building Tableau dashboards / data sources (that's Tableau-side work), NOT for CRM Analytics (Tableau is the separate product; see data/crm-analytics-patterns)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "embed tableau dashboard lightning record page lwc"
  - "tableau embedding api v3 javascript salesforce"
  - "tableau pulse lightning lwc embed"
  - "tableau jwt connected app sso salesforce"
  - "row level security tableau salesforce user"
  - "tableau viz lightning web component drag drop"
  - "csp trusted sites tableau host frame-src"
tags:
  - tableau
  - embedding
  - lwc
  - jwt-sso
  - row-level-security
inputs:
  - "Tableau host URL (Tableau Cloud or Server) and target view URL"
  - "SSO requirement (anonymous embed vs JWT-passthrough vs SAML)"
  - "Row-level security model on the Tableau side (data-source filter that uses the Salesforce user identity)"
outputs:
  - "Working LWC that embeds the Tableau view with SSO"
  - "Connected app + JWT signing config (high level — secrets handled by admin)"
  - "Trusted Sites / CSP entries for the Tableau host"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Tableau Embedding in Lightning

Tableau dashboards can be embedded directly in a Salesforce
Lightning page so users do not have to switch tools. The embedding
mechanics are well-documented; the operational complexity is in
auth (SSO from Salesforce to Tableau) and in row-level security
(making sure a logged-in Salesforce user only sees their own slice
of the Tableau data).

This skill covers the LWC build, the JWT-based SSO pattern, the
Trusted Sites / CSP configuration that the platform requires, and
the row-level security pattern that ties it all together.

## The two embed approaches

| Approach | When to use |
|---|---|
| **Tableau Viz LWC** | Drag-and-drop component on a Lightning page; minimal-code option; suitable for simple dashboards |
| **Custom LWC + Tableau Embedding API v3** | Need programmatic control: pass parameters, filter on record context, listen to viz events |

Tableau Pulse (Tableau's metric / AI-summary surface) embeds
similarly — Tableau provides Pulse-specific embedding.

## Tableau Embedding API v3 (custom LWC)

The Embedding API is a JavaScript SDK. In an LWC, you load the SDK
as a static resource (or a third-party `<script>` if CSP allows),
then instantiate a `tableau.Viz` against a `<div>` you render.

```javascript
import { LightningElement } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import tableauApi from '@salesforce/resourceUrl/tableauEmbeddingApiV3';

export default class TableauEmbed extends LightningElement {
    async renderedCallback() {
        if (this.isInitialized) return;
        this.isInitialized = true;
        await loadScript(this, tableauApi);

        const viz = document.createElement('tableau-viz');
        viz.src = 'https://tableau.example.com/views/Sales/Dashboard';
        viz.token = await this.getJwt();  // SSO token; see below
        this.template.querySelector('.tableau-container').appendChild(viz);
    }
}
```

The `<tableau-viz>` web component is provided by the Embedding API;
its attributes drive filters, parameters, and styling.

## JWT SSO — the trust pattern

Anonymous embed (no SSO) works for fully public dashboards but
exposes them to anyone with the URL — almost never what you want.

The recommended SSO is **JWT-based**:

1. Tableau admin creates a Connected App in Tableau (a "JWT Direct
   Trust" type). This generates a Client Id and Secret Id.
2. Salesforce Apex generates a short-lived JWT signed with that
   Secret Id, with claims that identify the Salesforce user (email
   or username) as the Tableau viewer.
3. The LWC asks Apex for the JWT and passes it to `<tableau-viz>` as
   the `token` attribute.
4. Tableau validates the JWT, identifies the user, and applies row-
   level security based on the user identity.

The Apex side typically uses `Crypto.signWithCertificate` with a
named certificate; secrets are stored in Custom Metadata or Named
Credentials, not hardcoded.

## Row-level security

Tableau's row-level security is configured on the **Tableau side**,
not Salesforce. The pattern:

1. Data source has a user-identity column (e.g. `OwnerEmail`).
2. Data source filter: `[OwnerEmail] = USERNAME()` where
   `USERNAME()` is Tableau's user-identity function.
3. SSO from Salesforce passes the Salesforce user's email as the
   Tableau identity.
4. When the user opens the embedded viz, the filter restricts to
   their rows.

If the SSO claim is wrong (e.g. passes a service-account name), the
filter applies to that account's rows — typically empty or
incorrect. RLS bugs almost always trace back to identity-claim
misconfiguration.

## CSP and Trusted Sites

The Tableau host URL must be added to:

- **Lightning Trusted Sites** (Setup -> CSP Trusted Sites). Without
  this, the iframe / fetch is blocked by Lightning's CSP.
- **CORS allowlist** if Apex makes a fetch to Tableau (rarer; JWT
  flow is local).

Both are admin-side configuration steps.

## Recommended Workflow

1. **Choose the embed approach.** Tableau Viz LWC for simple drop-in; custom LWC + Embedding API v3 for programmatic control.
2. **Configure CSP Trusted Sites.** Setup -> CSP Trusted Sites; add the Tableau host URL with `Connect-Source` and `Frame-Source` permissions as appropriate.
3. **Set up JWT Connected App in Tableau.** This is Tableau-side config; provides Client Id and Secret Id.
4. **Implement the JWT generator in Apex.** Sign with `Crypto.signWithCertificate`; claim payload identifies the Salesforce user; expiry short (5 min).
5. **Build the LWC.** Load the Embedding API static resource; render `<tableau-viz>`; pass JWT and parameters.
6. **Configure Tableau-side row-level security.** Data-source filter matches the JWT subject claim.
7. **Test as different Salesforce users** to confirm RLS works. Test with an inactive user to confirm the JWT generation fails gracefully.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Building Tableau dashboards / data sources | Tableau-side training |
| CRM Analytics (Salesforce native) | `data/crm-analytics-patterns` |
| Tableau-side admin (sites, projects, permissions) | Tableau Server / Cloud admin |
| SAML SSO into Tableau (alternative to JWT) | Tableau SSO docs |
