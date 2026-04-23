# LLM Anti-Patterns — LWC Focus Management

## Anti-Pattern 1: Global `document.querySelector`

**What the LLM generates:** `document.querySelector('lightning-input').focus()`

**Why it happens:** standard web idiom.

**Correct pattern:** `this.template.querySelector(...)` inside the component;
public `@api focus()` on children.

## Anti-Pattern 2: Focus In `connectedCallback`

**What the LLM generates:** `connectedCallback() { this.focusInput(); }`

**Why it happens:** sounds like "after insert."

**Correct pattern:** `renderedCallback` with a one-time flag, or
microtask / `setTimeout(0)` before calling focus.

## Anti-Pattern 3: Focus Every Render

**What the LLM generates:** calling `.focus()` in `renderedCallback` with no
guard.

**Why it happens:** missing control flow.

**Correct pattern:** set a pending-focus flag when the state change requires
focus, clear it once focused.

## Anti-Pattern 4: Trap Without Restore

**What the LLM generates:** modal that traps Tab but never returns focus on
close.

**Why it happens:** trap is the harder half to write; restore gets skipped.

**Correct pattern:** always save `activeElement` on open and restore on
close.

## Anti-Pattern 5: Live-Region With Static Text

**What the LLM generates:** `<div role="status">Loaded</div>` statically.

**Why it happens:** intuition that role announces on render.

**Correct pattern:** the text inside the live region must change AFTER
creation for screen readers to announce.
