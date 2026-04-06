# LLM Anti-Patterns — Network Security and Trusted IPs

Common mistakes AI coding assistants make when generating or advising on Salesforce network security controls.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Trusted IP Ranges with Login IP Ranges

**What the LLM generates:** "Add your office IP to Trusted IP Ranges (Setup > Security > Network Access) to restrict logins to that IP."

**Why it happens:** The name "Trusted IP Ranges" strongly implies access restriction. Training data from blogs and community answers frequently makes this same conflation.

**Correct pattern:**

```
Trusted IP Ranges (Network Access) only bypass the email verification challenge.
Users outside these ranges can still log in — they just receive an email code.

To hard-restrict logins to specific IPs, use Login IP Ranges on the profile:
Setup > Profiles > [Profile] > Login IP Ranges.
Login IP Ranges deny login entirely from IPs outside the configured range.
```

**Detection hint:** If the advice uses "Trusted IP Ranges" or "Network Access" for the purpose of preventing logins, the wrong control is being recommended.

---

## Anti-Pattern 2: Confusing CSP Trusted Sites with CORS Allowlist

**What the LLM generates:** "Add the external domain to CSP Trusted Sites so your JavaScript app can call the Salesforce REST API."

**Why it happens:** Both CSP and CORS are browser security concepts and training data often conflates them. LLMs treat them as interchangeable allowlists.

**Correct pattern:**

```
CSP Trusted Sites control what external resources Lightning pages can LOAD
(scripts, images, fonts, iframes). They do not govern API access.

CORS allowlist controls which external web app origins can CALL Salesforce
REST/SOAP/Bulk APIs from browser JavaScript.

- External JS library in an LWC → CSP Trusted Sites (script-src directive)
- External web app calling Salesforce REST API → CORS allowlist entry
```

**Detection hint:** If the advice adds a CSP Trusted Site for an API-calling use case (or a CORS entry for resource loading), the controls are swapped.

---

## Anti-Pattern 3: Claiming Trusted IP Ranges Bypass MFA

**What the LLM generates:** "Users logging in from Trusted IP Ranges will not need MFA."

**Why it happens:** Older training data predates Salesforce's MFA enforcement. Before MFA enforcement, Trusted IPs did bypass the identity verification challenge, and some sources incorrectly generalize this to MFA bypass.

**Correct pattern:**

```
Trusted IP Ranges bypass the EMAIL VERIFICATION challenge only. If MFA is
enforced for the org or the user's profile, MFA is still required even from
a Trusted IP. MFA enforcement and Trusted IP behavior are independent controls.
```

**Detection hint:** If the advice claims MFA is skipped for Trusted IPs, it is incorrect for any org with MFA enforcement enabled.

---

## Anti-Pattern 4: Setting Login IP Ranges Without Testing from a Known-Good IP

**What the LLM generates:** "Configure Login IP Ranges on the System Administrator profile with your VPN IP block" without warning about self-lockout.

**Why it happens:** LLMs generate configuration steps without modeling the consequence of the admin's own session being outside the new IP range on next login.

**Correct pattern:**

```
Before saving Login IP Ranges on ANY profile (especially System Administrator):
1. Confirm your current session IP is within the range you are about to save.
2. Keep a second admin session open from a known-good IP as a safety net.
3. Test login from a confirmed in-range IP before closing backup sessions.
If you save a range that excludes your own IP, you are locked out on next login
with no self-service recovery path.
```

**Detection hint:** If the advice configures Login IP Ranges without a lockout warning or testing step, it creates a high risk of admin self-lockout.

---

## Anti-Pattern 5: Adding CSP Trusted Sites with All Directives Enabled

**What the LLM generates:** "Add a CSP Trusted Site with all directives enabled for the CDN domain."

**Why it happens:** LLMs default to broad permissions to avoid follow-up errors. Enabling all CSP directives is the path of least resistance.

**Correct pattern:**

```
Each CSP Trusted Site entry should use the MINIMUM set of directives needed:
- External JS file → script-src (and possibly connect-src if it makes API calls)
- External CSS → style-src
- Web font → font-src
- External image → img-src
- Embedded iframe → frame-src

Enabling all directives for every entry widens the attack surface unnecessarily.
CSP Trusted Sites are org-wide with no profile or component scoping.
```

**Detection hint:** If the advice enables all CSP directives for a single resource type, the entry is over-permissioned.

---

## Anti-Pattern 6: Forgetting That Sandbox Refresh Removes IP Restrictions

**What the LLM generates:** Network security configuration steps with no mention of sandbox refresh behavior.

**Why it happens:** Training data focuses on production configuration. The sandbox refresh data loss for Network Access and Login IP Ranges is a platform-specific gotcha that LLMs rarely surface.

**Correct pattern:**

```
All Network Access (Trusted IP Ranges) and profile Login IP Ranges must be
re-entered manually after a full sandbox refresh. Salesforce does not carry
these settings over from production. Document all IP restriction configurations
in a runbook and reapply them after every sandbox refresh.
```

**Detection hint:** If the advice configures network restrictions without mentioning sandbox refresh implications, the configuration will silently disappear on the next refresh.
