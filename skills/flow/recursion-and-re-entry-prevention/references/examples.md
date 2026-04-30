# Examples — Flow Recursion and Re-Entry Prevention

## Example 1: Self-re-entry on the same record (state-guard fix)

**Context:** A record-triggered Flow on `Account` fires on update with entry condition `ISCHANGED({!$Record.AccountStatus__c})`. The Flow's purpose is to set `Last_Status_Change__c = NOW()`. The Flow's own update of `Last_Status_Change__c` doesn't satisfy the entry condition (the trigger field is `AccountStatus__c`, not the timestamp), so this case alone is fine — but a separate Flow on the same object fires when `Last_Status_Change__c` changes and updates `AccountStatus__c` for tracking. Now both Flows ping-pong.

**Problem:** After 16 cascading updates, the platform throws `System.LimitException: Maximum trigger depth exceeded`.

**Solution:** Tighten Flow A's entry criteria to exclude updates triggered by Flow B's audit logic.

```text
Flow A — Status Change Tracker (after-save, Account)

  Trigger: A record is updated
  Condition Requirements: All Conditions Are Met
    1. ISCHANGED({!$Record.AccountStatus__c})
    2. {!$Record.AccountStatus__c} <> {!$Record.Last_Tracked_Status__c}

  Actions:
    Update $Record:
      Last_Status_Change__c = NOW()
      Last_Tracked_Status__c = $Record.AccountStatus__c   // breaks the loop
```

**Why it works:** Flow B's audit update sets `AccountStatus__c` to a value that equals what Flow A wrote into `Last_Tracked_Status__c`. On Flow B's re-trigger of Flow A, condition 2 is false (current value matches last tracked), so Flow A exits without re-firing the audit cascade.

---

## Example 2: Hash-based idempotency for callout-shaped Flow

**Context:** A record-triggered Flow on `Order__c` fires when any of `Total_Amount__c`, `Discount__c`, or `Shipping_Cost__c` changes. The Flow recalculates `Final_Price__c`. An external integration also writes back to `Total_Amount__c` periodically, which re-triggers the Flow even though nothing meaningful changed (the integration is idempotent and may write the same value).

**Problem:** The Flow re-fires on every integration write, costing CPU time and occasionally racing with concurrent user edits.

**Solution:** Hash the input fields and skip if unchanged.

```text
Flow — Order Final Price Calc (after-save, Order__c)

  Trigger: A record is updated
  Condition Requirements:
    OR(ISCHANGED({!$Record.Total_Amount__c}),
       ISCHANGED({!$Record.Discount__c}),
       ISCHANGED({!$Record.Shipping_Cost__c}))

  Steps:
    1. Assignment: pricingHash =
         TEXT({!$Record.Total_Amount__c}) + '|' +
         TEXT({!$Record.Discount__c}) + '|' +
         TEXT({!$Record.Shipping_Cost__c})

    2. Decision: pricingHash == {!$Record.Last_Pricing_Hash__c}?
         Yes → End of Flow.
         No  → continue.

    3. Assignment: Final_Price__c = Total_Amount__c - Discount__c + Shipping_Cost__c

    4. Update $Record:
         Final_Price__c = {!Final_Price__c}
         Last_Pricing_Hash__c = {!pricingHash}
```

**Why it works:** When the integration writes back the same `Total_Amount__c`, `pricingHash` equals `Last_Pricing_Hash__c` and the Flow exits at step 2. When a user edits the value, the hash differs and the Flow proceeds. The Flow's own write at step 4 updates `Last_Pricing_Hash__c` so the next firing of the Flow finds an exact match and exits.

---

## Example 3: Cross-object cascade with shared lock

**Context:** A record-triggered Flow on `Account` updates the related `Primary_Contact__r` whenever the account's `Mailing_Address__c` changes (synchronizing addresses). A separate Flow on `Contact` runs whenever a Contact's `MailingStreet` changes, updating the parent Account's `Last_Contact_Sync__c` timestamp. The two flows trigger each other.

**Problem:** Account → Contact update → Contact's flow → Account update → Account's flow → ... cascades to depth 16.

**Solution:** Add `Sync_In_Progress__c` to Account; have Account's Flow set it during its run; have Contact's Flow read it from the parent and exit early.

```text
Account Flow — Sync Address to Primary Contact (after-save):

  Trigger: A record is updated
  Condition Requirements: ISCHANGED({!$Record.Mailing_Address__c})
                          AND Sync_In_Progress__c = FALSE

  Steps:
    1. Update $Record: Sync_In_Progress__c = TRUE
    2. Get Records: Primary Contact for this Account
    3. Update Records: Contact.MailingStreet = $Record.Mailing_Address__c
    4. Update $Record: Sync_In_Progress__c = FALSE


Contact Flow — Track Address Changes (after-save):

  Trigger: A record is updated
  Condition Requirements: ISCHANGED({!$Record.MailingStreet})
                          AND $Record.Account.Sync_In_Progress__c = FALSE

  Steps:
    1. Update Records: Account.Last_Contact_Sync__c = NOW()
```

**Why it works:** When Account's Flow performs step 3, the resulting Contact update fires Contact's Flow — which reads `$Record.Account.Sync_In_Progress__c = TRUE` and exits at the entry condition. Account's step 4 then unsets the flag. A user-driven Contact edit (independent of Account's automation) finds `Sync_In_Progress__c = FALSE` and proceeds normally.

**Caveats:** The lock field needs to be readable from Contact via `$Record.Account.Sync_In_Progress__c`, which requires a regular Account lookup (already present on Contact via `AccountId`). Cross-object reads of parent fields work in entry conditions for after-save Flows.

---

## Anti-Pattern: time-window throttle as the only recursion guard

**What practitioners do:**

```text
Flow steps:
  1. Decision: Has Last_Status_Change__c been updated in the past 1 minute?
       Yes → End (assume already running).
       No  → continue.
  2. ... work ...
  3. Update Last_Status_Change__c = NOW().
```

**What goes wrong:** The "1 minute" threshold is brittle — slow async transactions can stretch beyond it, causing real updates to be skipped. Worse, two near-simultaneous user edits from different sessions both fire the Flow within seconds, and the second is silently dropped because the timestamp isn't 1 minute stale.

**Correct approach:** Use a deterministic guard. State-based (Pattern 1), hash-based (Pattern 2), or lock-based (Pattern 3) all give exact, reproducible behavior. Time-based "throttle" guards introduce race conditions and silent data loss.
