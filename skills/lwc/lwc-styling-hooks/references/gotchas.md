# Gotchas — LWC Styling Hooks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Hook Names Are Case-Sensitive And Hyphenated

**What happens:** A CSS declaration like `--SLDS-C-Button-Color-Background: #123456` compiles without error, the page renders normally, and the theme change simply does not apply. There is no console warning because CSS custom properties with unknown names are valid CSS.

**When it occurs:** Most often when a developer retypes a hook name from memory, pastes from a PDF or slide, or lets an LLM guess at the name.

**How to avoid:** Copy hook names from the SLDS Styling Hooks reference. Use the checker script to flag suspicious custom properties. Treat the hook name as an exact string match.

---

## Gotcha 2: Not Every Internal Property Has A Public Hook

**What happens:** A developer wants to change something subtle — the exact padding of a `lightning-combobox` dropdown, the icon color in a specific variant — and finds no hook covers it. They're tempted to reach into internal SLDS classes as a workaround.

**When it occurs:** Detail-level visual changes beyond the documented hook surface.

**How to avoid:** If no hook exists, treat it as a gap to raise with Salesforce (IdeaExchange, SLDS GitHub) rather than an invitation to override internals. Consider whether the visual change is actually necessary, or whether the current base-component behavior is acceptable.

---

## Gotcha 3: Shadow DOM Blocks Parent CSS From Inner SLDS Classes

**What happens:** A rule like `my-parent lightning-button .slds-button_brand { ... }` appears to make sense but is completely blocked by the shadow boundary around `lightning-button`. Browser devtools show the rule matching zero elements.

**When it occurs:** Every time a developer tries to style base-component internals from the outside. This is the isolation guarantee the shadow DOM exists to provide.

**How to avoid:** Use styling hooks. CSS custom properties inherit through the shadow DOM and are the only reliable vector for theming base components.

---

## Gotcha 4: `!important` On A Hook Declaration Defeats The Cascade

**What happens:** A developer adds `!important` to a hook value thinking it will "make the theme win" against some imagined conflict. Later, a deliberate override at a narrower scope — exactly the scope specificity the cascade is designed for — cannot override the hook.

**When it occurs:** When `!important` is reached for as a debug strategy instead of as a last-resort tool.

**How to avoid:** Remove `!important` from hook declarations. If cascade specificity is wrong, fix the scope: set the hook on a narrower selector (`:host` of the specific LWC, a scoped class) rather than bludgeoning with `!important`.

---

## Gotcha 5: SLDS 2 Renames And Deprecates Some SLDS 1 Hooks

**What happens:** A codebase that works in SLDS 1 loses its theming when the org switches on SLDS 2 ("2e") because the hook names the code uses have been renamed or deprecated in the new system.

**When it occurs:** During SLDS 2 migration, and any time a new LWC is written copying patterns from old SLDS 1 examples.

**How to avoid:** Run SLDS Validator / SLDS Linter against the LWC source. Consult the SLDS 2 migration documentation for deprecated hook pairs. Prefer semantic global hooks where they exist, since they are more likely to have stable SLDS 2 equivalents.

---

## Gotcha 6: `:host` Has No Effect In Light-DOM LWCs

**What happens:** A developer writes `:host { --slds-c-button-color-background: ...; }` in a light-DOM LWC and the theme does not apply. `:host` only has meaning inside shadow roots.

**When it occurs:** Any time a component is declared as light DOM (`static renderMode = 'light'`) but the developer keeps writing shadow-DOM style selectors out of habit.

**How to avoid:** In light-DOM LWCs, set hooks on the component's root element via a component-specific class selector, or on a parent that wraps the component. Check the LWC's render mode before choosing the selector.

---

## Gotcha 7: Experience Cloud Theme Layer Can Outrank Component Hooks

**What happens:** An LWC sets a local component hook on `:host`, but the rendered color still matches the site's brand instead of the override. The site's theme layer has set the same hook at a higher scope that already inherits into the component.

**When it occurs:** On Experience Cloud sites where the theme or branding set supplies global and component hooks at the site root.

**How to avoid:** Remember the cascade — site root wins unless a narrower scope sets a later value. If you truly need an LWC-local override, ensure your `:host` hook matches the name the base component actually reads, and verify in devtools which custom property is resolving where.
