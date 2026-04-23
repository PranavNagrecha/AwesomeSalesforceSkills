# Well-Architected Notes — IP Relaxation / Restriction

## Relevant Pillars

- **Security** — narrows attack surface for integration users where IP
  is truly static.
- **Operational Excellence** — the runbook for IP changes is the
  difference between smooth ops and a 3am incident.

## Architectural Tradeoffs

- **Profile Login IP Ranges vs MFA:** IP is a network assumption, MFA
  is a user assumption. MFA scales better across travel, WFH, partner
  changes.
- **Broad vs narrow trusted IPs:** broader reduces friction, narrower
  reduces challenge-skip scope. Prefer narrow.
- **Per-profile vs per-Connected App IP:** per-Connected-App scopes the
  rule to the integration; per-profile scopes to the human.

## Hygiene

- Quarterly review of trusted IPs.
- Log and alert on Profile Login IP Range additions.
- Runbook for partner IP rotation.

## Official Sources Used

- Login IP Ranges —
  https://help.salesforce.com/s/articleView?id=sf.users_profiles_login_ip_ranges.htm
- Trusted IP Ranges —
  https://help.salesforce.com/s/articleView?id=sf.security_network_access.htm
