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
2. Create Non-Qualifying Currency "Reward Miles" with a Fixed expiry model.
3. Create Tier Group "Status Tier" and Tiers Silver, Gold, Platinum.
4. Create Qualifying Currency "Elite Qualifying Miles" and associate it with "Status Tier".
5. In Manage Tier Eligibility, enter the minimum balances (0; 25,000; 75,000) and Generate Rules to create the Change Tier process.
6. Clone the Reset Qualifying Points DPE template, activate the clone, and call it from a scheduled flow on the reset date.

**Why it works:** Separating qualifying and non-qualifying currencies allows the program to reset status miles annually without touching reward balances. This is the canonical two-currency architecture.

---

## Example 2: Members Reach the Threshold but Their Tier Never Changes

**Context:** A hotel loyalty program has tiers and currencies, and members with enough qualifying points stay in their starting tier.

**Problem:** The team activated DPE definitions and expected them to upgrade tiers. The DPE templates calculate balances, reset qualifying points, and expire points; tier upgrades come from a loyalty program process.

**Solution:**

1. On the loyalty program, open the tier group, choose Manage Tier Eligibility, enter the minimum eligible balances, and click Generate Rules. Salesforce generates and activates the Change Tier process.
2. Decide how it runs: as a child of the accrual Transaction Journal process for real-time upgrades, or through a Batch Management job.
3. For batch, turn on Select Members for Tier Assessment Automatically in Loyalty Management Settings and filter the job on Eligible for Tier Assessment.
4. Clone the balance and reset DPE templates, activate the clones, and call them from scheduled flows so qualifying balances are current before the tier job runs.
5. In a sandbox, post a transaction journal that crosses the Gold threshold and confirm the member's tier changes.

**Why it works:** Each job does the part the guide assigns to it: DPE clones keep balances current, and the generated process changes tiers.

---

## Anti-Pattern: Using Non-Qualifying Points for Tier Assessment

**What practitioners do:** Create a single "Points" non-qualifying currency and configure tier thresholds against it for tier advancement.

**What goes wrong:** Tier assessment reads the tier group's qualifying (assessment) currency, not the non-qualifying one. Members accumulate non-qualifying points but their tier does not advance.

**Correct approach:** Create a dedicated qualifying currency associated with the tier group. Non-qualifying points and qualifying points are tracked separately and serve different purposes. Never use a non-qualifying currency for tier thresholds.
