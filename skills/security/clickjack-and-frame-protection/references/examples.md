# Examples — Clickjack and Frame Protection

## Example 1: Partner site embeds an Experience Cloud page

**Context:** A dealer network embeds the manufacturer's Experience Cloud site inside `https://portal.dealer.example` so dealers never leave their own portal.

**Problem:** The iframe renders blank. The dealer's console shows:

```text
Refused to frame 'https://acme.my.site.com/partners' because an ancestor violates
the following Content Security Policy directive: "frame-ancestors 'self'".
```

That message names `frame-ancestors 'self'` — the site is at *Allow framing by the same origin only*, which is the documented default for Experience Cloud sites.

**Solution:**

1. Experience Builder → Settings → Security & Privacy → **Clickjack Protection Level** → *Allow framing of site pages on external domains*.
2. Under Trusted Domains for Inline Framing, add `https://portal.dealer.example`.
3. Publish the site, then retest from the dealer's real page.

**Why it works:** the site keeps a real framing policy; only the one named origin is added to it. The alternative level, *Allow framing by any page*, is documented as no protection at all.

**What to watch:** the per-site limit is 100 trusted domains, and the resulting CSP header should stay under 12 KB. A dealer network that grows past a few dozen origins needs a different design — a single branded proxy origin, not 200 allow-list entries.

---

## Example 2: A Canvas app is not a clickjack problem

**Context:** A third-party pricing tool is being surfaced on the Opportunity record page. The team assumed clickjack protection was blocking it and started disabling Session Settings checkboxes.

**Problem:** The framing direction was misread. Canvas apps are loaded on a Salesforce page in an iframe — **Salesforce is the parent and the third-party app is the child**. Salesforce's clickjack settings govern who may frame *Salesforce*, so they cannot be what is blocking the vendor's page.

**Solution:** stop editing Session Settings and diagnose the actual child. Ask which side the console error came from:

| Console message origin | What it means | Where to fix it |
|---|---|---|
| Error names the **vendor's** URL | The vendor's own server sends a framing header that refuses Salesforce | The vendor must allow the Salesforce origin |
| Error names a **Salesforce** URL | Something is genuinely framing a Salesforce page | Session Settings / Experience Builder, per the main skill |

**Why it matters:** the team's original path — turning off "Enable clickjack protection for non-Setup Salesforce pages" — would have removed framing protection from every non-Setup page in the org and still not fixed the Canvas app. This is the highest-cost misdiagnosis in this area because the "fix" is org-wide and silent.

---

## Example 3: Visualforce page on an external domain, done completely

**Context:** A quote-approval Visualforce page must render inside a broker's website. The page is defined as `<apex:page showHeader="false" standardStylesheets="false">` so it looks native to the broker.

**Problem:** The first attempt enabled only *Enable clickjack protection for customer Visualforce pages with standard headers* and added the broker origin. The page still refused to frame. The console showed an `X-Frame-Options` refusal, not a `frame-ancestors` one, in the broker's older browser.

**Solution:**

1. Setup → Quick Find → **Session Settings**.
2. Enable **both** Visualforce options: *customer Visualforce pages with standard headers* **and** *customer Visualforce pages with headers disabled*. The page sets `showHeader="false"`, so it is the second checkbox that governs it.
3. Under **Trusted Domains for Inline Frames**, add the broker's exact origin and set the iframe type to **Visualforce Pages**.
4. Retest in both a modern browser and the broker's legacy browser.

**Why the legacy browser behaved differently:** less capable browsers support clickjack protection through the legacy `X-Frame-Options` header only. That header cannot express a list of allowed origins, so a multi-origin allow-list degrades to single-origin behaviour there. If legacy browsers are in scope, the allow-list is not a complete answer and the requirement needs renegotiating.

**Capacity note:** up to 512 external domains can be added for a Salesforce Tabs + Visualforce site. Treat that as a ceiling, not a target — every entry is an origin you have promised to keep trustworthy.

---

## Example 4: Retest after a domain cutover

**Context:** The org completed an Enhanced Domains change. Two weeks later a partner reports their embed is blank.

**Problem:** "Same origin" is evaluated against the *current* hostname. Every trusted-domain entry, every parent page's hardcoded iframe `src`, and every same-origin assumption made before the cutover was validated against hostnames that no longer exist.

**Solution — the retest set, in this order:**

1. Re-enumerate every framable surface: Experience Cloud sites, Salesforce Tabs + Visualforce sites, and standalone Visualforce pages.
2. For each, confirm the governing setting is still where you left it — a site publish or a sandbox refresh can reset site-level configuration.
3. Confirm each parent page's iframe `src` points at the new hostname. A stale `src` produces a *navigation* failure, not a framing failure, and the two are easily confused.
4. Capture the DevTools console text for each embed from the real parent origin. Absence of an error is the pass criterion; "the page looks fine to me" from inside Salesforce is not, because that test is same-origin.

**Why it works:** it separates the three failure classes that all present as "blank iframe" — wrong URL, missing allow-list entry, and protection level reset — instead of guessing between them.
