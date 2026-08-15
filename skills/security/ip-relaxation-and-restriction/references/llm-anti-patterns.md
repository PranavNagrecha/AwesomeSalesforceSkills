# LLM Anti-Patterns — IP Relaxation and Restriction

Mistakes AI assistants reliably make when asked to "restrict Salesforce access by
IP."

## Anti-Pattern 1: Recommending Trusted IP Ranges as a Block

**What the LLM generates:** "Add your corporate CIDRs under Setup → Network Access
→ Trusted IP Ranges so that only those addresses can log in."

**Why it happens:** The name is the most allow-list-sounding string in the Setup
menu, and it is the more commonly documented of the two screens.

**Correct pattern:**

```
Trusted IP Ranges do NOT block. They suppress the device-activation identity
challenge:

  "With device activation, Salesforce challenges users to verify their identity
   when they log in from an unrecognized browser or device or from an IP address
   outside of a trusted range."

A login from outside a trusted range is CHALLENGED, not refused.

Use the right control:
  hard block                 -> Profile -> Login IP Ranges
  less verification friction -> Setup -> Network Access -> Trusted IP Ranges

An org with Network Access ranges and no profile ranges has ZERO IP-based
access restriction, however it reads in a security document.
```

**Detection hint:** the words "Network Access," "Trusted IP Ranges," or
"trusted IPs" in an answer whose stated goal is to prevent access.

---

## Anti-Pattern 2: Locking the System Administrator Profile

**What the LLM generates:** "Apply Login IP Ranges to the System Administrator
profile — admin accounts are the highest-value target."

**Why it happens:** "Most privileged account gets the tightest control" is correct
reasoning applied to a control whose failure mode is a hard lockout with no
self-service recovery.

**Correct pattern:**

```
Login IP Ranges are a hard block evaluated at login with no user-side escape.
An admin travelling, on a new ISP, or behind a changed corporate NAT is locked
out. If they are the only active admin - normal at weekends - recovery is a
Salesforce Support case measured in hours to days, during which NOBODY can
grant access or remove the restriction.

Protect admin accounts with controls that fail open for the legitimate user:
  - MFA (required by Salesforce for all logins anyway)
  - short session timeout
  - alerting on admin logins from unfamiliar locations (Login History)
  - at least one break-glass admin with NO IP restriction, MFA enforced,
    credentials vaulted, and login alerting on it

Reserve hard IP blocks for integration profiles, where the address genuinely is
static and there is no human to lock out.
```

**Detection hint:** "System Administrator" and "Login IP Ranges" in the same
recommendation, with no break-glass account mentioned.

---

## Anti-Pattern 3: Ignoring Connected App `ipRelaxation`

**What the LLM generates:** a complete profile Login IP Ranges design with no
mention of connected apps.

**Why it happens:** The two settings live on different Setup screens and are usually
owned by different people, so they appear in different documents and rarely in the
same training example.

**Correct pattern:**

```
A connected app can cancel the profile restriction. ipRelaxation is a REQUIRED
field on the app's OAuth policy:

  ENFORCE (default)      honours the org's IP restrictions
  BYPASS                 "Allows a user to run this app without org IP
                          restrictions"
  BYPASS_2FACTOR         bypasses when the app has its own allowed IP list and
                          uses the web server flow, or (no app IP list) when the
                          user passes identity verification on a new browser
                          or device
  ENFORCE_RELAXREFRESH   honours the restriction, but "bypasses these
                          restrictions when the connected app uses refresh
                          tokens to get access tokens"

Any IP design must audit ipRelaxation across every connected app. Non-ENFORCE
values need a written answer to: which profile restriction is this cancelling,
and who approved it?
```

**Detection hint:** an IP restriction plan with no `ipRelaxation` audit step, or a
connected app definition generated without an explicit `<ipRelaxation>` element.

---

## Anti-Pattern 4: Allow-Listing a Whole Cloud Provider

**What the LLM generates:** "The partner runs on AWS, so allow their region's
published IP range."

**Why it happens:** The model cannot ask the partner for a static address and
produces the only concrete range it can name.

**Correct pattern:**

```
A cloud provider range is not a restriction. Anyone with an account at that
provider is inside it.

The correct answer is a requirement, not a range:
  "This integration needs a static egress address. Ask the partner to provision
   a NAT Gateway / Cloud NAT / egress proxy and supply the address, in BOTH
   IPv4 and IPv6 if they are dual-stack."

If they cannot provide one, say so plainly: IP restriction is not an available
control for this integration. Carry the posture elsewhere - dedicated
integration user, minimal object permissions, short-lived tokens, monitoring on
query volume. Recording "IP restricted to AWS" as a control is worse than
recording no control, because it stops anyone looking for a real one.
```

