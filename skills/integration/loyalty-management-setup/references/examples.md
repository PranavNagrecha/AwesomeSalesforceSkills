# Examples — Loyalty Management Setup

## Example 1: Two-Currency Program Setup (Qualifying + Non-Qualifying)

**Context:** An airline wants to set up a loyalty program where miles flown determine tier status (Silver/Gold/Platinum) and separate reward points are earned and redeemed for flights.

**Problem:** The team initially created a single currency ("Miles") for both tier progression and redemption. When they tried to reset tier-qualifying miles at year end without clearing redemption balances, they found there was no way to do this with a single currency.

**Solution:**

Program structure:

```
Loyalty Program: "SkyRewards"
├── Non-Qualifying Currency: "Reward Miles" (redeemable for flights/upgrades)
├── Tier Group: "Status Tier"
│   ├── Qualifying Currency: "Elite Qualifying Miles" (tier measurement only)
│   ├── Tier: Silver (0 - 24,999 EQM)
│   ├── Tier: Gold (25,000 - 74,999 EQM)
│   └── Tier: Platinum (75,000+ EQM)
└── Promotion Rules:
    ├── Flight Purchase → Earn 1 Reward Mile per $1 spent
    └── Flight Purchase → Earn Elite Qualifying Miles per segment flown
```

Setup steps:

1. Create Loyalty Program "SkyRewards".
2. Create Non-Qualifying Currency "Reward Miles".
3. Create Tier Group "Status Tier".
4. Create Qualifying Currency "Elite Qualifying Miles" — associate with "Status Tier" Tier Group.
5. Create Tiers (Silver, Gold, Platinum) with EQM thresholds.
6. Activate and schedule DPE "Reset Qualifying Points" job (run annually on January 1).

**Why it works:** Separating qualifying and non-qualifying currencies allows the program to reset status miles annually without touching reward balances. This is the canonical two-currency architecture.

---

## Example 2: Activating DPE Batch Jobs for Tier Processing

**Context:** A hotel loyalty program has been set up with tiers and currencies but members are not advancing to higher tiers even though they've accumulated sufficient qualifying points.

**Problem:** The "Reset Qualifying Points" and tier assessment DPE batch jobs were created by the Loyalty Management setup but never activated or scheduled.

**Solution:**

1. In Salesforce Setup, navigate to **Data Processing Engine**.
2. Find the definition named `Reset Qualifying Points for [Program Name]`.
3. Click **Activate**.
4. Click **Schedule** → Set recurrence: Annual, January 1, 00:00 UTC.
5. Find the definition named `Aggregate and Expire Fixed Non-Qualifying Points for [Program Name]`.
6. Click **Activate**.
7. Click **Schedule** → Set recurrence: Daily, 01:00 UTC.
8. Run a manual test execution and verify member tier records update correctly.

**Why it works:** DPE jobs must be explicitly activated and scheduled. Default state after Loyalty Program setup is inactive — tier processing never runs until explicitly activated.

---

## Anti-Pattern: Using Non-Qualifying Points for Tier Assessment

**What practitioners do:** Create a single "Points" non-qualifying currency and configure tier thresholds against it for tier advancement.

**What goes wrong:** The tier group's qualifying currency is separate from the non-qualifying currency. Tier assessment reads from the qualifying currency balance, not the non-qualifying one. Members accumulate non-qualifying points but their tier does not advance. The tier calculation engine appears to be broken.

**Correct approach:** Create a dedicated qualifying currency associated with the tier group. Non-qualifying points and qualifying points are tracked separately and serve different purposes. Never use a non-qualifying currency for tier thresholds.
