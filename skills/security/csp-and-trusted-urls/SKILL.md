---
name: csp-and-trusted-urls
description: "Configure Content Security Policy via Trusted URLs and CSP Trusted Sites so Lightning, LWR, and LWC can call third-party scripts, APIs, and frame sources. NOT for clickjack configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "script refused to load salesforce csp"
  - "add trusted url for external api"
  - "lwc fetch third party blocked"
  - "csp trusted sites lightning"
tags:
  - csp
  - trusted-urls
  - lightning
inputs:
  - "External URLs the UI must reach"
  - "context (Lightning vs LWR vs Experience)"
outputs:
  - "Trusted URL records with correct context scopes"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# CSP and Trusted URLs

Salesforce enforces strict CSP for Lightning and LWR. External scripts, connect-src targets, and frame-src must be allow-listed via Trusted URLs (Setup → Security → Trusted URLs). This skill maps each context (Lightning Experience, Experience Cloud LWR, Lightning Communities) to the right directive.

## When to Use

Before adding an LWC or Aura component that calls a non-Salesforce endpoint, pulls a third-party library, or frames a partner site. Not for server-side callouts — use Named Credentials + Remote Site Settings.

Typical trigger phrases that should route to this skill: `script refused to load salesforce csp`, `add trusted url for external api`, `lwc fetch third party blocked`, `csp trusted sites lightning`.

## Recommended Workflow

1. Identify the failing directive: connect-src, script-src, img-src, frame-src, font-src.
2. Setup → Trusted URLs → New. Enter the URL, context (Lightning Experience / Experience Cloud LWR / Communities), and check the relevant directive boxes.
3. Reload the page; verify the console CSP violation is gone.
4. Document the external dependency in your architecture diagram + security review.
5. Remove entries quarterly when features are retired.

## Key Considerations

- Trusted URL is per context — a URL trusted in LEX is not automatically trusted in LWR.
- script-src with inline handlers (onclick=) is not allowed; refactor to LWC event listeners.
- Remote Site Settings govern Apex callouts; Trusted URL governs browser-side fetch.
- Salesforce generates a hash for each CSP-allowed script; use the SFDC-provided cdn when possible to reduce allow-list size.

## Worked Examples (see `references/examples.md`)

- *Add Stripe.js to an LWC checkout* — B2C LWR site.
- *Call internal analytics API from Lightning* — LEX dashboard.

## Common Gotchas (see `references/gotchas.md`)

- **Wildcard subdomains** — https://*.corp.com trusts unintended hosts.
- **LWR vs. LEX confusion** — Same URL added for wrong context silently fails.
- **CDN churn** — Script URL changes version and the allow-list breaks.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Using wildcards 'https://*'
- Disabling CSP ('Relaxed CSP') to ship faster
- Allow-listing a script URL without also allow-listing its connect-src dependencies

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
