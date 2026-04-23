# OmniStudio vs Flow — Examples

## Example 1: Guided Policy Purchase

**Context:** Insurance customer journey with 7 screens, conditional underwriting questions, and a callout to a policy-issuance system.

**Decision:** OmniScript for UI, Integration Procedure + DataRaptor for backend shaping.

**Why:** Branching across 7 screens is OmniScript's sweet spot; external payload shape fits DataRaptor Transform cleanly.

---

## Example 2: Admin-Owned Case Intake

**Context:** Internal agents enter a case with 3 fields. Owned by admin team that ships weekly.

**Decision:** Screen Flow.

**Why:** OmniScript-tier tooling is overkill; DataPack deployment cost exceeds value for a 3-field form.

---

## Anti-Pattern: FlexCard Replacing A Record Page

A team replaced the standard record page with a FlexCard "for consistency." No FlexCard-specific features were in use. Result: every admin change requires a developer because FlexCard edits go through the designer, not the Page Layout editor. Reverted to Lightning Record Page.
