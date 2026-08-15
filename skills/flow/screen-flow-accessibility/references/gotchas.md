# Gotchas — Screen Flow Accessibility

Non-obvious behaviours that make an apparently accessible Screen Flow fail.

---

## Gotcha 1: The Target Standard Is WCAG 2.2 AA, Not 2.1

**What happens:** A team audits against WCAG 2.1 Level AA, passes, and is handed
a procurement questionnaire or a VPAT that assesses against 2.2.

**When it occurs:** Whenever the audit criteria were set from older guidance.
Salesforce's own statement is that "Lightning Experience follows the
internationally recognized best practices in Section 508 of the Rehabilitation
Act and the Web Content Accessibility Guidelines (WCAG) 2.2 Level AA to the
extent possible."

**How to avoid:** Audit against 2.2 AA. The delta that matters for a Screen Flow
is 2.4.11 Focus Not Obscured (Minimum), 2.5.7 Dragging Movements, 2.5.8 Target
Size (Minimum) at 24×24 CSS pixels, 3.3.7 Redundant Entry, and 3.3.8 Accessible
Authentication (Minimum). Note also that 4.1.1 Parsing was removed in 2.2 — an
old report flagging duplicate IDs may no longer describe a conformance failure.

---

## Gotcha 2: Help Text Is Behind an Interaction

**What happens:** Instructions essential to completing a field are placed in the
screen component's Help Text, and a meaningful share of users never see them.

**When it occurs:** Always. `helpText` renders as a help icon the user has to
hover or activate. It is discoverable to a sighted mouse user scanning the form
and to nobody else by default.

**How to avoid:** Apply the completion test — if a user who never opens the help
icon can still answer correctly, it belongs in Help Text. If they cannot, it
belongs in a Display Text field immediately before the input, in the reading
order.

---

## Gotcha 3: An Asterisk in the Label Is Not a Required Field

**What happens:** A screen reader announces "Postal code star, edit text." No
required semantics reach any assistive technology, and enforcement happens in a
Decision several elements later where the error has lost its connection to the
field.

**When it occurs:** Whenever `isRequired` is left false and the requiredness is
communicated by typing `*` into `fieldText`, or by styling.

**How to avoid:** Set `isRequired` to `true` and delete the asterisk from the
label. The marker and the announcement then come from the component,
consistently, in every language the org is translated into.

---

## Gotcha 4: Free-Floating Error Text Is Not Attached to Anything

**What happens:** Validation failures are surfaced as a Display Text field at the
top of the screen. Sighted users see a red block; screen reader users encounter
it only if they happen to navigate back to the top, and it is not associated with
any input.

**When it occurs:** Whenever validation is implemented as flow logic (a Decision
routing back to the screen with an error variable) rather than as the screen
field's own `validationRule`.

**How to avoid:** Use `validationRule` on the field, with an `errorMessage`
written as an instruction rather than a verdict — "Enter a postal code in the
format A1A 1A1," not "Invalid." The platform then attaches the message to its
field. Reserve a screen-level error summary for cross-field validation that has
no single field to attach to, and treat it as a supplement rather than the
mechanism.

---

## Gotcha 5: Multi-Column Sections Divorce Visual Order From DOM Order

**What happens:** Tab order goes right, then left, then down, then jumps back up.
Nobody notices because nobody tabbed through it.

**When it occurs:** Multi-column screen layouts are built from `RegionContainer`
and `Region` fields, and the DOM order is the metadata order — not the visual
grid position. Rearranging fields for visual balance rearranges the tab order
with no visible signal.

**How to avoid:** Author the metadata in reading order — first column then second
column for an LTR locale — and verify by tabbing through without a mouse. Do not
compensate in the metadata for RTL rendering; a mirrored visual layout from the
same DOM order is correct behaviour.

---

## Gotcha 6: Conditional Visibility Changes the Page After It Has Been Read

**What happens:** A checkbox reveals a field. A screen reader user who has
already navigated past that point never learns the field exists; a magnification
user may have it entirely outside their viewport.

**When it occurs:** Any `visibilityRule` on a screen field. The interaction is
self-evident when you can see the whole form and invisible when you cannot.

