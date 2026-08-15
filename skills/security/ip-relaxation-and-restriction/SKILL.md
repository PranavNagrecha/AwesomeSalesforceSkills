---
name: ip-relaxation-and-restriction
description: "Design IP-based access controls: profile login IP ranges, org-wide trusted IPs, IP relaxation per profile, and the interaction with MFA and SSO. Trigger keywords: login IP range, trusted IP, IP relaxation, restricted IP, IP allowlist, login hours. NOT for CSP Trusted Sites, CORS allowlists, TLS requirements, or troubleshooting a CSP violation — use security/network-security-and-trusted-ips."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# IP Relaxation And Restriction

## The Three Controls (Do Not Confuse Them)

| Control | Where | Effect |
|---|---|---|
| **Profile → Login IP Ranges** | Profile (edition-dependent — see below) | **Hard block.** A login from outside the range is refused. |
| **Network Access → Trusted IP Ranges** | Setup → Network Access | **Soft relaxation.** Skips the device-activation identity challenge. Logins from outside are still permitted. |
| **Connected App → `ipRelaxation`** | Connected App → OAuth Policies | Decides whether *this app* honours the org's IP restrictions. Can cancel the profile block entirely. |

Using Trusted IP Ranges as a hard control is the single most common
misconfiguration in this domain, and it produces an org that reads as locked down
and is not. Trusted ranges govern device activation:

Device activation challenges a login from an unrecognised browser/device *or* from
outside a trusted IP range — quoted from the Security Guide, with the interaction
between the two triggers, in [`references/gotchas.md`](references/gotchas.md).
> — Salesforce Security Guide, *Device Activation*

Outside a trusted range the login is **challenged, not refused**.

---

## Before Starting

1. **Separate the populations.** Integration identities (static address, no human
   to lock out) and human identities (mobile, travelling, changing ISPs) need
   different controls. Almost every bad outcome in this domain comes from applying
   the integration control to a human population.

2. **Confirm where Login IP Ranges live in this edition.** Enterprise, Unlimited,
   Performance, and Developer manage them on profiles. Group and Personal manage
   them on the Session Settings page. Professional depends on whether the "Edit
   Profiles & Page Layouts" org preference is enabled.

3. **Get static egress in writing, both address families.** A partner who answers
   "our egress is 203.0.113.10" has answered about IPv4 only.

4. **Inventory connected apps.** A single app with `ipRelaxation` set to `BYPASS`
   cancels the profile design you are about to write.

---

## Core Concepts

### Login IP Ranges

Entered as inclusive start/end pairs; a single address is the same value in both
fields. Available as `loginIpRanges` (`ProfileLoginIpRange[]`) in the Profile
metadata type since API 17.0. Viewing needs **View Setup and Configuration**;
editing and deleting need **Manage Profiles and Permission Sets**.

Address-family rule, verbatim:

> "The IP addresses in a range must be either IPv4 or IPv6 ... A range can't include
> IP addresses both inside and outside of the IPv4-mapped IPv6 address space."

So a dual-stack partner needs two ranges, not one. Note also: "Partner User profiles
are limited to five IP addresses. To increase this limit, contact Salesforce."

### Login-time vs per-request enforcement

By default the check happens at login. The org-wide switch that makes it
continuous:

```text
Setup → Session Settings → [x] Enforce login IP ranges on every request
```

> "This option affects all user profiles that have login IP restrictions."

That sentence is the whole risk. It activates every Login IP Range in the org
simultaneously, including ranges on profiles nobody has reviewed in years.

### Connected App `ipRelaxation`

Required field, four values:

| Value | Effect |
|---|---|
| `ENFORCE` (default) | "Enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user profile." |
| `BYPASS` | "Allows a user to run this app without org IP restrictions." |
| `BYPASS_2FACTOR` | Bypasses when the app has its own allowed IP list and uses the web server OAuth flow; or, with no app IP list, when the user completes identity verification from a new browser or device. |
| `ENFORCE_RELAXREFRESH` | Enforces the restriction, "however, this option bypasses these restrictions when the connected app uses refresh tokens to get access tokens." |

Any value other than `ENFORCE` is a documented hole in the profile restriction and
needs a named approver.

### Interaction with MFA

Trusted IP Ranges suppress the *device-activation* challenge. They do not remove
MFA, which Salesforce requires unconditionally: "To safeguard access to your
network, Salesforce requires that all logins use multi-factor authentication (MFA)."
Treating a trusted range as a partial MFA exemption is a misreading of both
features.

### Interaction with SSO

The identity provider authenticates first; Salesforce still evaluates its own
profile ranges when the assertion arrives. The address Salesforce evaluates is the
one that reaches Salesforce, which behind a proxy may not be the user's origin. Read
it from **Setup → Login History**: the **Source IP** column "stores the client IP
address of the request that first reaches Salesforce during a login," and the
**Forwarded for IP** column carries `X-Forwarded-For` — but "This column doesn't get
populated for OAuth and single sign-on logins," so for SSO, Source IP is all you
have.

---

## Common Patterns

### Pattern A — hard-lock the integration profile

One dedicated profile per integration, ranges scoped to the partner's provisioned
NAT (primary and DR), every range carrying a `description` with the owner and the
renewal date. This is where IP restriction is strongest and cheapest.

