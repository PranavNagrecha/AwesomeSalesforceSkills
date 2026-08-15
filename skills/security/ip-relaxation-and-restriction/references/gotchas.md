# Gotchas — IP Relaxation and Restriction

Non-obvious behaviours of Salesforce's three IP controls. Grounded in the
Salesforce Security Guide and the Metadata API Developer Guide (Summer '26,
API 67.0).

## Gotcha 1: Trusted IP Ranges Block Nothing

**What happens:** An org adds its office CIDRs under **Setup → Network Access**,
records "IP restriction implemented" in the security programme, and passes an
internal review. A leaked credential is then used successfully from anywhere in the
world.

Trusted IP Ranges govern *device activation*, not access:

> "With device activation, Salesforce challenges users to verify their identity when
> they log in from an unrecognized browser or device or from an IP address outside
> of a trusted range."
> — Salesforce Security Guide, *Device Activation*

Inside a trusted range, the identity-verification challenge is skipped. Outside it,
the login is **challenged, not refused**.

**When it occurs:** In almost every org that has not read the difference, because
"Trusted IP Ranges" is the more discoverable of the two screens and the name reads
like an allow-list.

**How to avoid:** Use the right control for the intent.

- Want a **block**? Profile → Login IP Ranges.
- Want **less verification friction** for known networks? Network Access →
  Trusted IP Ranges.

Say which one you mean in the design document, and audit the claim: an org with
Network Access ranges and no profile ranges has zero IP-based access restriction.

---

## Gotcha 2: Login IP Ranges Are Checked at Login, Not on Every Request

**What happens:** A session established from an allowed address continues to work
after the client moves — including when a session token is replayed from a different
network entirely.

**When it occurs:** By default, always. It is the platform's baseline behaviour.

**How to avoid:** Enable the org-wide setting deliberately:

> "You can further restrict access to Salesforce to only those IPs in Login IP
> Ranges ... Select **Enforce login IP ranges on every request**. This option
> affects all user profiles that have login IP restrictions."

That last sentence is the risk, not a footnote. It is org-wide, and it activates
*every* Login IP Range in the org at once, including ranges configured years ago on
profiles nobody has reviewed. Before enabling:

1. Inventory every profile with `loginIpRanges` populated. The list is usually
   longer than expected.
2. Delete ranges on profiles that should not have them.
3. Confirm the remaining populations have genuinely stable addresses.
4. Rehearse in a full sandbox with mobile, VPN reconnect, and Experience Cloud
   logins — a mid-session IP change now interrupts the user.

---

## Gotcha 3: A Connected App Can Cancel Your Profile Restriction

**What happens:** A profile is locked to two addresses. The org's security posture
report says so. A connected app authenticating against that same profile works from
anywhere, because its OAuth policy was set to `BYPASS`.

`ipRelaxation` is a **required** field on the connected app's OAuth policy with four
values, only one of which honours the profile:

| Value | Effect |
|---|---|
| `ENFORCE` (default) | Honours the org's IP restrictions |
| `BYPASS` | "Allows a user to run this app without org IP restrictions" |
| `BYPASS_2FACTOR` | Bypasses the org restriction when the app has its own allowed IP list and uses the web server flow, or (with no app IP list) when the user passes identity verification from a new browser or device |
| `ENFORCE_RELAXREFRESH` | Honours the restriction, "however, this option bypasses these restrictions when the connected app uses refresh tokens to get access tokens" |

**When it occurs:** Whenever an integration is onboarded by a team that owns the
connected app but not the profile — which is the normal division of labour.

**How to avoid:** Audit `ipRelaxation` across every connected app whenever you audit
profile Login IP Ranges; they are one control, split across two screens. Any value
other than `ENFORCE` needs a written answer to *which profile restriction is this
cancelling, and who approved it*. `ENFORCE_RELAXREFRESH` is often the honest middle
ground for a background job whose refresh happens from a rotating egress — but it is
still a hole, and it should be recorded as one.

---

## Gotcha 4: A Range Cannot Straddle the IPv4-Mapped IPv6 Boundary

**What happens:** An attempt to enter a range that covers both an IPv4 address and
an IPv6 address is rejected, with an error that does not explain the underlying rule.

> "The IP addresses in a range must be either IPv4 or IPv6. In ranges, IPv4
> addresses exist in the IPv4-mapped IPv6 address space `::ffff:0:0` to
> `::ffff:ffff:ffff` ... A range can't include IP addresses both inside and outside
> of the IPv4-mapped IPv6 address space. Ranges like `255.255.255.255` to
> `::1:0:0:0` or `::` to `::1:0:0:0` aren't allowed."

**When it occurs:** On the first dual-stack partner, and again — worse — on the day
a partner's network team enables IPv6 on an egress that was previously IPv4 only.
The integration then fails intermittently, depending on which family the client
picks per connection.

**How to avoid:** Create separate ranges per address family, each entirely inside one
space. When collecting addresses from a partner, ask explicitly for both families
rather than accepting "our egress is 203.0.113.10" — that answer is about IPv4 only.

Also note the licence-specific cap: "Partner User profiles are limited to five IP
addresses. To increase this limit, contact Salesforce." That is a hard ceiling that
arrives without warning as an Experience Cloud partner programme scales.

