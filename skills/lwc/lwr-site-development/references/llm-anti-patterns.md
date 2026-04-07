# LLM Anti-Patterns — LWR Site Development

Common mistakes AI coding assistants make when generating or advising on LWR site development.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Aura Components for Use in LWR Sites

**What the LLM generates:** Code or advice suggesting an Aura component (`.cmp` file, `<aura:component>`) can be used on an LWR site by wrapping it in an LWC or adding it to the site's Experience Builder setup.

**Why it happens:** Training data includes extensive Aura community content predating LWR. LLMs conflate the Aura-based "Build Your Own" template with the LWR-based "Build Your Own (LWR)" template because both share similar names and community-building context. LLMs may also suggest Aura component wrappers as a compatibility shim, which does not work in LWR.

**Correct pattern:**

```xml
<!-- Correct: LWC component with lightningCommunity__Page target for LWR sites -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>
</LightningComponentBundle>
```

**Detection hint:** Any mention of `.cmp` files, `<aura:component>`, `aura:application`, `$A.createComponent`, or Aura component wrappers in the context of an LWR site is incorrect. Flag any recommendation to add Aura components to a Build Your Own (LWR) or Microsite (LWR) site.

---

## Anti-Pattern 2: Missing the `--dxp` CSS Hook Prefix for Custom Theming

**What the LLM generates:** Component CSS that uses hardcoded hex values or raw SLDS tokens (e.g., `--slds-g-color-brand-base-50`) for brand colors instead of `--dxp` theming hooks.

```css
/* Wrong: hardcoded or raw SLDS tokens */
.my-button {
    background-color: #0070d2;
    color: #ffffff;
}
```

**Why it happens:** LLMs trained on general LWC examples default to SLDS color tokens or hardcoded values because those work in Lightning Experience. LLMs are not consistently aware that LWR sites have a separate `--dxp` hook layer that bridges the Theme panel to component CSS.

**Correct pattern:**

```css
/* Correct: --dxp hooks connect to the Theme panel */
.my-button {
    background-color: var(--dxp-g-brand);
    color: var(--dxp-g-brand-contrast);
}

/* For fine-grained SLDS overrides where --dxp does not reach */
.my-button:hover {
    background-color: var(--dxp-g-brand-1);
}
```

**Detection hint:** Look for hardcoded hex color values or `--slds-g-color-*` tokens in component CSS intended for LWR sites. Any brand color that is not expressed as a `var(--dxp-*)` reference may break Theme panel responsiveness.

---

## Anti-Pattern 3: Forgetting to Republish After Component Code Changes

**What the LLM generates:** Deployment instructions that deploy a component fix via Salesforce CLI and then describe the change as "live" without mentioning that the LWR site must be republished.

**Why it happens:** In Aura sites and Lightning Experience, component changes go live immediately after deployment. LLMs trained primarily on general Salesforce deployment patterns assume the same behavior for LWR sites.

**Correct pattern:**

```
Deployment checklist for LWR site component changes:
1. Deploy component changes via `sf project deploy start` or change set
2. Verify the fix in Experience Builder preview (always shows current code)
3. Republish the site: Experience Builder > Publish
4. Confirm the fix on the live published site URL (not the preview URL)
```

**Detection hint:** Any deployment workflow for an LWR site that does not include an explicit "republish the site" step is incomplete. Look for instructions that say the change is "live" after a deploy without a publish step.

---

## Anti-Pattern 4: Using Aura Navigation APIs Instead of `lightning/navigation`

**What the LLM generates:** Navigation code using community-specific Aura patterns — `comm__namedPage` with `pageName` (deprecated), `comm:pageReference`, or Aura navigation service — instead of the LWC `lightning/navigation` module.

```javascript
// Wrong: Aura-style navigation or deprecated pageName attribute
navigateToPage() {
    const pageRef = {
        type: 'comm__namedPage',
        attributes: {
            pageName: 'home'  // pageName is deprecated; use name in LWR
        }
    };
}
```

**Why it happens:** LLMs trained on older Experience Cloud documentation include the `pageName` attribute (deprecated in Spring '20) and Aura navigation service patterns. LLMs may also suggest `standard__namedPage`, which is unsupported in LWR templates.

**Correct pattern:**

```javascript
// Correct: lightning/navigation with comm__namedPage using name attribute
import { LightningElement } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class MyNavComponent extends NavigationMixin(LightningElement) {
    navigateToHome() {
        this[NavigationMixin.Navigate]({
            type: 'comm__namedPage',
            attributes: {
                name: 'Home'  // name is the page API name; not pageName
            }
        });
    }
}
```

**Detection hint:** Flag any usage of `pageName` attribute (not `name`) in `comm__namedPage` page references. Flag any usage of `standard__namedPage` in LWR site context — unsupported; use `comm__namedPage`. Flag Aura navigation service imports or `$A.get("e.force:navigateToURL")` patterns.

---

## Anti-Pattern 5: Adding `lightningCommunity__Theme_Layout` Without a Default Slot

**What the LLM generates:** A theme layout LWC template that defines header and footer named slots but omits the unnamed default `<slot></slot>` for main content.

```html
<!-- Wrong: missing default slot — main content has nowhere to render -->
<template>
    <header>
        <slot name="header"></slot>
    </header>
    <footer>
        <slot name="footer"></slot>
    </footer>
</template>
```

**Why it happens:** LLMs generating theme layout components focus on the visible named regions (header, footer) and treat the main content slot as implicit or unnecessary. In Aura theme layouts, `{!v.body}` was the body placeholder — LLMs may omit the LWC equivalent.

**Correct pattern:**

```html
<!-- Correct: default unnamed slot is required for main content -->
<template>
    <header data-f6-region>
        <slot name="header"></slot>
    </header>
    <main data-f6-region>
        <!-- Required: unnamed default slot renders the page's main content -->
        <slot></slot>
    </main>
    <footer data-f6-region>
        <slot name="footer"></slot>
    </footer>
</template>
```

**Detection hint:** Any `lightningCommunity__Theme_Layout` component template that contains only named slots with no unnamed `<slot></slot>` is missing the main content region. The page will render a blank content area. Check for the presence of at least one unnamed `<slot></slot>` in every theme layout template.

---

## Anti-Pattern 6: Omitting `@slot` JSDoc Annotations from Layout Components

**What the LLM generates:** Page layout or theme layout LWC components with slots defined in the template but no `@slot` JSDoc annotations in the JavaScript class, or annotations placed after an import statement or inline comment instead of directly before the class declaration.

**Why it happens:** JSDoc-based slot registration is specific to the Experience Builder LWR pattern and is rarely covered in general LWC documentation or tutorials. LLMs may generate valid LWC slot syntax without knowing that the annotation is required for Experience Builder to recognize and expose the regions.

**Correct pattern:**

```javascript
// Correct: @slot annotations immediately before the class declaration
// No intervening code, comments, or blank-line blocks between annotation and class

/**
 * @slot header
 * @slot footer
 */
export default class MyThemeLayout extends LightningElement {}
```

**Detection hint:** Any `lightningCommunity__Page_Layout` or `lightningCommunity__Theme_Layout` component whose JavaScript file lacks `@slot` JSDoc annotations will have slots that do not appear as configurable regions in Experience Builder. Check that annotations appear immediately before the `export default class` statement with no intervening code.