**Detection hint:** any CIDR shorter than roughly `/24` in a partner allow-list, or
any reference to a cloud provider's published IP range document.

---

## Anti-Pattern 5: Assuming Login IP Ranges Apply to Every Request

**What the LLM generates:** "Once you set Login IP Ranges, all access from outside
the range is blocked."

**Why it happens:** It is the intuitive reading of the feature name, and the
per-request setting is on a different page.

**Correct pattern:**

```
Login IP Ranges are evaluated AT LOGIN. An established session survives an IP
change by default. Session replay from another network works.

The per-request check is a separate, org-wide switch:
  Setup -> Session Settings -> "Enforce login IP ranges on every request"

  "This option affects all user profiles that have login IP restrictions."

That sentence is the risk. It activates EVERY Login IP Range in the org at once,
including ranges configured years ago on profiles nobody reviewed. Always pair
the recommendation with:
  1. inventory every profile with loginIpRanges populated
  2. delete ranges that should not be there
  3. rehearse in a full sandbox (mobile, VPN reconnect, Experience Cloud)
  4. enable in a low-activity window with a documented rollback
```

**Detection hint:** an answer that describes Login IP Ranges as continuous
enforcement without naming the Session Settings checkbox, or that recommends the
checkbox without the org-wide warning.

---

## Anti-Pattern 6: Treating a Removed Range as Closed Access

**What the LLM generates:** incident guidance that ends at "remove the compromised
range from the profile."

**Why it happens:** Revoking the grant reads as revoking the access. For most
permission models it is.

**Correct pattern:**

```
Removing a range prevents the NEXT login. It does not end current sessions
unless "Enforce login IP ranges on every request" is enabled.

Incident response for a suspected IP-scoped compromise:
  1. remove or tighten the range
  2. terminate active sessions (Setup -> Session Management, or deactivate
     the user)
  3. revoke OAuth tokens - a token-based client does not depend on a browser
     session at all
  4. review Login History Source IP for the affected identity
  5. only then declare the access closed
```

**Detection hint:** incident guidance mentioning IP ranges with no session
termination and no token revocation step.

---

## Anti-Pattern 7: One Range for a Dual-Stack Partner

**What the LLM generates:** a single start/end pair intended to cover both an IPv4
and an IPv6 address, or an IPv4-only range for a partner that is dual-stack.

**Why it happens:** The model treats a range as an abstract interval rather than an
address-family-bound one, and IPv6 is rarely mentioned in the prompt.

**Correct pattern:**

```
"A range can't include IP addresses both inside and outside of the IPv4-mapped
 IPv6 address space. Ranges like 255.255.255.255 to ::1:0:0:0 or :: to
 ::1:0:0:0 aren't allowed."

Create one range per address family:

  203.0.113.10   203.0.113.10   Partner NAT - IPv4
  2001:db8::1    2001:db8::1    Partner NAT - IPv6

And ask the partner for both families explicitly. "Our egress is 203.0.113.10"
answers about IPv4 only, and their IPv6 traffic will start failing the day
their network team turns it on.

Also flag the cap where relevant: "Partner User profiles are limited to five IP
addresses. To increase this limit, contact Salesforce."
```

**Detection hint:** an IP plan with no IPv6 consideration, or a single range whose
endpoints are in different address families.

---

## Anti-Pattern 8: Hardening a Public Site by IP-Restricting Its Guest Profile

**What the LLM generates:** "Add IP ranges to the site's guest user profile to limit
who can reach the public site."

**Why it happens:** Guest users are an obvious risk surface and profile restriction
is the tool the model has for profiles.

**Correct pattern:**

```
Two problems. First, a public site is public - if only known addresses should
reach it, it should not be a public site. Second, the restriction has a
documented performance side effect:

  "Cache settings on static resources are set to private when accessed via a
   Salesforce Site whose guest user's profile has restrictions based on IP range
   or login hours ... if a previously unrestricted site becomes restricted, it
   can take up to 45 days for the static resources to expire from the Salesforce
   cache and any intermediate caches."

Harden a guest profile through object and field permissions, sharing, and rate
limiting instead. If IP restriction is genuinely required, record the 45-day
cache tail in the change so the slowdown is not later mistaken for an unrelated
regression.
```

**Detection hint:** "guest user" and "Login IP Ranges" in the same recommendation,
with no mention of the caching consequence.
