# Examples - Flow Governance

## Example 1: Replace Generic Names With A Durable Convention

**Context:** The org has flows named `New Flow`, `Case Flow Copy`, and `Case Flow Final`.

**Problem:** Support cannot tell which automation owns case routing or which one is safe to modify.

**Solution:**

Adopt a convention that encodes purpose and trigger style.

```text
Before:
- New Flow
- Case Flow Copy
- Case Flow Final

After:
- Case_AfterSave_AssignOwner
- Case_Screen_CloseCaseWizard
- Case_Scheduled_SendEscalationReminders
```

**Why it works:** The portfolio becomes readable without opening each flow individually.

---

## Example 2: Activation Gate With Named Owner And Rollback Note

**Context:** A team frequently activates new flow versions during release windows with minimal metadata.

**Problem:** When issues appear, support does not know who owns the change or how to roll it back safely.

**Solution:**

Require a simple release record for every activation.

```text
Flow: Opportunity_AfterSave_SetRenewalRisk
Owner: Revenue Operations
Change summary: Added partner-channel branch
Validated by: Sandbox regression + fault-path review
Rollback plan: Reactivate version 12 if version 13 causes incorrect task creation
```

**Why it works:** Activation becomes an auditable operational event rather than an opaque config change.

---

## Anti-Pattern: Governance By Tribal Memory

**What practitioners do:** They assume the right admin or developer will remember what each flow does and which versions matter.

**What goes wrong:** Incident response slows down, duplicate automations accumulate, and retirement becomes risky because nobody trusts the portfolio map.

**Correct approach:** Put naming, ownership, and lifecycle expectations directly into the flow governance standard and enforce them at release time.
