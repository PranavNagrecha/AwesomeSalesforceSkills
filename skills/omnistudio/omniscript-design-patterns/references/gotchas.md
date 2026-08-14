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

---

## OmniScript-Only Validation Is Not a Server Boundary

**What happens:** Step conditions, Set Errors, and pattern messages live in the OmniScript. Direct IP / Apex / `GenericInvoke2NoCont` callers skip them. Under System Mode the write still happens.

**When it occurs:** Guest applications that "validate on the step" and trust the Remote Action.

**How to avoid:** Re-validate in the Remote Action / IP. Field allowlists on writes. The script is UX.

---

## Typeahead Turbo Is a Per-Keystroke DataRaptor

**What happens:** Type Ahead / Type Ahead Turbo fires a DR or IP on each keystroke. On a guest script that is a DoS and an exfil vector (suggestions leak records the guest should not list).

**When it occurs:** "Search-as-you-type against Contact."

**How to avoid:** Min characters, debounce, `ignoreCache` as required, no PII in suggestion labels. Prefer a `with sharing` picklist Remote Action over Turbo against objects the guest can query. If you do not need Typeahead, do not add it.

---

## Many Remote / IP Actions vs One Orchestrating IP

**What happens:** A step grows 6–9 Integration Procedure Actions plus Remote Actions. Each is a round trip; nested IPs add another.

**How to avoid:** Default to **one IP Action** per user intent (`omnistudio-remote-actions`). The OmniScript stays UI.