**How to avoid:** Place the revealed field immediately after its trigger in field
order, label the trigger with the outcome ("I have a promo code," not "Promo
code?"), and never make a revealed field required in a way the user cannot
discover. Then test at a narrow viewport: a reveal that pushes the Next button
under a sticky footer is 2.4.11 Focus Not Obscured.

---

## Gotcha 7: A Custom LWC Inherits None of the Screen's Accessibility

**What happens:** A screen full of standard components passes an audit, and the
one `ComponentInstance` field on it fails everything — no label association, no
focus management, no error announcement.

**When it occurs:** Always. Standard screen components carry those behaviours
because Salesforce implemented them. A custom component carries whatever its
author implemented, and the flow author usually did not write it and cannot see
inside it from Flow Builder.

**How to avoid:** Treat every `ComponentInstance` as a separate audit scope, and
refuse to sign off a screen containing an unaudited one. The component's
internals belong to `lwc/lwc-accessibility`; the flow author's job is knowing
which fields are components.

---

## Gotcha 8: A Flow That Passes in Lightning Experience Can Fail in Experience Cloud

**What happens:** The same flow, audited and passed in LEX, fails contrast and
focus checks on an Experience Cloud site.

**When it occurs:** The two containers apply different themes, different SLDS
versions, and different surrounding page structure. Brand colours on a site can
fail contrast against text that passed on the LEX background; the site's page
structure can change focus order; a sticky site header can obscure the focused
element in a way LEX never did.

**How to avoid:** Run the audit in every container the flow is published to. It
is the same script twice, and a meaningful share of real failures live only in
the second run.

---

## Gotcha 9: Long Screens Have No Skip Mechanism

**What happens:** A keyboard user on a twenty-field screen must tab through every
field to reach Next, every time they navigate back to correct something.

**When it occurs:** Screen Flows do not provide a skip link, and `showFooter`
controls whether the navigation footer renders at all rather than where it sits
in the tab order.

**How to avoid:** Treat screen length as an accessibility parameter. Splitting a
twenty-field screen into three shorter ones costs two extra Next clicks and
removes a large amount of repeated traversal. The trade is real — more screens
means more context switches — but the traversal cost compounds on every
correction pass, and the context-switch cost does not.

---

## Gotcha 10: `allowPause` Puts a Control in the Footer Whether You Want It or Not

**What happens:** An audit finds an unexplained "Pause" control in the tab order
that the flow author did not knowingly add.

**When it occurs:** `allowPause` on the Screen element defaults to enabled in
common authoring paths. It adds a footer control, which is another tab stop and
another thing a screen reader announces on every screen — and it introduces a
whole second lifecycle (paused interviews) that most flows have no reason to
support.

**How to avoid:** Set `allowPause` deliberately per screen. If the flow is short
enough to complete in one sitting, turning it off removes a tab stop from every
screen and removes the paused-interview population from the org's cleanup burden
— see `flow/flow-versioning-strategy` on what those interviews cost later.

---

## Gotcha 11: Rich Text in Display Text Can Carry Inaccessible Markup

**What happens:** A Display Text field contains an image with no alt text, a
heading level that skips from `h2` to `h4`, or a link labelled "click here."

**When it occurs:** `fieldText` accepts rich text, and the rich-text editor lets
authors insert images, headings, and links without prompting for alternatives or
checking hierarchy. The output is raw markup in the flow metadata, unreviewed.

**How to avoid:** Read the `fieldText` markup, not just the rendered preview.
Images that convey information need alt text; decorative ones need empty alt.
Heading levels descend by one. Link text describes the destination — "Read the
refund policy," not "click here." This is ordinary web content review; the trap
is that it is hidden inside a flow and nobody thinks to review it as content.

---

## Gotcha 12: Automated Checkers Pass Screens That Fail Users

**What happens:** An automated scan reports zero violations, and a screen reader
user cannot complete the flow.

**When it occurs:** Automated tooling reliably catches missing alt text, contrast
ratios, and missing programmatic labels. It cannot evaluate whether the focus
order is sensible, whether an error message tells the user what to do, whether a
revealed field is discoverable, or whether the announcement of a control conveys
its state. Those are the failures that actually block people.

**How to avoid:** Use automation as a floor, never as the sign-off. One manual
keyboard pass and one screen reader pass per flow catch the class of failure
tooling structurally cannot see. Budget them as work, not as a review step.
