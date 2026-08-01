# Gotchas — Clickjack and Frame Protection

## Gotcha 1: Enabling only one of the two Visualforce options

**What happens:** Half the org's Visualforce pages are protected and half are not, and nothing in Setup indicates the gap.

**When it occurs:** *Enable clickjack protection for customer Visualforce pages with standard headers* is enabled and *…with headers disabled* is not (or the reverse). The split is on whether the page renders the Salesforce header — the `showHeader` attribute on `<apex:page>`. Embedded and white-labelled pages are exactly the ones that set `showHeader="false"`, so the unprotected half is the half most likely to be framed.

**How to avoid:** enable both. Then list the pages that set `showHeader="false"` and confirm each one is either intentionally framable with a trusted-domain entry or should not exist.

---

## Gotcha 2: A wildcard entry is not the shortcut it looks like

**What happens:** An allow-list entry intended to cover "all our partner subdomains" either fails to match anything or widens the policy far past what the reviewer believed they approved.

**When it occurs:** Someone tries to express a set of origins as a pattern rather than enumerating them, usually because the partner has one origin per region. The Experience Cloud level that corresponds to "anyone may frame this" is a distinct, explicitly labelled option — *Allow framing by any page*, documented as the least secure level with no protection — and choosing it is the only way to actually get wildcard behaviour.

**How to avoid:** enumerate exact origins. If the count is unmanageable, the answer is an architectural change (one branded proxy origin) rather than a looser policy. Any change that moves an Experience Cloud site to *Allow framing by any page* should require the same approval as turning off authentication.

---

## Gotcha 3: Experience Builder preview passes while production fails

**What happens:** The embed works during build and breaks the moment it is published and consumed from the partner's site.

**When it occurs:** The preview is same-origin from inside Salesforce, so it satisfies even *Allow framing by the same origin only*. The production test is cross-origin from the partner's hostname and is the only one that exercises the policy. The same illusion appears with Visualforce: opening the page directly in a tab never evaluates a framing header at all.

**How to avoid:** the acceptance test must be executed from the real parent page on the real parent origin, and the evidence is the DevTools console output, not a screenshot of the rendered page.

---

## Gotcha 4: Trusted-domain limits and the 12 KB CSP header ceiling

**What happens:** Framing starts failing intermittently and inconsistently across browsers and networks once the allow-list has grown large. There is no error in Salesforce.

**When it occurs:** Documented capacity is 512 trusted domains for a Salesforce Tabs + Visualforce site and 100 for each Experience Builder site, with the guidance to keep the size of the CSP header under 12 KB when multiple domains are allowed. A long allow-list produces a large header, and intermediaries handle large headers inconsistently.

**How to avoid:** budget the header, not just the row count — 100 origins at roughly 30 characters each already approaches the ceiling once the rest of the directive is included. Review the register on a schedule and delete entries whose business owner has left or whose project has ended.

---

## Gotcha 5: A site with two page technologies needs two configurations

**What happens:** Some pages in one Experience Cloud site frame correctly and others refuse, which reads as random.

**When it occurs:** The site mixes Experience Builder pages with Salesforce Tabs + Visualforce pages. The documented guidance is explicit: the location for enabling clickjack protection differs between the two, and a site containing both must have protection enabled in both locations. Configuring only Experience Builder leaves the Visualforce half on whatever Session Settings say, and vice versa.

**How to avoid:** classify each page by the technology that renders it before touching either screen, and configure both. Record which pages belong to which technology in the frame policy matrix so the next person does not rediscover it.

---

## Gotcha 6: Legacy Visualforce pages left deployed are still framable surface

**What happens:** An attacker frames a page nobody remembers deploying — an old approval page, a demo page, a page from a retired managed package — and the trusted domain you carefully scoped for the current partner covers it too, because the allow-list applies to the iframe type, not to one page.

**When it occurs:** Any org more than a couple of years old. The framing policy is set per surface class, so every Visualforce page in the org shares the trusted-domain list configured for Visualforce Pages.

**How to avoid:** delete unused Visualforce pages rather than relying on obscurity. Treat the trusted-domain register as granting framing rights over the *whole class* of pages, and size the approval accordingly.

---

## Gotcha 7: The header cannot be set, overridden, or relaxed from code

**What happens:** A developer adds header-setting code, sees no change in behaviour, and concludes the setting is broken — then escalates to disabling the org-wide checkbox.

**When it occurs:** Anywhere someone reaches for `ApexPages.currentPage().getHeaders()`, a custom `RestResponse` header, or a `<meta http-equiv>` tag to influence framing. The framing headers for these surfaces are emitted by the platform; a `<meta http-equiv>` tag cannot deliver `frame-ancestors` at all, since that directive is only honoured in an HTTP header.

**How to avoid:** treat the two Setup surfaces plus the trusted-domain list as the entire control set. If a proposed fix involves writing a header, it is the wrong fix, and the escalation it leads to — disabling protection org-wide — is far more damaging than the original blank iframe.

