# LLM Anti-Patterns — IP Relaxation / Restriction

## Anti-Pattern 1: Trusted IPs As Hard Block

**What the LLM generates:** "Add office IPs to Trusted IPs to block
other logins."

**Why it happens:** conflates the two controls.

**Correct pattern:** Trusted IPs relax the challenge; Profile Login IP
Ranges block.

## Anti-Pattern 2: Lock The Admin Profile Hard

**What the LLM generates:** tight IP range on System Administrator.

**Why it happens:** "admins should be highest security."

**Correct pattern:** keep admin profile open; rely on MFA + short
session + login alerting.

## Anti-Pattern 3: IPv4 Only When Partner Emits IPv6

**What the LLM generates:** only v4 ranges.

**Why it happens:** network stack not verified.

**Correct pattern:** cover both v4 and v6 ranges where partner emits
both.

## Anti-Pattern 4: Whole Cloud Provider CIDR

**What the LLM generates:** allow 52.0.0.0/8 because "AWS."

**Why it happens:** dynamic IPs.

**Correct pattern:** require partner to provision static egress; allow
only that.

## Anti-Pattern 5: No Breakglass Runbook

**What the LLM generates:** tight IP rules without a rotation plan.

**Why it happens:** assumes IPs are forever.

**Correct pattern:** runbook with owner, steps, dual-range overlap window.
