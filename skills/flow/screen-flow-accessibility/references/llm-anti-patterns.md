# LLM Anti-Patterns — Screen Flow Accessibility

## Anti-Pattern 1: Recommend Placeholder-Only Labels

**What the LLM generates:** "Add placeholder text to the input for clarity."

**Why it happens:** placeholders look clean.

**Correct pattern:** visible label + optional placeholder for example input.
Labels carry semantics.

## Anti-Pattern 2: "Just Make Errors Red"

**What the LLM generates:** CSS-only styling for validation failure.

**Why it happens:** visual intuition dominates.

**Correct pattern:** color + text + icon + ARIA. Color alone fails WCAG 1.4.1.

## Anti-Pattern 3: Skip A11y Audit Because "Flow Is Salesforce-Native"

**What the LLM generates:** "Standard Flow components are accessible by
default."

**Why it happens:** half-truth. Components are partially accessible; flow
design can still fail.

**Correct pattern:** audit the full flow, not just component primitives.

## Anti-Pattern 4: Treat Screen Reader Testing As Optional

**What the LLM generates:** checklist with no mention of NVDA / VoiceOver.

**Why it happens:** automated checkers miss most a11y failures.

**Correct pattern:** one pass with a real screen reader catches what tooling
misses.

## Anti-Pattern 5: Design For Sighted Keyboard Users Only

**What the LLM generates:** "Ensure Tab reaches all fields."

**Why it happens:** keyboard is confused with a11y.

**Correct pattern:** keyboard is one of several assistive modalities. Also
test screen readers, zoom, and high-contrast modes.
