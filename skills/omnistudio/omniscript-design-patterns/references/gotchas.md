# Gotchas — OmniScript Design Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## UX Debt Builds Faster Than Technical Debt In Large Scripts

**What happens:** The script technically works, but users abandon it or support teams struggle to explain where they are in the journey.

**When it occurs:** Step count grows without a clear milestone model.

**How to avoid:** Design around meaningful user checkpoints, not just implementation convenience.

---

## Save And Resume Can Reopen A Different World

**What happens:** A user resumes the journey later, but backend data or eligibility conditions have changed.

**When it occurs:** Long-running journeys preserve state without considering how external context might drift.

**How to avoid:** Define what must be revalidated when a saved journey is resumed.

---

## Custom Components Increase Operational Surface Area

**What happens:** The script becomes harder to debug because a custom LWC or remote action introduces separate failure modes.

**When it occurs:** Teams solve every edge case by embedding another custom component.

**How to avoid:** Use custom components selectively and document their contract with the OmniScript clearly.
