# LLM Anti-Patterns — Screen Flow Accessibility

Mistakes AI assistants reliably make when asked to make a Screen Flow accessible.

---

## Anti-Pattern 1: Auditing Against WCAG 2.1 When the Target Is 2.2

**What the LLM generates:** a checklist headed "WCAG 2.1 Level AA," with no
mention of the criteria added in 2.2.

**Why it happens:** 2.1 dominates the training corpus by volume — it was the
reference standard for years and most accessibility guidance written to date
targets it.

**Correct pattern:** Salesforce states that Lightning Experience follows Section
508 and WCAG 2.2 Level AA to the extent possible. Audit against 2.2. The delta
that matters here is 2.4.11 Focus Not Obscured (Minimum), 2.5.7 Dragging
Movements, 2.5.8 Target Size (Minimum) at 24×24 CSS pixels, 3.3.7 Redundant Entry
and 3.3.8 Accessible Authentication (Minimum) — plus the removal of 4.1.1
Parsing, which means an old duplicate-ID finding may no longer be a failure.

**Detection hint:** "WCAG 2.1" as the stated target in a Salesforce
accessibility deliverable.

---

## Anti-Pattern 2: Prescribing ARIA Attributes on Standard Screen Components

**What the LLM generates:** "add `aria-describedby` to the input and
`aria-live="polite"` to the error region," written as though the flow author can
set attributes on a screen field.

**Why it happens:** ARIA is the vocabulary of the model's web-accessibility
training data, and the guidance is correct for hand-written HTML. Nothing in the
prompt signals that the author is editing declarative metadata.

**Correct pattern:** a Screen Flow author cannot set arbitrary attributes on
standard components. The available levers are metadata properties — `isRequired`
for required semantics, `validationRule` with an `errorMessage` for field-attached
errors, `fieldText` for the label, field order for reading order, `visibilityRule`
for conditional content. ARIA advice applies only inside a custom LWC, which is
`lwc/lwc-accessibility`'s scope.

**Detection hint:** any `aria-*` attribute recommended for a `<fields>` element
whose `fieldType` is not `ComponentInstance`.

---

## Anti-Pattern 3: Asterisk-in-the-Label for Required Fields

**What the LLM generates:** `<fieldText>Postal code *</fieldText>` with
`isRequired` left false, or CSS advice to style required labels red.

**Why it happens:** the asterisk convention is ubiquitous in form design and
reads as the standard solution. The `isRequired` property is one line in the
metadata and easy to overlook.

**Correct pattern:** set `isRequired` to `true` and remove the asterisk. The
marker, the announcement, and the translated text then come from the component.
An asterisk typed into a label is a character a screen reader reads as "star" and
no assistive technology treats as a requirement.

**Detection hint:** `*` in a `<fieldText>` value.

---

## Anti-Pattern 4: An Error Summary Instead of Field-Level Validation

**What the LLM generates:** an elaborate pattern where a Decision collects
validation failures into a variable, routes back to the screen, and renders them
in a Display Text block at the top with links to each field.

**Why it happens:** the error-summary pattern is genuinely good practice on
hand-built web forms and is heavily documented. The model reproduces the shape
without the platform's own affordance.

**Correct pattern:** `validationRule` on the screen field attaches the message to
its field, which is what makes it announced in context. Write the `errorMessage`
as an instruction, not a verdict. A screen-level summary is a supplement for
cross-field validation with no single field to attach to — not the mechanism.
And the "links to each field" part usually requires a custom LWC to implement
focus movement, which quietly turns a declarative screen into a component audit.

**Detection hint:** a validation design with no `<validationRule>` in it.

---

## Anti-Pattern 5: Treating Help Text as a Description

**What the LLM generates:** "put the field guidance in the Help Text so the form
stays clean."

**Why it happens:** it is what the property is named, and it produces a tidier
screen. The rendering behaviour is not visible from the metadata.

**Correct pattern:** `helpText` renders as an icon the user must hover or
activate. Content required in order to answer the field correctly must be in a
Display Text field in the reading order. The test: if a user who never opens the
help icon can still complete the field, it belongs in Help Text.

**Detection hint:** a `<helpText>` value containing an instruction with an
imperative verb, or containing the field's format requirements.

---

## Anti-Pattern 6: Claiming Standard Components Make the Flow Accessible

**What the LLM generates:** "Salesforce's standard screen components are
accessible out of the box, so the flow meets WCAG."

**Why it happens:** it is a half-truth. The components do carry label
association, required semantics, and error announcement — which makes the claim
feel supported.

**Correct pattern:** component-level accessibility does not produce
screen-level accessibility. Focus order, whether an error tells the user what to
do, whether a conditionally revealed field is discoverable, screen length, and
contrast against the host container's theme are all flow-author decisions that
standard components cannot make. And a single `ComponentInstance` field brings in
an entire unaudited scope.

**Detection hint:** an accessibility sign-off whose justification is the
component library.

---

## Anti-Pattern 7: Auditing Only in Lightning Experience

**What the LLM generates:** a test plan that names one container, usually LEX,
for a flow that is published to an Experience Cloud site.

**Why it happens:** the flow is one artifact, so it reads as one thing to test.
The container's contribution to the rendered result is not visible in the flow
metadata.

**Correct pattern:** the two containers apply different themes, different SLDS
versions, and different page structure. Contrast, focus order, and focus
obscuring can all differ. Run the audit in every container the flow is actually
published to.

**Detection hint:** an audit plan with no container list, for a flow whose
metadata or description mentions a community or site.

---

## Anti-Pattern 8: Automated Scan as the Sign-Off

**What the LLM generates:** "run an automated accessibility checker; if it
reports no violations, the flow is compliant."

**Why it happens:** it produces a clean binary result, which is what a
verification step wants, and automated tooling is real and useful.

**Correct pattern:** automated tooling catches missing alt text, contrast, and
missing programmatic labels. It structurally cannot evaluate focus order,
whether an error message is actionable, whether a revealed field is
discoverable, or whether a control's announcement conveys its state — which is
where the failures that block people live. Use it as a floor. Budget one manual
keyboard pass and one screen reader pass per flow as work.

**Detection hint:** a verification section naming only a scanning tool, with no
keyboard walk and no screen reader pass.

---

## Anti-Pattern 9: Recommending a Custom LWC to Fix an Accessibility Gap

**What the LLM generates:** a custom component to implement a focus-managing
error summary, an accessible date picker, or a skip link.

**Why it happens:** the model can write the component, and writing code feels
like a more complete answer than rearranging metadata.

**Correct pattern:** a custom component converts a screen whose accessibility the
platform maintains into one the team maintains, forever, across every SLDS
version. Sometimes that is the right trade. It is not the right trade for
problems that field order, `isRequired`, `validationRule`, and splitting a long
screen already solve. Exhaust the declarative levers first, and when a component
genuinely is required, say explicitly that its internals are now in scope for
`lwc/lwc-accessibility`.

**Detection hint:** a custom LWC proposed for a requirement expressible as
`isRequired`, `validationRule`, field ordering, or fewer fields per screen.
