# LLM Anti-Patterns — Experience Cloud Site Setup

Common mistakes AI coding assistants make when generating or advising on Experience Cloud site setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Aura Components in an LWR Site

**What the LLM generates:**
```
"Add the c:myAuraWidget component to your Experience Cloud page by dragging it
from the component panel in Experience Builder."
```
(When the target site uses the Build Your Own LWR template.)

**Why it happens:** LLMs conflate the legacy Aura-based and modern LWR-based Experience Cloud templates. Training data contains large amounts of Aura-era Experience Cloud documentation where Aura components were standard. The LLM does not distinguish which template is in use.

**Correct pattern:**
```
LWR sites support LWC components only. Aura components (c:myAuraWidget)
will not appear in the Experience Builder component picker for an LWR site.

To add this functionality to an LWR site, either:
1. Migrate c:myAuraWidget to an LWC component, or
2. Switch to the Aura Build Your Own template (requires recreating the site).
```

**Detection hint:** Look for references to Aura component names (`c:` prefix on well-known Aura components) or `<aura:component>` in advice targeted at an LWR site context.

---

## Anti-Pattern 2: Omitting the Template Permanence Warning

**What the LLM generates:**
```
"Create a new Experience Cloud site and select the Aura template for now.
You can switch to LWR later when you're ready to migrate."
```

**Why it happens:** LLMs often suggest incremental approaches to reduce perceived complexity. They may not have internalized (or may have inconsistent training data about) the fact that the template cannot be changed after site creation. The phrase "you can switch later" is a common LLM hedge that is factually incorrect here.

**Correct pattern:**
```
Template selection is permanent. Once a site is created with the Aura Build Your Own
template, it cannot be changed to LWR. Switching templates requires deleting the site
and recreating it, losing all Experience Builder configuration.

Choose the template based on your full component inventory before creating the site.
```

**Detection hint:** Any phrase like "you can switch later", "migrate the template", or "upgrade to LWR" in the context of an existing site should trigger a review. Template migration in Experience Cloud means site recreation, not an in-place upgrade.

---

## Anti-Pattern 3: Confusing the /s URL Path Prefix

**What the LLM generates:**
```
"Your Experience Cloud page URLs will follow the pattern:
MyDomainName.my.site.com/portal/home"
```
(When the site uses an Aura template, where URLs actually include `/s`.)

**Why it happens:** LWR sites introduced clean URL paths without the `/s` prefix. LLMs trained on both Aura and LWR documentation may apply LWR URL behavior to Aura sites, or vice versa.

**Correct pattern:**
```
Aura-based Experience Cloud sites include /s in all page paths:
  MyDomainName.my.site.com/portal/s/home

LWR-based sites use clean paths without /s:
  MyDomainName.my.site.com/portal/home

Deep links, email templates, and integration callbacks must account for this
difference based on the template in use.
```

**Detection hint:** When providing URLs for an Aura site, check whether `/s` is present. For LWR sites, confirm `/s` is absent. A mismatch between stated template and URL pattern is a signal.

---

## Anti-Pattern 4: Missing CDN Caching Implications for LWR

**What the LLM generates:**
```
"After saving your changes in Experience Builder, the updates will be visible
to site visitors."
```
(On an LWR site, where changes require explicit republish before they are served.)

**Why it happens:** LLMs default to Aura-era behavior where many Experience Builder changes appear more immediately. The LWR publish-time freeze and HTTP caching model is a meaningful behavioral difference that LLMs frequently miss or understate.

**Correct pattern:**
```
On LWR sites, changes saved in Experience Builder are in draft state and are NOT
visible to site visitors until the site is explicitly republished.

After making any changes (branding, components, navigation, page content):
1. Click the Publish button in Experience Builder.
2. Confirm the published version timestamp in Site Settings has updated.
3. Only then are changes visible to visitors.
```

**Detection hint:** Any LWR site instruction that uses phrases like "your changes will appear", "visitors will see", or "the update is live" without an explicit republish step should be flagged.

---

## Anti-Pattern 5: Using --dxp- CSS Tokens in Aura Sites (or Ignoring Them for LWR)

**What the LLM generates:**
```
"To style your Experience Cloud site, set the primary color by adding
--dxp-color-brand: #0070D2 to your component's CSS file."
```
(When the site uses an Aura-based template, where `--dxp-*` tokens are not the branding mechanism.)

**Or inversely:**
```
"Open the Theme panel in Experience Builder and use the color pickers to set
the primary color for your site."
```
(When the site uses an LWR template, where the Branding Set with `--dxp-*` tokens is the correct mechanism.)

**Why it happens:** LLMs conflate Aura and LWR branding systems. `--dxp-*` CSS custom properties are an LWR-specific concept. Aura-based sites use the Experience Builder theme panel, not CSS custom property tokens. LLMs trained on a mix of documentation apply one pattern to both contexts.

**Correct pattern:**
```
LWR sites: Use Branding Sets in Experience Builder. Define CSS custom property tokens
(e.g., --dxp-color-brand, --dxp-color-background, --dxp-font-family-primary).
Component CSS should consume these tokens rather than hardcoded values.

Aura sites: Use the Theme panel in Experience Builder (color pickers, font selectors).
CSS custom properties are not the branding mechanism for Aura-based sites.
```

**Detection hint:** If `--dxp-*` tokens appear in advice for an Aura site, or if the Theme panel is recommended for an LWR site's branding, the advice is using the wrong branding model for the template type.

---

## Anti-Pattern 6: Recommending Internal Lightning App Components for Experience Cloud Without Verifying Target Configuration

**What the LLM generates:**
```
"Add your c:productList component to the Experience Cloud page — it should
work the same as in your internal app."
```

**Why it happens:** LLMs assume LWC components built for internal Lightning pages are automatically available in Experience Cloud. They overlook the `targetConfig` declaration in the component's `*.js-meta.xml` that controls which surfaces (App Builder, Record Page, Experience Cloud) a component is exposed to.

**Correct pattern:**
```
A LWC component only appears in Experience Builder if its *.js-meta.xml includes
an appropriate target. For Experience Cloud, the component needs:

<targets>
  <target>lightningCommunity__Page</target>
  <target>lightningCommunity__Default</target>
</targets>

Without this, the component will not appear in the Experience Builder component
picker, regardless of how the component is coded.
```

**Detection hint:** Any advice that says a component "should work the same" across internal Lightning pages and Experience Cloud without confirming `targetConfig` is a signal to verify the component metadata.