---

## Gotcha 5: Where Login IP Ranges Live Depends on the Edition

**What happens:** A runbook says "Setup → Profiles → [profile] → Login IP Ranges,"
and in the target org the ranges are on the Session Settings page instead. The
operator concludes the feature is missing.

> "If you're using an Enterprise, Unlimited, Performance, or Developer Edition,
> manage valid IP addresses in profiles. If you're using a Group, or Personal
> Edition, from Setup, manage valid IP addresses on the Session Settings page. In a
> Professional Edition, the location of IP ranges depends on whether you have the
> 'Edit Profiles & Page Layouts' org preference enabled as an add-on feature."

**When it occurs:** In Professional Edition orgs, and in any consultancy runbook
written against one edition and reused against another.

**How to avoid:** State the edition assumption at the top of the runbook. In
Professional Edition, check the "Edit Profiles & Page Layouts" org preference before
writing the steps — with it enabled, ranges are on individual profiles; without it,
they are on Session Settings and are therefore org-wide rather than per-profile,
which is a materially different control.

Permissions differ too: viewing ranges needs **View Setup and Configuration**;
editing and deleting them needs **Manage Profiles and Permission Sets**.

---

## Gotcha 6: IP-Restricting a Site's Guest Profile Changes Static Resource Caching

**What happens:** After adding IP restrictions (or login hours) to a Salesforce Site
guest user's profile, the site becomes measurably slower, and reverting the change
does not restore performance for a long time.

> "Cache settings on static resources are set to private when accessed via a
> Salesforce Site whose guest user's profile has restrictions based on IP range or
> login hours. Sites with guest user profile restrictions cache static resources only
> within the browser. Also, if a previously unrestricted site becomes restricted, it
> can take up to **45 days** for the static resources to expire from the Salesforce
> cache and any intermediate caches."
> — Salesforce Security Guide

**When it occurs:** During a hardening exercise on a public Experience Cloud site or
Salesforce Site, where restricting the guest profile looks like an obvious win.

**How to avoid:** Treat guest-profile IP restriction as a performance decision as
well as a security one, and note the 45-day cache-expiry tail in the change record so
the effect is not mistaken for an unrelated regression. If the site is genuinely
public, IP restriction on the guest profile is usually the wrong control anyway —
harden through object and field permissions, sharing, and rate limiting instead.

---

## Gotcha 7: Cloud-Hosted Partners Often Have No Static Egress

**What happens:** A partner says "we're on AWS, our IPs are in this published
range," and the resulting allow-list is a `/8` covering an entire cloud provider.
Anyone with an account at that provider is now inside the restriction.

**When it occurs:** With any SaaS partner that has not explicitly provisioned egress,
which is most of them until asked.

**How to avoid:** Make static egress a contractual requirement, not a technical
detail. Partners can provision it — a NAT Gateway, a Cloud NAT, an egress proxy —
but only if asked before the integration is built. If they cannot, the honest answer
is that IP restriction is not an available control for that integration, and the
security posture must be carried by other means: a dedicated integration user with
minimal permissions, short-lived tokens, and monitoring on query volume. Recording
"IP restricted to AWS" as a control is worse than recording no control, because it
stops anyone looking for a real one.

---

## Gotcha 8: SSO Changes Where the Restriction Applies, Not Whether It Does

**What happens:** An org enables SSO and assumes the identity provider is now the
only gate, or conversely assumes profile IP ranges no longer matter.

Both halves of the picture are true and people usually hold only one:

- The IdP authenticates the user first, so IdP-side network policy applies there.
- Salesforce still evaluates its own profile Login IP Ranges when the assertion
  arrives. A user who passes IdP policy from a blocked address is still blocked.

The address Salesforce evaluates is the one that reaches Salesforce, which behind
proxies may not be the user's origin address. Login History exposes both: the
**Source IP** column "stores the client IP address of the request that first reaches
Salesforce during a login," while the **Forwarded for IP** column "stores the value
that the client passed in the `X-Forwarded-For` header." Note the caveat on the
latter: "This column doesn't get populated for OAuth and single sign-on logins."

**When it occurs:** During SSO rollout, and whenever a corporate proxy or CASB is
introduced in front of Salesforce.

**How to avoid:** Test the specific login path before enforcing, and read **Setup →
Login History** to see which address Salesforce actually recorded. Configure ranges
against that address, not against what the network team believes the user's address
to be. Note that for SSO logins the `Forwarded for IP` column is empty, so Source IP
is the only signal available.

---

## Gotcha 9: Tightening a Range Does Not Terminate Existing Sessions

**What happens:** An incident response removes a compromised range from a profile
and reports the access closed. The attacker's existing session keeps working.

**When it occurs:** During incident response, which is exactly when the assumption
is most costly.

**How to avoid:** Understand the two-part behaviour. Removing a range prevents the
*next* login. It does not end current sessions unless **Enforce login IP ranges on
every request** is enabled — with that setting on, the very next request from
outside the range fails, which is the main operational argument for having it on
before you need it. During an incident, pair the range change with an explicit
session termination (**Setup → Session Management**, or deactivating the user) and
with revoking the relevant OAuth tokens, since a token-based client does not depend
on a browser session at all.
