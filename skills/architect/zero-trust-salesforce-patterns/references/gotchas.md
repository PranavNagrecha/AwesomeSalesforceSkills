# Gotchas — Zero-Trust Salesforce Patterns

Non-obvious behaviors that cause real production problems when assembling
a zero-trust posture in Salesforce. Each entry is **what / when / how**.

## 1. Not every RTEM event type supports Transaction Security Policy enforcement

**What:** `IdentityVerificationEvent` and `MobileEmailEvent` are
notification-only RTEM events. TSPs cannot block, require MFA, or end
session on them. Other event types (`LoginEvent`, `ApiAnomalyEvent`,
`SessionHijackingEvent`, `CredentialStuffingEventStore`, `ReportEvent`,
`ListViewEvent`, `BulkApiEvent`, etc.) do support enforcement.

**When:** It bites when an architect builds a TSP design doc that
relies on `IdentityVerificationEvent` to enforce step-up after an
identity-verification challenge fails. The TSP appears to deploy but
never fires.

**How:** Build the RTEM event-type matrix at design time and mark
unsupported events as **detect-only**. For unsupported events,
subscribe via Apex / Flow on the underlying Platform Event and take
non-synchronous action (notify, queue a step-up requirement for next
login). Confirm against the latest Enhanced TSP docs every release.

## 2. High-Assurance Session at the Profile level breaks routine work

**What:** Setting Session Security Level to High Assurance on a
**Profile**'s Session Settings forces step-up MFA on every page-load
that touches the profile, not just the high-assurance operation.

**When:** It bites the day after enforcement: the help desk gets
flooded with "I have to MFA every 5 minutes" tickets and the
Permission Set Group owner reverts the change.

**How:** Set High Assurance on the **Permission Set Group** that
holds the high-blast-radius right (Modify All Data, View All, Manage
Users, etc.) — not on the Profile. Step-up fires only when the user
exercises the right.

## 3. Login Flow runs once and only at session start

**What:** Login Flows are interstitials between authentication and
session admission. They cannot re-evaluate IdP risk or device state
mid-session — once the session is established, Login Flow is done.

**When:** It bites when an architect treats Login Flow as the whole
"continuous verification" answer. The IdP correctly raises a risk
flag at hour 4; Salesforce never sees it because the Login Flow ran
at hour 0.

**How:** Pair Login Flow (session-start verification) with RTEM + TSP
(continuous verification on events). Document the boundary: Login Flow
covers admission, RTEM covers in-session enforcement.

## 4. Muting Permission Sets do not mute Profile-granted permissions

**What:** Muting Permission Sets (the negative grants used in Permission
Set Groups) only suppress permissions granted via Permission Sets, not
permissions granted by the Profile.

**When:** It bites in long-lived orgs where Profiles still hold
high-blast-radius rights. The architect creates a "deny-Modify-All-Data"
muting PS, attaches it to the baseline PSG, and is surprised that
admins still have Modify All Data — because their Profile granted it.

**How:** Move the right out of the Profile to a Permission Set first;
THEN mute it from the PSG. This is multi-quarter work in some orgs and
is part of the "Profile minimization" workstream that pairs with this
skill.

## 5. Mobile Security policies cover only the Salesforce mobile app

**What:** "Salesforce Mobile Security" is the trade name for policies
applied to the Salesforce mobile app: jailbreak detection, app
integrity, geolocation policy, biometric requirements. None of these
apply to the desktop browser session.

**When:** It bites when an architect writes "device trust = Mobile
Security" in the design doc. Auditors find the desktop has no
device-trust check and ask a hard question.

**How:** Mobile Security is one of two device-trust controls. The
desktop counterpart is **the IdP's device-trust signal passed through
SAML/OIDC and consumed by Login Flow**. Document both.

## 6. CAEP is not natively consumed by Salesforce

**What:** Continuous Access Evaluation Profile (the IETF / Microsoft
standard for cross-vendor risk-signal propagation) lets Azure AD
revoke a session for risk in M365 in real time. Salesforce sessions are
NOT subject to CAEP — Azure AD's risk-revoke does not propagate.

**When:** It bites in regulated environments where the security team
expects "the IdP can kill any session anywhere". They cannot, on
Salesforce, today.

**How:** Document CAEP as a residual gap. Mitigate with shorter session
timeouts (so the next Login Flow fires sooner) and aggressive RTEM-based
session-end TSPs on suspicious events.

## 7. JIT grant of a high-assurance PSG without revocation is a slow leak

**What:** Apex / Flow that JIT-assigns a PSG for a specific operation
and forgets to schedule the unassign turns "JIT grant" into "permanent
grant". Auditors who look six months later find every rep has the
ViewSSN PSG.

**When:** It bites whenever the schedule-unassign step is not part of
the same atomic transaction as the assign — typically because the
unassign was a "we'll add that later" comment.

**How:** Always pair the assignment with a `Database.Schedule`-able
unassign job in the same Apex transaction, OR with a Flow that uses
the Pause element. Set the timeout to the shortest plausible
window (15–60 minutes for SSN view; 24 hours for break-glass).
Audit JIT-PSG assignments in the quarterly zero-trust review.
