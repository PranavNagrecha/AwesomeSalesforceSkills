# Examples — LWR Site Development

## Example 1: Custom Themed Customer Portal with Brand-Aligned Components

**Context:** A B2B company is building a customer support portal on Experience Cloud using the Build Your Own (LWR) template. They have a proprietary design system (custom fonts, brand colors, dark section backgrounds) that must be applied consistently across all pages. The team wants site admins to be able to update brand colors through the Experience Builder Theme panel without involving developers.

**Problem:** Without `--dxp` styling hooks, developers hardcode hex values in each component's CSS. Every brand update requires hunting down all CSS files and republishing. Section backgrounds that differ from the root background break color contrast because child components inherit the wrong root values.

**Solution:**

```css
/* customerPortalHero.css */
:host {
    /* Use --dxp-g-root hooks to define this section's background and text color.
       This ensures child base components (buttons, inputs) adapt automatically. */
    --dxp-g-root: var(--custom-section-bg, #1a1b1e);
    --dxp-g-root-contrast: #ffffff;

    /* Brand color flows from the Theme panel Brand Color property */
    --dxp-g-brand: var(--dxp-g-brand);
    --dxp-g-brand-contrast: var(--dxp-g-brand-contrast);
}

.hero-container {
    background-color: var(--dxp-g-root);
    color: var(--dxp-g-root-contrast);
    padding: var(--dxp-g-sizing-border-radius-medium, 1.5rem);
}

.hero-cta-button {
    background-color: var(--dxp-g-brand);
    color: var(--dxp-g-brand-contrast);
}
```

```xml
<!-- customerPortalHero.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Customer Portal Hero</masterLabel>
    <description>Full-width hero banner for the customer portal home page.</description>
    <targets>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightningCommunity__Default">
            <property type="String" name="headingText" default="Welcome" translatable="true"/>
            <property type="String" name="subheadingText" default="How can we help you today?" translatable="true"/>
            <property type="String" name="ctaLabel" default="Browse Support Articles" translatable="true"/>
            <property type="Color" name="sectionBackground" default="#1a1b1e"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why it works:** `--dxp-g-root` and `--dxp-g-brand` hooks cascade to all child base components within the hero section's scope. When a site admin updates the Brand Color in the Theme panel, the hero CTA button and all other brand-colored elements update automatically. Setting `--dxp-g-root` on a dark section ensures that child components like `lightning-button` and `lightning-input` derive their states correctly against the new background — preventing invisible text or inaccessible contrast ratios.

---

## Example 2: Microsite with Brand-Aligned LWC Theme Layout

**Context:** A marketing team is launching a product event microsite using the Microsite (LWR) template. They need a custom header with a centered logo and minimal navigation, and a branded footer with social links — neither of which is available in the default out-of-the-box theme layout component.

**Problem:** Without a custom theme layout component, the team is limited to the standard header/footer offered by the Microsite template. They cannot restructure the header layout, add custom navigation behavior, or integrate the event's unique brand identity.

**Solution:**

```html
<!-- eventThemeLayout.html -->
<template>
    <header data-f6-region class="event-header">
        <slot name="header"></slot>
    </header>
    <main data-f6-region class="event-content">
        <!-- Default slot: required for main content rendering in theme layouts -->
        <slot></slot>
    </main>
    <footer data-f6-region class="event-footer">
        <slot name="footer"></slot>
    </footer>
</template>
```

```javascript
// eventThemeLayout.js

/**
 * @slot header
 * @slot footer
 */
import { LightningElement, api } from 'lwc';

export default class EventThemeLayout extends LightningElement {
    @api brandLogoUrl;
    @api eventName;
}
```

```xml
<!-- eventThemeLayout.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Event Theme Layout</masterLabel>
    <targets>
        <target>lightningCommunity__Theme_Layout</target>
        <target>lightningCommunity__Default</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightningCommunity__Default">
            <property type="String" name="eventName" default="Our Event"/>
            <property type="String" name="brandLogoUrl" default=""/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

```css
/* eventThemeLayout.css */
.event-header {
    background-color: var(--dxp-g-root);
    border-bottom: 2px solid var(--dxp-g-brand);
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.event-content {
    min-height: 60vh;
    padding: var(--dxp-g-sizing-border-radius-medium, 2rem);
}

.event-footer {
    background-color: var(--dxp-g-root);
    padding: 1.5rem 2rem;
    text-align: center;
    color: var(--dxp-g-root-contrast);
}
```

**Why it works:** The `@slot` JSDoc annotations (placed directly before the class declaration, with no intervening code) tell Experience Builder which named regions to expose in the layout editor. The unnamed default `<slot></slot>` is required — without it, main page content has nowhere to render. The `data-f6-region` attributes enable F6 keyboard navigation between header, content, and footer regions, meeting accessibility requirements for screen reader users.

After deploying, the theme layout is assigned in Settings > Theme in Experience Builder. Site admins can then assign it to pages that need the event branding, overriding the default theme layout for those pages.

---

## Anti-Pattern: Adding Aura Components to an LWR Site

**What practitioners do:** A developer reuses an existing Aura component from a legacy community by adding it to the LWR site's package or referencing it in an LWC template via composition syntax.

**What goes wrong:** LWR sites do not support Aura components at all. The component simply does not appear in the Experience Builder Components panel. If the developer references it in an LWC template directly, the deployment may succeed but the component either silently fails to render or throws a runtime error. There is no graceful degradation or compatibility shim.

**Correct approach:** Rewrite the Aura component as an LWC component with the appropriate `lightningCommunity__*` targets. All layout, navigation, and event patterns must be reimplemented in LWC idioms (named slots instead of `{!v.body}`, `CustomEvent` instead of application events, `lightning/navigation` instead of Aura navigation service).
