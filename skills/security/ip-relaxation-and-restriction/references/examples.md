# IP Relaxation / Restriction — Examples

## Example 1: Lock ETL Integration User

Integration profile `ETL_Integration` with login IP ranges:

| Start | End | Description |
|---|---|---|
| 203.0.113.10 | 203.0.113.10 | Partner primary NAT |
| 198.51.100.20 | 198.51.100.20 | Partner DR NAT |

Profile applies ONLY to the integration user. Any login from another IP
is rejected regardless of credentials.

## Example 2: Office Trusted IPs

Org-wide trusted IPs:

| Range | Justification |
|---|---|
| 192.0.2.0/24 | NYC office egress |
| 192.0.2.128/25 | SF office VPN pool |

Users inside these ranges skip device-activation challenges but still
MFA per policy.

## Example 3: Do Not Lock The Admin Profile

Avoid Profile Login IP Ranges on the System Administrator profile.
Scenario: admin travels; hardware token left at office; profile blocks;
only other admin is on vacation; support ticket opens for recovery.

Instead: MFA + short session + login history alerting.

## Example 4: Connected App For Middleware

Connected App `Mulesoft_Integration`:

- OAuth policy: Client Credentials.
- IP Relaxation: "Enforce IP restrictions" → the Connected App honors
  profile IP ranges at token mint.
- Middleware static IPs: 203.0.113.0/28.

Token cannot be minted from outside that /28.

## Example 5: Partner IP Change Runbook

1. Partner notifies of IP change 14 days ahead.
2. Admin adds NEW range to profile. Keep old range.
3. Partner switches.
4. After 72h of success, remove OLD range.
5. Changelog updated.
