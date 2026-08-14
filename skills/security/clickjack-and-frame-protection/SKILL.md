---
name: clickjack-and-frame-protection
description: "Configure clickjack protection headers and frame-ancestors for VF pages, LWR sites, and Aura apps. NOT for CSP or Trusted URL configuration — use security/csp-and-trusted-urls."
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-31
---

# Clickjack and Frame Protection

Clickjacking hides your page inside an attacker's iframe and harvests the user's clicks. Salesforce does not expose an `X-Frame-Options` or `Content-Security-Policy` header for you to set — the framing headers are emitted by the platform, and you control them through two completely separate Setup surfaces plus a trusted-domain allow-list. Getting this wrong shows up as a blank iframe on a partner's site, not as a security alert, so it is usually diagnosed as "the integration is broken".

---

## Before Starting

- Determine which surface you are protecting: **Salesforce/Visualforce pages** (Session Settings) or an **Experience Cloud site** (Experience Builder). These are different screens with different option sets, and a site that mixes Experience Builder pages with Salesforce Tabs + Visualforce pages needs both.
- Determine the framing *direction*. Canvas apps are loaded on a Salesforce page in an iframe — Salesforce is the parent there, so clickjack settings are not what is blocking a Canvas app.
- Collect the exact parent origins that must be allowed, including scheme and any port. There is no wildcard-shaped answer here.
- Note the org's My Domain / Enhanced Domains hostnames — "same origin" is evaluated against the current hostname, so a domain change invalidates prior testing.

---

## Core Concepts

### The four Session Settings options (Salesforce and Visualforce pages)

Setup → Quick Find → **Session Settings**. These are independent checkboxes, not a single level:

| Option | What it protects (documented description) |
|---|---|
| **Enable clickjack protection for Setup pages** | "Protects against clickjack attacks on setup Salesforce pages." |
| **Enable clickjack protection for non-Setup Salesforce pages** | "Protects against clickjack attacks on non-setup Salesforce pages." |
| **Enable clickjack protection for customer Visualforce pages with standard headers** | "Protects against clickjack attacks on your Visualforce pages with headers enabled." |
| **Enable clickjack protection for customer Visualforce pages with headers disabled** | "Protects against clickjack attacks on your Visualforce pages with headers disabled." |

The last two split on whether the page renders the Salesforce header — in Visualforce that is the `showHeader` attribute on `<apex:page>`. A page with `showHeader="false"` is governed by the *headers disabled* checkbox only. Turning on just one of the two leaves the other class of page unprotected, which is the most common half-finished state in the wild.

### Trusted Domains for Inline Frames

Enabling protection and then allow-listing a parent are two separate steps. In Session Settings, under **Trusted Domains for Inline Frames**, add each external domain that may frame your pages and set the **iframe type** (for example, Visualforce Pages). Documented capacity limits:

| Surface | Trusted-domain limit |
|---|---|
| Salesforce Tabs + Visualforce site | 512 domains |
| Experience Builder site | 100 domains per site |
| Any surface | Keep the resulting CSP header under 12 KB |

The 12 KB ceiling is the one that bites at scale: a long allow-list produces a header some proxies and browsers will truncate or reject, and the symptom is intermittent framing failure rather than a clean error.

### Experience Cloud has its own four-level control

Experience Builder → **Settings** → **Security & Privacy** → **Clickjack Protection Level**:

| Level | Effect |
|---|---|
| **Allow framing by any page** | No protection. Any external domain can frame your site pages. |
| **Allow framing of site pages on external domains** | Only domains you list under Trusted Domains for Inline Framing can frame the site. |
| **Allow framing by the same origin only** | Framing permitted only from pages with the same domain name and protocol security. This is the default for Experience Cloud sites and the recommended level. |
| **Don't allow framing by any page** | Most restrictive. |

A site built with both Experience Builder pages and Salesforce Tabs + Visualforce pages needs clickjack protection configured in **both** locations — the settings do not inherit from one another.

### X-Frame-Options versus CSP `frame-ancestors`

Salesforce emits the framing policy as HTTP headers. Modern browsers honour the CSP `frame-ancestors` directive; Internet Explorer and other less-capable browsers support clickjack protection through the legacy `X-Frame-Options` header only. Two consequences for practitioners:

- A multi-domain allow-list is only expressible in `frame-ancestors`. `X-Frame-Options` has no multi-origin form, so legacy browsers get the stricter behaviour and your "it works in Chrome" test proves nothing about them.
- You cannot add, override, or relax these headers from Apex, Visualforce, or an LWC. Any code that appears to set them is either dead or is setting a header on a response Salesforce will overwrite.

### What the failure actually looks like

The browser blocks the render and writes to the DevTools console — a `Refused to display … 'X-Frame-Options'` message when it acted on the legacy header, or a `Refused to frame … frame-ancestors` message when it acted on CSP. Which one you get tells you which header path is in play. Neither appears in any Salesforce log, so the person reporting the bug has to be asked for the console text. Worked captures are in `references/examples.md`.

---

## Common Patterns

### Pattern 1: Let one named partner domain frame a Visualforce page

**When to use:** a dealer, broker, or partner portal embeds a Visualforce page inside their own site.

