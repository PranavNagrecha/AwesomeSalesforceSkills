# LLM Anti-Patterns — Zero-Trust Salesforce Patterns

Mistakes AI assistants commonly make about zero-trust architecture in
Salesforce. Each entry is **what / why / correct / detection**.

## 1. Conflating "MFA enforced" with "zero trust"

**What the LLM generates:** A plan that enables MFA universally and
declares the zero-trust posture done. Often paired with "best practice
is MFA + SSO".

**Why:** The phrase "zero trust" appears most frequently in marketing
content next to MFA. Training data overweights the equivalence.

**Correct pattern:** Treat MFA as the verify-explicitly leg's
**session-start** input. Layer on (1) High-Assurance Session for
step-up at the operation level, (2) Login Flow consuming an IdP
device/risk claim, (3) RTEM + Transaction Security Policies for
continuous in-session verification, and (4) PSG + Muting for
least-privilege. See SKILL.md "The four zero-trust legs in Salesforce".

**Detection:** Output that mentions zero trust and MFA together but
does not mention RTEM, Transaction Security Policies, or Login Flow.

## 2. Assuming TSP enforcement applies to every RTEM event

**What the LLM generates:** A Transaction Security Policy design that
fires "Block" or "Require MFA" actions on `IdentityVerificationEvent`
or `MobileEmailEvent`.

**Why:** The RTEM event-type list is long and most events do support
TSP enforcement. LLMs generalize to "all RTEM events support TSP" and
miss the documented exceptions.

**Correct pattern:** Build the explicit support matrix at design time.
`IdentityVerificationEvent` and `MobileEmailEvent` are notification-only;
TSPs do NOT block on them. For these events, subscribe via Apex / Flow
on the underlying Platform Event and take non-synchronous action.

**Detection:** A TSP design document that includes
`IdentityVerificationEvent` or `MobileEmailEvent` in a "Block" or
"RequireMfa" action.

## 3. Setting High-Assurance Session at the Profile level

**What the LLM generates:** "Set Session Security Level Required to
High Assurance on the Standard User profile" or similar Profile-wide
recommendations.

**Why:** Profile-level settings are the most well-known knob in
Salesforce. LLMs default to Profile when the right answer is
Permission Set Group.

**Correct pattern:** Set High-Assurance Session on the **Permission
Set Group** that holds the high-blast-radius permission. Step-up fires
only when the user exercises that permission, not on every page-load.

**Detection:** Output recommending Profile-level High Assurance for
day-to-day users. Also flag any guidance that does not mention PSGs
when discussing High-Assurance Session.

## 4. Treating Login Flow as the continuous-verification mechanism

**What the LLM generates:** "Use Login Flow to re-evaluate device
state and IdP risk every time the user accesses sensitive data."

**Why:** Login Flow is the most flexible Apex-customizable insertion
point and the corpus describes it as "session-start enforcement" in
some places and "session-management Apex" in others. LLMs blur the two.

**Correct pattern:** Login Flow runs once, at session admission. For
in-session re-evaluation, the layer is RTEM + Transaction Security
Policies. Pair the two; do not substitute one for the other.

**Detection:** Output that proposes Login Flow as the answer to a
question about in-session enforcement.

## 5. Recommending "least privilege" via Profile rewrites

**What the LLM generates:** A multi-month plan to rewrite every
Profile to remove Modify All Data, View All, and similar
high-blast-radius rights.

**Why:** Profile is the most prominent permission container; LLMs
default to it. The fact that Profiles cannot be muted from PSGs is an
operational nuance underrepresented in the corpus.

**Correct pattern:** Profile minimization is real but is a separate
workstream. The least-privilege leg of zero trust uses **PSG + Muting
Permission Sets** for the dynamic policy and JIT grants for break-glass.
Profiles hold only the truly-static common ground.

**Detection:** Output that recommends rewriting Profiles as the
zero-trust least-privilege strategy with no mention of PSGs or muting.

## 6. Claiming CAEP / cross-vendor continuous risk works on Salesforce

**What the LLM generates:** "Azure AD's CAEP can revoke a Salesforce
session in real time when the user's risk level rises."

**Why:** CAEP works between Azure AD and M365 and is heavily
documented. The Salesforce side does not consume CAEP; LLMs miss the
boundary.

**Correct pattern:** Document CAEP as a residual gap. Mitigate with
shorter session timeouts (so the next Login Flow firing sees the new
risk state) and aggressive RTEM-based session-end TSPs.

**Detection:** Any output that asserts cross-vendor real-time session
revocation works for Salesforce.
