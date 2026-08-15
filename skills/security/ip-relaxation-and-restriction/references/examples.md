# Examples — IP Relaxation and Restriction

Salesforce has three IP controls that people routinely mistake for one another.
Every claim below is from the Salesforce Security Guide (Summer '26, API 67.0) and
the Metadata API Developer Guide.

| Control | Where | What it does |
|---|---|---|
| **Profile Login IP Ranges** | Profile (or Session Settings in some editions) | **Hard block.** A login from outside the range is refused. |
| **Trusted IP Ranges (Network Access)** | Setup → Network Access | **Soft relaxation.** Skips the device-activation identity challenge. Logins from outside are still allowed. |
| **Connected App IP Relaxation** | Connected App → OAuth Policies | Decides whether *this app* honours the org's IP restrictions. Can override the profile block. |

The single most common misconfiguration is treating Trusted IP Ranges as a block.
It is not one. Device activation is what it affects:

> "With device activation, Salesforce challenges users to verify their identity when
> they log in from an unrecognized browser or device or from an IP address outside
> of a trusted range."
> — Salesforce Security Guide, *Device Activation*

---

## Example 1: Lock an integration profile to a partner's egress, correctly

**Context:** A partner ETL job authenticates as a dedicated integration user. The
partner has two static NAT addresses — a primary and a DR — and no others.

**Problem:** The credential is long-lived. If it leaks, it works from anywhere.

**Solution — the profile, not Network Access.**

```text
Setup → Profiles → Partner_ETL_Integration
  Enhanced profile UI:  Login IP Ranges → Add IP ranges
  Original profile UI:  Login IP Ranges related list → New
```

| IP Start Address | IP End Address | Description |
|---|---|---|
| `203.0.113.10` | `203.0.113.10` | Partner primary NAT — renewal 2027-03 |
| `198.51.100.20` | `198.51.100.20` | Partner DR NAT — renewal 2027-03 |

> "Specify allowed IP addresses for the profile. Enter a valid IP address in the
> **IP Start Address** field and a higher-numbered IP address in the **IP End
> Address** field. To allow logins from a single IP address, enter the same address
> in both fields."

**As metadata**, which is what you actually commit:

```xml
<!-- profiles/Partner_ETL_Integration.profile-meta.xml (excerpt) -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <loginIpRanges>
        <description>Partner primary NAT — renewal 2027-03</description>
        <endAddress>203.0.113.10</endAddress>
        <startAddress>203.0.113.10</startAddress>
    </loginIpRanges>
    <loginIpRanges>
        <description>Partner DR NAT — renewal 2027-03</description>
        <endAddress>198.51.100.20</endAddress>
        <startAddress>198.51.100.20</startAddress>
    </loginIpRanges>
</Profile>
```

`loginIpRanges` is available in API 17.0 and later. Use the `description` field —
"If you maintain multiple ranges, use the **Description** field to provide details,
such as which part of your network corresponds to this range." An undescribed range
is unremovable, because nobody can prove it is dead.

**Why it works:** the restriction is on the profile that only this integration user
holds, so the blast radius is one identity. A leaked credential is unusable outside
two addresses.

**What this does NOT do:** it does not restrict *requests* after login. For that,
see Example 4.

---

## Example 2: Office ranges in Network Access — and what they actually buy you

**Context:** Staff work from three offices and a VPN. Users are being challenged for
identity verification several times a week, generating help-desk volume.

**Problem:** Every unrecognised browser or off-trusted-range login triggers device
activation. That is the intended behaviour, and it is friction.

**Solution:**

```text
Setup → Quick Find: "Network Access" → Network Access → New
```

| Start | End | Description |
|---|---|---|
| `192.0.2.0` | `192.0.2.255` | London office egress |
| `198.51.100.64` | `198.51.100.127` | VPN concentrator pool |

**Why it works:** logins from inside these ranges skip the device-activation
challenge. Users log in without the emailed verification code.

**What it explicitly does not do:**

- It does not block anything. A login from outside these ranges still succeeds
  (subject to the profile rule) — it is merely challenged.
- It does not remove MFA. Device activation and MFA are separate mechanisms; a
  trusted IP suppresses the identity-verification challenge, not the MFA
  requirement. Salesforce's own guidance is unconditional: "To safeguard access to
  your network, Salesforce requires that all logins use multi-factor authentication
  (MFA)."

**The design rule:** Network Access is a *usability* control that reduces
verification friction inside known networks. Profile Login IP Ranges is the
*security* control. Using the first where you meant the second produces an org that
looks locked down in a health check and is not.

---

## Example 3: Connected App IP Relaxation — the setting that overrides the profile

**Context:** A middleware platform uses the OAuth web server flow. Its outbound IPs
are stable but the profile it authenticates against is also used by a handful of
named human users who travel.

**Problem:** Tightening the profile breaks the humans; loosening it un-protects the
integration. The two populations need different IP behaviour on the same profile.

**Solution:** the Connected App's OAuth policy decides, per app, whether the org's
IP restrictions apply. `ipRelaxation` is a **required** field with four documented
values:

| Value | Behaviour (Metadata API Developer Guide) |
|---|---|
| `ENFORCE` (default) | "Enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user profile." |
| `BYPASS_2FACTOR` | "Allows a user running the app to bypass the org's IP restrictions when either of these conditions is true: The app has a list of allowed IP ranges and is using the web server OAuth authorization flow. Requests coming from only these IPs are allowed. — The app doesn't have a list of allowed IP ranges, but it uses the web server authentication flow. And the user successfully completes identity verification if accessing Salesforce from a new browser or device." |
| `BYPASS` | "Allows a user to run this app without org IP restrictions." |
| `ENFORCE_RELAXREFRESH` | "Enforces the IP restrictions configured for the org ... However, this option bypasses these restrictions when the connected app uses refresh tokens to get access tokens." |

```xml
<!-- connectedApps/Middleware_Integration.connectedApp-meta.xml (excerpt) -->
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Middleware Integration</label>
    <contactEmail>integration-owner@example.com</contactEmail>
    <oauthConfig>
        <callbackUrl>https://middleware.example.com/oauth/callback</callbackUrl>
        <isPkceRequired>true</isPkceRequired>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
        <refreshTokenPolicy>infinite</refreshTokenPolicy>
    </oauthPolicy>
</ConnectedApp>
```

**Why `ENFORCE` is the right default:** it is the platform default and it means the
profile's Login IP Ranges are the single source of truth. Every other value is a
*hole* in the profile restriction, granted per app.

**Where `ENFORCE_RELAXREFRESH` earns its place:** a long-running background job that
obtained its refresh token from an allowed IP but now runs from a rotating egress.
It keeps the initial authorisation gated by IP while letting token refresh happen
anywhere. That is a genuine trade and should be written down as one.

**Where `BYPASS` almost never does:** it removes IP restriction for the app
entirely, for every user of it. If an app needs `BYPASS`, the honest reading is
usually that the profile restriction is wrong for that population — fix the profile
or split the profile, rather than punching a hole per app.

**The review question for any non-`ENFORCE` value:** *which profile restriction is
this cancelling, and who approved that?*

---

## Example 4: Enforce IP ranges on every request, not just at login

**Context:** A session is established from an allowed IP. The session cookie is then
replayed from elsewhere — a stolen laptop, an exfiltrated token, a compromised
browser extension.

**Problem:** Profile Login IP Ranges are evaluated at *login*. By default, an
established session is not re-checked against them.

**Solution:**

```text
Setup → Quick Find: "Session Settings" → Session Settings
  [x] Enforce login IP ranges on every request
```

> "You can further restrict access to Salesforce to only those IPs in Login IP
> Ranges. To enable this option, in Setup, in the Quick Find box, enter
> `Session Settings`, and then select **Session Settings**. Select **Enforce login
> IP ranges on every request**. This option affects all user profiles that have
> login IP restrictions."

**Why it works:** every request, not just the login, is checked. A replayed session
from outside the range fails.

**Why it is a real decision, not a free win:** the sentence "This option affects
**all** user profiles that have login IP restrictions" is the whole risk. It is an
org-wide switch. Every profile that has *any* Login IP Range — including ones
configured years ago for reasons nobody remembers — becomes continuously enforced
at once. A user whose IP changes mid-session (a mobile handoff, a VPN reconnect, a
carrier NAT rotation) is interrupted.

**Sequence it safely:**

1. Inventory every profile that has Login IP Ranges. This is the population the
   switch affects, and it is usually larger than expected.
2. For each, confirm the ranges are current and that the population's addresses are
   genuinely stable.
3. Delete ranges on profiles that should not have them.
4. Enable in a full sandbox and exercise mobile, VPN reconnect, and Experience Cloud
   logins.
5. Enable in production during a low-activity window with the rollback documented.

---

## Example 5: IPv6, and the range rule that rejects your entry

**Context:** A partner's egress presents an IPv6 address for some traffic and IPv4
for the rest. An admin tries to enter one range covering both.

**Problem:** The save is rejected, with no obvious explanation of why the range is
invalid.

**The rule**, verbatim:

> "The IP addresses in a range must be either IPv4 or IPv6. In ranges, IPv4
> addresses exist in the IPv4-mapped IPv6 address space `::ffff:0:0` to
> `::ffff:ffff:ffff`, where `::ffff:0:0` is `0.0.0.0` and `::ffff:ffff:ffff` is
> `255.255.255.255`. A range can't include IP addresses both inside and outside of
> the IPv4-mapped IPv6 address space. Ranges like `255.255.255.255` to
> `::1:0:0:0` or `::` to `::1:0:0:0` aren't allowed."

**Solution:** two separate ranges, each entirely inside one address space.

| IP Start Address | IP End Address | Description |
|---|---|---|
| `203.0.113.10` | `203.0.113.10` | Partner NAT — IPv4 |
| `2001:db8::1` | `2001:db8::1` | Partner NAT — IPv6 |

**Why it works:** each range is wholly within one space, so the "inside and outside"
prohibition does not apply.

**The operational point:** ask the partner for *both* families explicitly. A partner
who answers "our egress is 203.0.113.10" is answering about IPv4 only, and their
IPv6 traffic will start failing on whatever day their network team enables it.

**Also note:** "Partner User profiles are limited to five IP addresses. To increase
this limit, contact Salesforce." That is a hard cap on a specific licence type and
it arrives without warning when an Experience Cloud partner programme scales.

---

## Anti-Pattern: Tightening the System Administrator profile

**What practitioners do:** apply Login IP Ranges to the System Administrator profile
during a hardening exercise, because admins are the highest-value accounts.

**What goes wrong:** the restriction is a hard block evaluated at login, and there
is no self-service escape. An admin travelling, working from a new ISP, or behind a
changed corporate NAT is locked out. If they are the only active admin — which is
common at weekends and during holidays — recovery requires a Salesforce Support case
and identity verification, measured in hours to days. During that window nobody can
grant access, reset a password, or turn the restriction off.

**Correct approach:** protect admin accounts with controls that fail open for the
legitimate user and closed for the attacker: MFA, a short session timeout, and
alerting on admin logins from unfamiliar locations via Login History. Keep at least
one break-glass administrator with no IP restriction, MFA enforced, credentials in a
vault, and login alerting on it. Reserve hard IP blocks for integration profiles,
where the address genuinely is static and the identity has no human to lock out.