1. Setup → Session Settings. Enable **both** Visualforce options — *customer Visualforce pages with standard headers* and *customer Visualforce pages with headers disabled* — so the protection is on regardless of the page's `showHeader` value.
2. Under **Trusted Domains for Inline Frames**, add the partner's exact origin and set the iframe type to Visualforce Pages.
3. Retest from the partner's real origin. A same-origin test from inside Salesforce proves nothing about a cross-origin frame.

**Why not turn the protection off:** disabling the checkbox removes the header for every Visualforce page in the org, not just the one the partner needs. The allow-list is the narrow control; the checkbox is the org-wide one.

### Pattern 2: Experience Cloud site embedded by a corporate intranet

**When to use:** a customer or partner community is surfaced inside an internal portal.

1. Experience Builder → Settings → Security & Privacy → set **Clickjack Protection Level** to *Allow framing of site pages on external domains*.
2. Add the intranet origin to the site's Trusted Domains for Inline Framing (limit 100 per site).
3. If the site also serves Salesforce Tabs + Visualforce pages, repeat the configuration in Session Settings — the two surfaces are configured independently.

**Why not *Allow framing by any page*:** it is the documented no-protection level. It will make the embed work and it makes every page in the site available to any attacker origin.

### Pattern 3: Diagnose "the iframe is blank" without guessing

**When to use:** an embed that previously worked stops working, typically after a domain change or a Session Settings edit.

1. Get the DevTools console text from the person seeing the failure — it names both the refused URL and the header that refused it.
2. Confirm the framed URL's surface: Setup page, non-Setup Salesforce page, Visualforce page (and whether `showHeader` is false), or Experience Cloud page. Only one of the settings above governs it.
3. Compare the parent origin character for character against the trusted-domain entry — scheme and host both count.
4. If the org recently changed My Domain or deployed Enhanced Domains, the "same origin" that used to match no longer does.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| No external party needs to frame anything | Enable all four Session Settings options; Experience Cloud at *same origin only* | Strongest posture with no allow-list to maintain |
| One or two known partner origins | Keep protection on; add exact origins to Trusted Domains for Inline Frames | Allow-list is scoped; the checkbox is org-wide |
| Dozens of partner origins | Reconsider the architecture before adding entries | 512/100 domain limits and the 12 KB CSP header ceiling both bite |
| Third-party app must appear *inside* Salesforce | Canvas, not clickjack settings | Canvas apps load in an iframe on a Salesforce page — Salesforce is the parent |
| Legacy browsers in scope | Assume single-origin behaviour only | Those browsers support the legacy `X-Frame-Options` header only, which cannot express a multi-origin list |
| Someone proposes setting the header in code | Reject | The framing headers are platform-emitted; Apex/VF/LWC cannot set them |

---

## Recommended Workflow

1. Inventory what can be framed: Visualforce pages (noting `showHeader`), Experience Cloud sites, and any Salesforce Tabs + Visualforce site.
2. Set the baseline — all four Session Settings options on, and Experience Cloud at *Allow framing by the same origin only*.
3. Collect the exact parent origins that genuinely require framing, with scheme and host, from the owning team rather than from a ticket description.
4. Add those origins to Trusted Domains for Inline Frames with the correct iframe type; check the count against the 512 / 100 limits and keep the CSP header under 12 KB.
5. Test cross-origin from the real parent page and capture the DevTools console output as the evidence, in both a modern browser and any legacy browser still in scope.
6. Re-run step 5 after any My Domain rename, Enhanced Domains change, or Experience Cloud site publish.

---

## Review Checklist

- [ ] All four Session Settings clickjack options are enabled, or each exception is documented with an owner
- [ ] Both Visualforce options are on, not just the *standard headers* one
- [ ] Experience Cloud sites are at *same origin only* or *external domains* — never *Allow framing by any page*
- [ ] A site mixing Experience Builder and Salesforce Tabs + Visualforce pages is configured in both places
- [ ] Every trusted domain entry has a named business owner and a review date
- [ ] Trusted-domain counts are within 512 (Tabs + Visualforce) / 100 (Experience Builder) and the CSP header is under 12 KB
- [ ] Cross-origin framing was tested from the real parent origin, not from a same-origin preview
- [ ] Unused legacy Visualforce pages have been removed rather than left deployed behind the allow-list

---

## Deep Dives

`references/examples.md` — partner embed, Canvas direction correction, domain-cutover retest. `references/gotchas.md` — six production failure modes with the message each produces. `references/llm-anti-patterns.md` — six wrong/right pairs, starting with code that pretends it can set the header.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Frame policy matrix | Every framable surface → governing setting → current value → intended value |
| Trusted-domain register | Each allowed origin, its iframe type, the business owner, and the review date |
| Cross-origin test evidence | DevTools console capture from the real parent origin, before and after |
| Domain-change retest plan | The subset of the above that must be re-run after a My Domain or Enhanced Domains change |

---

## Related Skills

- `security/network-security-and-trusted-ips` — owns CSP Trusted Sites for Lightning components and CSP-violation troubleshooting generally; this skill covers only the framing directive.
- `security/csp-and-trusted-urls` — owns Trusted URLs and the script/style/connect source directives.
- `security/experience-cloud-security` — owns the wider Experience Cloud security posture that the Clickjack Protection Level sits inside.
- `security/visualforce-security-and-modernization` — owns Visualforce hardening and retirement, including the legacy pages this skill tells you to delete rather than allow-list.
