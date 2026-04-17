# Gotchas — API-Only User Hardening

## Gotcha 1: Shared secret

**What happens:** Two services share credentials; one compromise = both exposed.

**When it occurs:** Rushed integration onboarding.

**How to avoid:** One user per integration.


---

## Gotcha 2: No IP restriction

**What happens:** Credential leak leads to data exfiltration from anywhere.

**When it occurs:** Partner NAT change not updated.

**How to avoid:** Include IP range review in quarterly audit.


---

## Gotcha 3: Password-expires on

**What happens:** Integration silently breaks in 90 days.

**When it occurs:** Default profile cloned.

**How to avoid:** API-only profile should have 'Password never expires' or use Client Credentials (no password).

