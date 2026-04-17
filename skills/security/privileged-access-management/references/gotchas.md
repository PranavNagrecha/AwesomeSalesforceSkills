# Gotchas — Privileged Access Management (PAM)

## Gotcha 1: ExpirationDate ignored for Permission Set Group licenses

**What happens:** License-required PSGs don't auto-expire on all editions.

**When it occurs:** Enterprise without the User Access and Permissions Assistant.

**How to avoid:** Verify ExpirationDate honors on your edition; otherwise use a Scheduled Apex fallback.


---

## Gotcha 2: Setup Audit Trail gaps

**What happens:** Certain configuration changes are not logged.

**When it occurs:** Licenses and feature toggles.

**How to avoid:** Supplement with Event Monitoring RealTimeEventMonitoring and archive monthly.


---

## Gotcha 3: Break-glass account shared

**What happens:** One account used by multiple humans; no personal accountability.

**When it occurs:** Small IT teams.

**How to avoid:** Two break-glass accounts, each assigned to one named human, rotated quarterly.

