---
name: ip-relaxation-and-restriction
description: "Design IP-based access controls: profile login IP ranges, org-wide trusted IPs, IP relaxation per profile, and the interaction with MFA and SSO. Trigger keywords: login IP range, trusted IP, IP relaxation, restricted IP, IP allowlist, login hours. Does NOT cover: network-layer firewalling, corporate VPN design, or Shield Event Monitoring."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "configure login ip ranges"
  - "trusted ip relaxation"
  - "ip allowlist for profile"
  - "restrict api access by ip"
  - "ip challenge behavior"
tags:
  - security
  - access-control
  - ip
  - login
inputs:
  - Profile-to-persona mapping
  - Known corporate egress IPs and VPN ranges
  - Integration partner source IPs (if static)
outputs:
  - Profile login-IP range plan
  - Org-wide trusted IP ranges with justification
  - Runbook for breakglass when IPs change
dependencies:
  - security/mfa-enforcement-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# IP Relaxation And Restriction

## The Two Controls (Do Not Confuse)

- **Profile → Login IP Ranges**: HARD block. Logins from outside the
  range are refused.
- **Network Access → Trusted IPs (org-wide)**: SOFT relaxation. Logins
  from these IPs skip the device activation / IP challenge. Outside
  still allowed (subject to profile rule) but challenged.

Using "Trusted IPs" as a hard control is the most common misconfiguration.

## When To Use Which

| Goal | Control |
|---|---|
| Block all logins outside corporate network | Profile Login IP Ranges |
| Reduce MFA / device challenge for office users | Trusted IPs |
| Restrict integration user to partner's egress | Profile Login IP Ranges on integration user's profile |
| Allow travelling user flexibility | Do not use Login IP Ranges; rely on MFA |

## Profile Login IP Ranges — Design

- Apply at profile level; narrow scope, narrow blast radius.
- Integration profiles: lock to partner static IPs. Include both primary
  and DR IPs.
- Admin profile: resist locking too tightly — lockout risk. Use Trusted
  IPs + MFA instead.
- Standard user profiles: if you enforce, make sure VPN covers remote
  workers.

## Trusted IPs — Design

- Org-wide ranges for offices and VPN egress.
- Keep this list tight: too broad defeats the purpose.
- Review quarterly — ISP changes will leave stale ranges.

## Interaction With MFA

- Inside a Trusted IP range, Salesforce skips the device challenge. It
  does NOT skip MFA if MFA is enforced at session or SSO level.
- Do not treat Trusted IPs as "partial MFA exemption" — MFA should stay.

## Interaction With SSO

- Profile Login IP Ranges apply to direct Salesforce login.
- With SSO, the IdP is the initial gate; Salesforce still enforces IP
  ranges if configured.
- For Connected Apps using JWT/Client Credentials, IP ranges on the
  Connected App limit where the token can be minted from.

## Breakglass Runbook

- When partner IP changes, integration jobs silently fail login.
- Runbook: page on login failure spike → admin updates profile IP range
  → rerun jobs. Store current IPs and change owner.

## Recommended Workflow

1. Inventory profiles and their personas.
2. Catalog egress IPs per office, VPN, partner integration.
3. Apply Profile Login IP Ranges where hard-block is right.
4. Configure Trusted IPs for office ranges.
5. Do NOT tighten admin profile IP ranges — rely on MFA instead.
6. Write the breakglass runbook before enforcing.
7. Monitor login failures post-cutover.

## Official Sources Used

- Login IP Ranges —
  https://help.salesforce.com/s/articleView?id=sf.users_profiles_login_ip_ranges.htm
- Trusted IP Ranges (Network Access) —
  https://help.salesforce.com/s/articleView?id=sf.security_network_access.htm
- Connected App IP Relaxation —
  https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm
