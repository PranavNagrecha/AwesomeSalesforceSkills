# Examples — Journey Builder Administration

## Example 1: Post-Purchase Onboarding Journey With Goal-Based Early Exit

**Context:** A retail brand wants to send a 3-email onboarding series to new customers over 14 days. However, customers who make a second purchase before the series ends should exit immediately so they do not receive onboarding content they no longer need.

**Problem:** Without a goal defined, all contacts receive all three emails regardless of whether they converted. Customers who repurchase on Day 2 still receive a "make your first purchase" email on Day 7, creating a jarring brand experience. The team initially used Exit Criteria but found contacts were still receiving emails in the 15-minute window between purchase and the next exit criteria evaluation.

**Solution:**

The correct approach is to use a Goal (not Exit Criteria) because Goals evaluate at every activity step as the contact progresses — meaning a contact who meets the goal condition before the Day 7 email step is sent will exit before that message fires.

Journey setup:
```
Entry Source: Data Extension (NewCustomers_JB)
  └─ Entry Criteria: PurchaseDate IS NOT NULL AND JourneyFlag = 'Pending'

Activity Chain:
  Email 1 (Welcome) — Day 0
  Wait — 3 days
  Email 2 (Product tips) — Day 3
  Wait — 4 days
  Email 3 (Loyalty invite) — Day 7
  Wait — 7 days
  Email 4 (Review request) — Day 14
  Update Contact (set JourneyFlag = 'Complete')

Goal:
  Condition: SecondPurchaseDate IS NOT NULL
  Evaluate: At each activity
  Exit path: Update Contact (set JourneyFlag = 'Converted')
```

The `SecondPurchaseDate` field on the contact Data Extension is populated by a nightly automation that queries purchase history. Contacts who purchased again will have this field set before their next scheduled email step, causing goal evaluation to exit them at that step.

**Why it works:** Goal evaluation fires at each activity transition. When the journey engine checks a contact before sending Email 2, it first evaluates the goal — if `SecondPurchaseDate IS NOT NULL`, the contact exits via the goal path and Email 2 is never sent. Exit Criteria would not achieve this behavior because they run on a fixed schedule independent of activity transitions.

---

## Example 2: Re-Engagement Journey With Attribute Split and Re-Entry Configuration

**Context:** A B2C company wants to run a quarterly winback campaign targeting lapsed customers (no purchase in 90+ days). They have two customer tiers — Gold and Standard — and want different email sequences for each. A customer who purchases during the journey should exit. After completing or exiting the journey, a customer should be eligible to re-enter if they lapse again after 90 days.

**Problem:** The first version of this journey used a single email sequence for all lapsed customers and did not configure re-entry. Gold customers complained about receiving the same generic discount email as Standard customers. After the first run, no contacts re-entered on subsequent quarterly refreshes because re-entry was disabled.

**Solution:**

Journey setup:
```
Entry Source: Data Extension (LapsedCustomers_Quarterly)
  └─ Entry Criteria: DaysSinceLastPurchase >= 90

Re-Entry: Enabled
  └─ Minimum interval: 90 days

Attribute Decision Split (first activity):
  Arm 1 — Gold: CustomerTier = 'Gold'
    Email: Gold Winback (premium offer, 20% discount)
    Wait: 5 days
    Email: Gold Exclusive Invite
    Wait: 5 days
    Email: Gold Final Offer

  Arm 2 — Standard: CustomerTier = 'Standard'
    Email: Standard Winback (10% discount)
    Wait: 7 days
    Email: Standard Follow-up
    Wait: 7 days
    Email: Standard Last Chance

  Default Arm:
    Email: General Winback
    Wait: 7 days
    Email: General Follow-up

Exit Criteria:
  Condition: PurchaseDate > JourneyEntryDate
  (Evaluates every 15 minutes — communicate lag to stakeholders)

Goal:
  Condition: PurchaseDate > JourneyEntryDate
  Evaluate: At each activity
  (Goal tracks conversion for analytics even if exit criteria fires first)
```

The `CustomerTier` field is maintained in the Master Subscriber Data Extension and synced nightly from the CRM. Before launch, a query validates that all contacts in the entry DE have a non-null `CustomerTier` value.

**Why it works:** Attribute splits route contacts to the appropriate message sequence based on their tier data. Re-entry with a 90-day interval means lapsed customers who complete the journey without converting can re-enter the next quarterly run. The Goal layer provides conversion metrics in Journey Analytics even when Exit Criteria is also configured.

---

## Anti-Pattern: Using Exit Criteria to Block Transactional Messages in Real Time

**What practitioners do:** They configure Exit Criteria with `UnsubscribeDate IS NOT NULL` expecting that as soon as a contact unsubscribes, they will be instantly removed from the journey and not receive any further messages.

**What goes wrong:** Exit Criteria evaluate on a scheduled cycle (every 15 minutes). A contact who unsubscribes at 2:00 PM may still receive a scheduled email at 2:05 PM if that email fires before the 2:15 PM evaluation window removes them from the journey. The contact receives a message after unsubscribing, creating a compliance risk.

**Correct approach:** For compliance-sensitive unsubscribe scenarios, do not rely solely on Exit Criteria for real-time protection. Instead:
1. Ensure the Email activity itself references the All Subscribers list and Marketing Cloud's built-in unsubscribe suppression — Marketing Cloud will not send to contacts on the All Subscribers unsubscribe list regardless of journey state.
2. Use Exit Criteria as a belt-and-suspenders mechanism to clean up active journey entries, not as the primary unsubscribe gate.
3. If the concern is non-email activities (e.g., an Update Contact activity that should not fire post-unsubscribe), add an attribute split immediately before those activities that checks the unsubscribe flag and routes matching contacts to an end activity.
