# LLM Anti-Patterns — LWC Styling Hooks

Common mistakes AI coding assistants make when generating or advising on SLDS Styling Hooks.
These patterns help the consuming agent self-check its own output before shipping.

## Anti-Pattern 1: Targeting Internal SLDS Classes With Raw CSS

**What the LLM generates:**

```css
.my-card .slds-button_brand {
    background: #ff0000;
    color: #ffffff;
}
```

**Why it happens:** LLMs trained on generic web-CSS examples reach for selector-based overrides because that is how theming works in non-Salesforce ecosystems. They treat `.slds-button_brand` as if it were a public CSS class in a framework like Bootstrap.

**Correct pattern:**

```css
:host {
    --slds-c-button-color-background: #ff0000;
    --slds-c-button-text-color: #ffffff;
}
```

**Detection hint:** grep for `\.slds-[a-z_-]+\s*\{` in `lwc/**/*.css`. Any match is a candidate for removal.

---

## Anti-Pattern 2: Inline `style` Attributes Instead Of Hooks

**What the LLM generates:**

```html
<lightning-button
    label="Save"
    variant="brand"
    style="background: #ff0000; color: white;"
></lightning-button>
```

**Why it happens:** Inline `style` is the quickest path the model sees and it "works" in the preview, so the model settles for it. It doesn't travel with the theme and it fights the component's own styling logic.

**Correct pattern:**

```css
/* In the consuming LWC's CSS */
:host {
    --slds-c-button-color-background: var(--slds-g-color-accent-warning-base-50);
}
```

**Detection hint:** grep for `style="[^"]*(background|color|border)` in `lwc/**/*.html` on Lightning base components.

---

## Anti-Pattern 3: Inventing Hook Names That Do Not Exist

**What the LLM generates:**

```css
:host {
    --slds-button-bg: #0b5cab;
    --slds-button-fg: white;
}
```

**Why it happens:** The model pattern-matches on the shape `--slds-<something>-<something>` and makes up plausible-sounding names. The page renders unchanged and there is no error, so the mistake is invisible without a visual check.

**Correct pattern:**

```css
:host {
    --slds-c-button-color-background: #0b5cab;
    --slds-c-button-text-color: white;
}
```

**Detection hint:** flag any `--slds-` or `--sds-` custom property that does not start with `--slds-c-`, `--slds-g-`, or `--sds-c-`. The tier prefix is the fastest integrity check.

---

## Anti-Pattern 4: Using `!important` On Hook Values Inside Shadow DOM

**What the LLM generates:**

```css
:host {
    --slds-c-card-color-background: #f4f4f4 !important;
}
```

**Why it happens:** When the theme appears not to apply, the model reaches for `!important` the way it would in a plain web page. But the real problem is usually a wrong hook name or a parent scope overriding the hook — `!important` does not fix either and blocks legitimate future overrides.

**Correct pattern:**

```css
:host {
    --slds-c-card-color-background: #f4f4f4;
}
```

If a parent scope is winning, set the hook at that parent scope instead of escalating priority.

**Detection hint:** grep for `--slds-.*!important` or `--sds-.*!important` in `lwc/**/*.css`.

---

## Anti-Pattern 5: Shipping SLDS 1 Hook Names For An SLDS 2 Org

**What the LLM generates:** Code that uses older SLDS 1 hook names (or hex values) without running SLDS Validator / SLDS Linter and without checking the SLDS 2 deprecation list. The component themes correctly today and fails when the org migrates to SLDS 2.

**Why it happens:** The model's training data predates or underweights SLDS 2, so it defaults to whatever pattern was most common in older examples.

**Correct pattern:** Before finalizing theming code, run:

```
sf slds lint <path>
```

or the SLDS Validator equivalent. Cross-reference flagged hooks against the SLDS 2 migration guide and update to the semantic equivalents (typically an `--slds-g-color-*` hook or a renamed `--slds-c-*` hook).

**Detection hint:** run SLDS Validator in CI. Any deprecation warning in LWC CSS is a blocker for SLDS 2 migration.
