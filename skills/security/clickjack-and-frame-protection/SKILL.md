---
name: clickjack-and-frame-protection
description: "Configure clickjack protection headers and frame-ancestors for VF pages, LWR sites, and Aura apps. NOT for CSP or Trusted URL configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "clickjack protection salesforce"
  - "x frame options visualforce"
  - "lwr site embedded in iframe"
  - "frame ancestors experience cloud"
tags:
  - clickjack
  - frame
  - csp
inputs:
  - "Custom VF pages"
  - "Experience Cloud sites"
  - "intended embedding parents"
outputs:
  - "Frame policy settings per page/site"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Clickjack and Frame Protection

Clickjacking embeds a target page in an invisible iframe and tricks users into clicking hidden controls. Salesforce offers per-page clickjack settings and site-level frame-ancestor allow-lists.

## When to Use

When building or auditing a custom VF page, LWR site, or Experience Cloud page. Also for orgs going through SOC 2 or pen-test remediation.

Typical trigger phrases that should route to this skill: `clickjack protection salesforce`, `x frame options visualforce`, `lwr site embedded in iframe`, `frame ancestors experience cloud`.

## Recommended Workflow

1. Inventory custom VF pages and Experience Cloud sites.
2. For VF: Setup → Session Settings → 'Clickjack protection' options. Default to 'Enable for non-Setup Salesforce pages'.
3. For LWR/Aura sites: Setup → Digital Experiences → Security → Clickjack Protection. Set to 'Allow framing by the same origin only' or 'Allow framing by specific external domains'.
4. If external embedding is required, add only the specific https origin — never '*'.
5. Verify with browser devtools that X-Frame-Options or frame-ancestors header is present.

## Key Considerations

- Modern frame-ancestors (CSP) supersedes X-Frame-Options on browsers that support both.
- Sites embedded in Lightning Out require the parent domain on the allow-list.
- Community pages served over Visualforce Override have separate settings.
- Don't allow '*' — it defeats the protection.

## Worked Examples (see `references/examples.md`)

- *Partner portal embedded in partner site* — Customer portal iframe'd by dealer.com.
- *Visualforce page invoked by a canvas app* — Canvas app frames the VF.

## Common Gotchas (see `references/gotchas.md`)

- **Wildcard * allow-list** — Any attacker origin can frame the site.
- **Preview mode bypass** — Experience Builder preview frames work, production doesn't.
- **Legacy VF without CSP** — Attack via old VF page on force.com domain.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Using '*' in frame-ancestors
- Disabling clickjack protection to make something 'just work'
- Leaving legacy VF pages deployed

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
