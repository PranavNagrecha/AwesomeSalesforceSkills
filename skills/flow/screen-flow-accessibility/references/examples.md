# Screen Flow Accessibility — Examples

## Example 1: Error Summary With Deep Links

On the "Review and Submit" screen, when validation fails:

- Render a Display Text at the top listing errors: "3 issues to resolve: 1. Date of Birth missing. 2. Postal Code invalid. 3. Consent not checked."
- Each item is a link that sets focus to the matching field (Custom LWC with `focus()` exposed).
- Focus jumps to the summary; screen readers announce "3 issues to resolve."

**Why:** one place summarizes errors, assistive tech announces once, the user can act.

---

## Example 2: Radio Group With Fieldset-Style Labeling

A risk-tolerance question with three options. Without explicit group labeling,
a screen reader reads each option in isolation ("low," "medium," "high") with
no context. The fix: a parent Display Text that programmatically precedes the
radio group with the question, plus a consistent label prop. Tested with NVDA
→ announces "Risk tolerance, radio group, 1 of 3, low."

---

## Example 3: Keyboard-Only Flow Walkthrough

QA script: "Navigate the Account Intake flow using Tab, Shift-Tab, Space,
Enter only."

- Page 1: all three inputs reachable; Next button receives focus after last input.
- Page 2: file upload triggered via Space; progress announced via live region.
- Page 3: radio group focuses as a unit; arrow keys move between options.

Failures to log: any field only reachable via mouse, any button that requires
a click, any error that only appears visually.

---

## Anti-Pattern: Placeholder As Label

A team used placeholder text in text inputs instead of labels. Sighted users
saw "Enter your email" until they clicked in — then the placeholder vanished.
Screen reader users heard "edit text" with no label. Fix: always a visible
label, placeholder is example-only.
