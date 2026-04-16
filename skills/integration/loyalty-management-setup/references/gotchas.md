# Gotchas — Loyalty Management Setup

## Gotcha 1: DPE Batch Jobs Are Not Auto-Scheduled After Program Setup

**What happens:** Members accumulate qualifying points and meet tier thresholds but are never promoted to higher tiers. The tier assessment appears broken.

**When it occurs:** After initial Loyalty Program setup, when practitioners assume the DPE tier-processing jobs run automatically.

**How to avoid:** After program setup, explicitly navigate to Setup > Data Processing Engine, find all DPE definitions created for the loyalty program, activate each one, and schedule them. Without activation, tier processing never runs.

---

## Gotcha 2: One Qualifying Currency Per Tier Group Is a Hard Constraint

**What happens:** A program designer wants two independent tier tracks (e.g., one based on spend and one based on engagement) but tries to associate both qualifying currencies to a single tier group. The setup fails or produces incorrect tier calculations.

**When it occurs:** When program designs require multiple independent tier tracks within a single tier group.

**How to avoid:** Each tier group can only be associated with one qualifying currency. For multiple independent tier tracks, create separate tier groups with their own qualifying currencies. The member's tier in each group is tracked independently.

---

## Gotcha 3: Partner Loyalty DPE Definitions Must Both Be Activated

**What happens:** Partner transactions are recorded in the system but partner balances never update. The partner ledger appears empty.

**When it occurs:** When only the "Create Partner Ledgers" DPE definition is activated and the "Update Partner Balance" definition is left inactive — or vice versa.

**How to avoid:** Partner loyalty requires TWO separate DPE definitions: Create Partner Ledgers AND Update Partner Balance. Both must be activated and scheduled. Activating only one leaves partner balance tracking incomplete.

---

## Gotcha 4: One Loyalty Program Per Experience Cloud Site

**What happens:** A company with two separate loyalty programs (one for consumers, one for business customers) tries to associate both programs with a single Loyalty Member Portal Experience Cloud site. Only one program can be configured.

**When it occurs:** Multi-program implementations attempting to share a single Experience Cloud site.

**How to avoid:** Each Experience Cloud site using the Loyalty Member Portal template can be associated with exactly one loyalty program. For multiple programs, create separate Experience Cloud sites (each with their own URL/domain).

---

## Gotcha 5: Non-Qualifying Points Cannot Drive Tier Advancement

**What happens:** A program is designed where members earn "Reward Points" (non-qualifying currency) and these points are expected to advance members through tiers. Members earn points but tier levels never change.

**When it occurs:** When the program design conflates non-qualifying (redemption) currency with qualifying (tier assessment) currency.

**How to avoid:** Tier groups look specifically for their associated qualifying currency balance when assessing tier thresholds. Non-qualifying currency balances are invisible to tier assessment. Ensure a separate qualifying currency is created and associated with the tier group.
