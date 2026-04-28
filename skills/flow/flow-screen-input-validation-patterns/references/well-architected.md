# Well-Architected Notes — Flow Screen Input Validation Patterns

## Relevant Pillars

This skill primarily serves Reliability and Operational Excellence. Security is a secondary concern (defence-in-depth) but the screen-flow validation layer is explicitly **not** the security boundary — record-level Validation Rules + object permissions are.

- **Reliability** — Bad data captured at the UI layer cascades into broken reports, malformed integrations, and downstream automation failures. Component-level validation rejects bad data at the boundary, before it ever touches a record. The earlier in the data lifecycle a defect is caught, the lower the recovery cost; rejecting `asdf` in an Email field at the screen costs zero, fixing it in 50 000 Lead records six months later costs days of remediation.
- **Operational Excellence** — Clear, field-attached error messages reduce support tickets, end-user confusion, and admin debugging time. Inline rules also serve as living documentation of the data contract — a future developer reading the flow XML can see exactly what each input must satisfy without consulting external docs. The alternative (Decision-after-screen + a Display Text component holding the error) is an order of magnitude harder to read.
- **Security** (secondary) — Input validation is *part of* defence-in-depth but is not the security boundary. A user with API access bypasses the flow entirely and hits the object directly. Always pair flow validation with object-level Validation Rules and field-level security; treat the flow rule as the user-experience layer, the object rule as the authority. Never validate access control or authorization in a screen flow's `<validationRule>` — that's a permission set / sharing concern.
- **Performance** (limited applicability) — Validation rules execute client-side (or server-side for non-reactive); the cost is generally negligible. The exception is reactive validation with heavy formulas (`REGEX()` against long strings, multi-condition AND) firing on every keystroke — see `gotchas.md` Gotcha 10. For heavy formulas, prefer Next-time evaluation.
- **Scalability** — Validation rules don't impact bulk processing because Screen Flows are interactive (one user at a time). Scalability concerns belong to record-triggered flows, not screen flows.
- **User Experience** — The choice between inline (component-level), screen-level (Decision), and form-wide (final Decision before commit) directly determines how forgiving the form feels. Inline reactive validation feels like a modern web app; click-Next-then-error feels like a 1990s CGI form.

## Architectural Tradeoffs

The central tradeoff is **immediate user feedback** vs **formula complexity vs reactive component cost**. The decision matrix:

| Choice | When it wins | When it loses |
|---|---|---|
| Component-level non-reactive | Short forms (< 5 inputs), simple formulas, validation OK on Next | Long forms — user-feedback cycle is painful |
| Component-level reactive | Long forms, interdependent inputs, modern UX expectation | Heavy formulas (REGEX on long strings) cause perceived lag |
| Decision-after-screen for cross-screen | Validation needs prior-screen data | Anything that could live on the input itself — bad UX |
| Custom LWC `@api validate()` | Validation requires logic the formula language can't express | Higher maintenance cost; must implement reactivity manually |
| No flow validation, only object Validation Rule | Fast to ship; record-level rule still catches bad data | Bad UX — user clicks Next, flow runs DML, error surfaces as a runtime fault |

A second tradeoff is **single source of truth vs duplication**. Flow `<validationRule>` and object Validation Rule that enforce the same constraint must stay consistent. The cost of consistency is two places to update; the cost of inconsistency is silent data divergence. Treat the object rule as authoritative and derive the flow rule from it; document the derivation in the field's description.

A third tradeoff is **explicit per-field rules vs centralised "validation flow"**. Some teams centralise validation into a single Decision element (or even a sub-flow). This concentrates the logic but loses field-attachment, accessibility, and inline UX. Prefer per-field unless the validation truly spans multiple inputs in a way component-level can't express.

## Anti-Patterns

1. **Validation in a Decision after the screen** — The user has already clicked Next; the error feels like a server-side rejection rather than inline guidance. Move to a `<validationRule>` on the input. The Decision is reserved for cross-screen checks only.
2. **Treating `isRequired = true` as format validation** — `isRequired` blocks empty values; it does not validate format. A user types `asdf` in an Email field marked required and Next is allowed. Combine `isRequired` with a `<validationRule>` that checks format.
3. **Returning a string from the validation formula** — `IF(cond, "", "Error")` does not validate; the formula must return BOOLEAN. The user-facing string lives in `<errorMessage>`, not the formula.
4. **Cross-field rule on the first (independent) field** — When the user fills the first field, the second is null; the comparison short-circuits. Always put cross-field rules on the dependent (later) field.
5. **Trusting the flow's screen validation as the security boundary** — Anyone with API access bypasses the screen entirely. Always pair with object-level Validation Rules and field-level security. The screen rule is UX; the object rule is the authority.
6. **Hardcoded error messages in multilingual orgs** — English error text appears for French / Japanese / Spanish users. Use Custom Labels for the error message string where supported, or route through a Display Text fallback.
7. **`<validationRule>` block under a custom LWC's `<extensionName>`** — Silently ignored. Custom LWCs honour only `@api validate()`. Authors who don't know this ship a "validated" component that doesn't validate.

## Official Sources Used

- Salesforce Help — Screen Flow Input Components reference: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screen_input.htm
- Salesforce Help — Validate Screen Component Input in a Flow: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_input_validation.htm
- Salesforce Metadata API Developer Guide — Flow type schema (`<validationRule>` on `<fields>` elements): https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Salesforce Release Notes — Reactive Screen Components (Winter '24): https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_reactive_screens.htm
- Salesforce Developer Guide — Custom LWC Screen Components and `@api validate()`: https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-screen.html
- WCAG 2.1 SC 3.3.1 (Error Identification): https://www.w3.org/TR/WCAG21/#error-identification
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/well-architected
