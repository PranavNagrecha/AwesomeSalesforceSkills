# LLM Anti-Patterns — Clickjack and Frame Protection

## Anti-Pattern 1: Emitting a framing header from Apex or Visualforce

**What the LLM generates:**

```apex
// WRONG - Salesforce emits the framing headers for these surfaces; this does nothing useful
public PageReference allowPartnerFraming() {
    ApexPages.currentPage().getHeaders().put('X-Frame-Options', 'ALLOW-FROM https://dealer.example');
    ApexPages.currentPage().getHeaders().put(
        'Content-Security-Policy', 'frame-ancestors https://dealer.example');
    return null;
}
```

```html
<!-- WRONG - frame-ancestors is only honoured in an HTTP header, never in a meta tag -->
<meta http-equiv="Content-Security-Policy" content="frame-ancestors *">
```

**Why it happens:** on every other web stack the developer owns the response headers, so the model reaches for the tool it knows. `ALLOW-FROM` compounds the error — it was never broadly supported and is not how a multi-origin allow-list is expressed.

**Correct pattern:** configure it, do not code it.

```text
Setup -> Session Settings
  [x] Enable clickjack protection for customer Visualforce pages with standard headers
  [x] Enable clickjack protection for customer Visualforce pages with headers disabled
  Trusted Domains for Inline Frames -> add https://dealer.example, iframe type = Visualforce Pages
```

**Detection hint:** any diff that writes `X-Frame-Options` or `Content-Security-Policy` in Apex, Visualforce, or LWC for a Salesforce-hosted page is dead code. Reject it and ask which Setup surface the page belongs to.

---

## Anti-Pattern 2: Recommending `frame-ancestors *` or "allow framing by any page"

**What the LLM generates:** "Set the Clickjack Protection Level to *Allow framing by any page* so the partner embed works" — or, in header form, `frame-ancestors *`.

**Why it happens:** it is the smallest change that makes the symptom disappear, and the option is right there in the picklist.

**Correct pattern:** move one level, not all the way to the bottom.

```text
WRONG:  Clickjack Protection Level = Allow framing by any page      (documented: no protection)
RIGHT:  Clickjack Protection Level = Allow framing of site pages on external domains
        Trusted Domains for Inline Framing -> https://portal.dealer.example
```

**Detection hint:** *Allow framing by any page* is the documented least-secure level. Any change request that lands there should carry the same approval weight as disabling authentication, and should name the specific origin that could not be enumerated and why.

---

## Anti-Pattern 3: Enabling one Visualforce checkbox and calling it done

**What the LLM generates:** "Enable clickjack protection for customer Visualforce pages" — as if there were one setting.

**Why it happens:** the two options have nearly identical names and most summaries collapse them into one.

**Correct pattern:** they are independent, and the split is `showHeader`.

```text
<apex:page showHeader="true">    -> governed by "customer Visualforce pages with standard headers"
<apex:page showHeader="false">   -> governed by "customer Visualforce pages with headers disabled"
```

Enable both. The `showHeader="false"` pages are the embedded, white-labelled ones — exactly the ones an attacker would want to frame.

**Detection hint:** a remediation plan that mentions clickjack protection for Visualforce exactly once has covered at most half the pages in the org.

---

## Anti-Pattern 4: Blaming clickjack settings for a Canvas app

**What the LLM generates:** "The Canvas app won't render — enable framing by Salesforce servers in Session Settings."

**Why it happens:** both stories involve an iframe and Salesforce, so the model matches on the word rather than the direction.

**Correct pattern:** identify which side is the child.

```text
Canvas app        : parent = Salesforce page, child = vendor app
                    -> vendor's server must permit framing by the Salesforce origin
Partner embed     : parent = partner site,    child = Salesforce page
                    -> Salesforce Session Settings / Experience Builder + trusted domains
```

Canvas apps are loaded on a Salesforce page in an iframe, so Salesforce clickjack settings — which govern who may frame Salesforce — are not in the path at all.

**Detection hint:** ask for the console error and read the URL inside it. If the refused URL is the vendor's, no Salesforce setting will fix it, and the "fix" being proposed removes protection org-wide for nothing.

---

## Anti-Pattern 5: Declaring success from a same-origin test

**What the LLM generates:** "Open the page in Experience Builder preview to confirm framing works."

**Why it happens:** preview is the fastest feedback loop available and it renders the page, so it looks like proof.

**Correct pattern:** the test must be cross-origin from the real parent, and the artefact is the console, not the pixels.

```text
WRONG:  Experience Builder preview renders -> "framing works"
WRONG:  open /apex/PartnerQuote directly in a tab -> no framing header is evaluated at all
RIGHT:  load https://portal.dealer.example (the real parent), open DevTools,
        confirm no "Refused to display" / "Refused to frame" entry appears
```

**Detection hint:** an acceptance step that does not name the external parent origin has not tested the policy. Preview is same-origin and satisfies even *same origin only*.

---

## Anti-Pattern 6: Treating an allow-list entry as page-scoped

**What the LLM generates:** "Add the partner domain so they can frame `PartnerQuote` — this only affects that page."

**Why it happens:** the request was about one page, so the model assumes the grant is one page wide.

**Correct pattern:** the entry is scoped to the iframe *type*, not to a page.

```text
Trusted Domains for Inline Frames
  https://portal.dealer.example   iframe type = Visualforce Pages
        ^ grants framing rights over EVERY Visualforce page in the org,
          including retired demo and managed-package pages
```

So the prerequisite work is deleting unused Visualforce pages, not just adding the domain.

**Detection hint:** if the change request does not include a page inventory, the reviewer is approving framing over pages nobody has looked at. Check the counts too — 512 domains for a Salesforce Tabs + Visualforce site, 100 per Experience Builder site, with the CSP header kept under 12 KB.

