# Well-Architected Notes — Screen Flow Accessibility

## Relevant Pillars

- **User Experience** — accessibility work in a Screen Flow is mostly the same
  work as making the screen comprehensible: a visible label, an instruction the
  user can act on, an error that says what to do, and a reading order that
  matches the layout. Nearly every fix improves the experience for everyone.
- **Security and Compliance** — Salesforce targets Section 508 and WCAG 2.2 Level
  AA, and publishes Accessibility Conformance Reports per product. An internal
  flow that locks out employees using assistive technology is a compliance
  exposure, and one on a public Experience Cloud site is a larger one.
- **Adaptable** — the declarative levers (`isRequired`, `validationRule`, field
  order) are maintained by the platform across SLDS versions. A custom component
  that reimplements them becomes the team's maintenance burden indefinitely,
  which is the strongest argument for exhausting the declarative options first.

## Architectural Tradeoffs

- **Declarative properties vs a custom LWC:** the platform maintains the
  accessibility of standard components across releases; a component moves that
  burden to the team permanently. Take the trade when the requirement genuinely
  cannot be expressed declaratively, and state explicitly that the component's
  internals are now in audit scope.
- **One long screen vs several short ones:** long screens reduce context switches
  and multiply keyboard traversal on every correction pass; short screens invert
  both. The traversal cost compounds and the context-switch cost does not, which
  usually favours splitting — but the flow gains screens, which is more surface
  to audit.
- **Field-level validation vs a screen-level summary:** `validationRule` attaches
  the message to its field, which is what makes it announced in context. A
  summary is scannable and is the only option for cross-field rules. Do the first
  always and the second when there is no single field to attach to.
- **Hard-blocking validation vs soft warnings:** hard blocking is unambiguous for
  assistive technology and more frustrating for everyone; a warning that can be
  dismissed is gentler and easier to miss entirely without sight. Block on
  correctness, warn on advisability.
- **`allowPause` on vs off:** pausing is a genuine accessibility affordance for
  users who need to complete a task across sessions. It also adds a tab stop and
  an announcement on every screen, and creates paused interviews that become a
  version-cleanup burden. Decide per flow, not by default.

## Hygiene

- The audit target is WCAG 2.2 Level AA, and the checklist names the criteria.
- Every input's requiredness comes from `isRequired`, never from an asterisk.
- Every field-level validation uses `validationRule` with an `errorMessage`
  written as an instruction.
- Content required to answer a field is in Display Text, not `helpText`.
- Metadata field order matches reading order; verified by tabbing, not by
  inspection.
- Conditionally revealed fields sit immediately after their trigger.
- Every `ComponentInstance` on a screen has its own accessibility sign-off.
- The audit is run in every container the flow is published to.
- One manual keyboard pass and one screen reader pass per flow, budgeted as work.

## Related

- `lwc/lwc-accessibility` — the internals of any custom component on a screen.
  This skill's boundary is the screen; that skill owns what is inside a
  `ComponentInstance`.
- `flow/flow-screen-input-validation-patterns` — validation design in depth.
- `flow/flow-screen-lwc-components` — building and wiring screen components.
- `flow/screen-flow-choice-component-selection` — choosing between radio groups,
  picklists, and checkbox groups, which is partly an accessibility decision.
- `flow/pause-elements-and-wait-events` — what `allowPause` creates downstream.

## Official Sources Used

- Accessibility Standards (Salesforce Help) — "Lightning Experience follows the internationally recognized best practices in Section 508 of the Rehabilitation Act and the Web Content Accessibility Guidelines (WCAG) 2.2 Level AA to the extent possible" — https://help.salesforce.com/s/articleView?id=sf.accessibility_overview.htm&type=5
- Product Accessibility Status (Salesforce) — Accessibility Conformance Reports and VPATs per product — https://www.salesforce.com/company/legal/508_accessibility/
- Salesforce Compliance — WCAG 2.2 AA — https://compliance.salesforce.com/en/categories/wcag
- What's New in WCAG 2.2 (W3C) — the nine added success criteria including 2.4.11 Focus Not Obscured (Minimum) AA, 2.5.7 Dragging Movements AA, 2.5.8 Target Size (Minimum) AA, 3.2.6 Consistent Help A, 3.3.7 Redundant Entry A, 3.3.8 Accessible Authentication (Minimum) AA; and the removal of 4.1.1 Parsing — https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- Web Content Accessibility Guidelines (WCAG) 2.2 (W3C Recommendation) — https://www.w3.org/TR/WCAG22/
- Flow metadata type — `FlowScreen` (`allowBack`, `allowFinish`, `allowPause`, `showFooter`, `showHeader`, `helpText`, `pausedText`, `nextOrFinishButtonLabel`) and `FlowScreenField` (`fieldText`, `fieldType`, `helpText`, `isRequired`, `dataType`, `choiceReferences`, `validationRule`, `visibilityRule`, `extensionName`, `inputParameters`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Screen Element (Salesforce Help) — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screen.htm&type=5
- Salesforce Lightning Design System — Accessibility — https://www.lightningdesignsystem.com/accessibility/overview/
- Salesforce Well-Architected — Adaptable — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable
