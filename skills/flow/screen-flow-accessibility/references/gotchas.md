# Screen Flow Accessibility — Gotchas

## 1. Help Text Is Not Always Announced

The help-text icon on Flow screen components relies on hover. If you want the
text announced, echo it as programmatic description.

## 2. Custom LWCs Reset Focus

A custom LWC dropped into a screen can capture and never release focus. Verify
`focus()` and `blur()` are intentional.

## 3. Navigation Buttons Are Not Skippable

On long screens, a keyboard user must tab through every field to reach Next.
Consider a skip link or split the screen.

## 4. Flow In Lightning Experience vs Flow In Experience Cloud

Rendering and focus differ. A flow that passes a11y in LEX can fail in
Experience Cloud due to theme and SLDS version differences. Test both.

## 5. Conditional Visibility Moves Focus

Revealing a hidden component can cause focus to jump or be lost. Manage focus
explicitly after a reveal.

## 6. Multi-Column Layouts Scramble Tab Order

DOM order and visual order can diverge. Confirm Tab order matches reading
order.

## 7. Required Field Styling Alone Is Not Enough

A red asterisk conveys nothing to assistive tech. Use `required` attribute
AND text "(required)" where appropriate.
