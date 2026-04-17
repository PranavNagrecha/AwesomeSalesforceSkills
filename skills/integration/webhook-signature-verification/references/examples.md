# Examples — Webhook Signature Verification

## Example 1: Stripe webhook

**Context:** Payment success

**Problem:** Anyone could POST fake payment events

**Solution:**

Stripe-Signature header → HMAC verify against Stripe secret from Protected CMDT → process only on match

**Why it works:** Only real Stripe signature passes


---

## Example 2: Replay protection

**Context:** Attacker replays yesterday's valid event

**Problem:** Signature would still match

**Solution:**

Stripe timestamp in signed payload; reject if >5 min old

**Why it works:** Combines signature + freshness