### Pattern B — trusted ranges for offices, MFA everywhere

Network Access ranges for office and VPN egress to cut verification friction. MFA
stays on for everyone. No profile ranges on human profiles.

### Pattern C — per-app relaxation instead of per-profile loosening

When one profile serves both a stable integration and travelling humans, keep the
profile restriction and set the humans' connected app to a documented non-`ENFORCE`
value — rather than deleting the profile restriction and protecting nothing.

### Pattern D — dual-range rotation

When a partner address changes: add the new range, keep the old, let the partner
cut over, confirm 72 hours of clean logins, then remove the old range as a separate
change. Never a same-day swap.

---

## Decision Guidance

| Situation | Control |
|---|---|
| Integration user, partner has provisioned static egress | Profile Login IP Ranges, scoped to that profile only |
| Integration user, partner cannot provide static egress | **Not available.** Say so, and carry the posture with a dedicated user, minimal permissions, short-lived tokens, and query-volume monitoring |
| Human users, office and VPN networks known | Network Access Trusted IP Ranges (friction only) + MFA |
| System Administrator profile | **No IP block.** MFA, short session, login alerting, break-glass admin |
| Session replay is in the threat model | Session Settings → Enforce login IP ranges on every request, after an inventory and a sandbox rehearsal |
| One profile serves integrations and travelling humans | Keep the profile restriction; adjust the app's `ipRelaxation` with an approver |
| Background job refreshes tokens from a rotating egress | `ENFORCE_RELAXREFRESH`, recorded as a documented hole |
| Public Site guest profile | Not an IP problem — harden with object/field permissions and sharing |

---

## Recommended Workflow

1. **Map profiles to personas** and classify each as integration or human. Only
   integration profiles are candidates for a hard block.
2. **Catalogue egress addresses per office, VPN, and partner**, in both IPv4 and
   IPv6, with a named owner and a renewal date for each.
3. **Apply Profile Login IP Ranges to integration profiles only**, one profile per
   integration, with a `description` on every range.
4. **Configure Network Access Trusted IP Ranges for office and VPN egress** to
   reduce device-activation friction. Do not treat this as a restriction.
5. **Audit `ipRelaxation` on every connected app.** Anything other than `ENFORCE`
   needs a written justification and an approver, recorded alongside the profile
   design.
6. **Leave the System Administrator profile unrestricted** and protect it with MFA,
   a short session timeout, and Login History alerting. Keep one monitored
   break-glass admin.
7. **Write the rotation and break-glass runbook before enforcing**, then enable and
   monitor login failures for integration identities for the first two weeks.

---

## Review Checklist

- [ ] Every hard block is on an integration profile, not a human one
- [ ] System Administrator profile has no Login IP Ranges
- [ ] A monitored, MFA-protected break-glass admin exists outside every restriction
- [ ] Every range has a `description` naming its owner and renewal date
- [ ] Dual-stack partners have separate IPv4 and IPv6 ranges
- [ ] No cloud-provider-wide CIDR anywhere in the allow-list
- [ ] `ipRelaxation` audited across all connected apps; non-`ENFORCE` values justified
- [ ] Trusted IP Ranges are documented as friction reduction, not as a restriction
- [ ] MFA is enforced independently of every IP setting
- [ ] If per-request enforcement is on: profile inventory pruned and sandbox-rehearsed
- [ ] Rotation runbook exists with a dual-range overlap window
- [ ] Alerting on login failures for integration identities

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **Trusted IP Ranges block nothing** — they suppress the device-activation
   challenge.
2. **Login IP Ranges are checked at login, not on every request**, until the
   org-wide Session Settings switch is on.
3. **A connected app can cancel your profile restriction** via `ipRelaxation`.
4. **A range cannot straddle the IPv4-mapped IPv6 boundary.**
5. **Where Login IP Ranges live depends on the edition.**
6. **IP-restricting a Site guest profile forces private static-resource caching**,
   with a documented tail of up to 45 days on reversal.
7. **Cloud-hosted partners often have no static egress** unless it was contracted.
8. **SSO changes where the restriction applies, not whether it does** — and
   Forwarded for IP is empty for SSO and OAuth logins.
9. **Removing a range does not terminate existing sessions or revoke tokens.**

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Profile-to-persona map | Every profile classified integration or human, with the control selected for each and the reason |
| IP inventory | Address, family, owner, renewal date, and source (contract clause or partner confirmation) for every range |
| Connected app relaxation audit | Every app's `ipRelaxation` value, with a justification and approver for anything other than `ENFORCE` |
| Rotation runbook | Dual-range overlap procedure with the confirmation window and the separate removal change |
| Break-glass procedure | The unrestricted admin identity, where its credentials live, and what alerting watches it |

---

## Related Skills

- `security/mfa-enforcement-patterns` — the identity-side control that carries the
  populations IP restriction cannot
- `security/network-security-and-trusted-ips` — the broader network-layer surface,
  including CORS and TLS, which this skill explicitly excludes
- `security/api-only-user-hardening` — the integration identity that a hard IP block
  is usually protecting
- `security/session-management-and-timeout` — session lifetime and the per-request
  enforcement switch's neighbours
