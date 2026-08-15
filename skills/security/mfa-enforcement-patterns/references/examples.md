# Examples — MFA Enforcement

MFA in Salesforce is no longer a decision. It is a contractual requirement with a
platform default behind it:

> "To protect users from security threats like phishing, credential stuffing, and
> account takeovers, Salesforce requires MFA for logins to Salesforce products. This
> contractual requirement applies equally to direct logins with a Salesforce username
> and password and to logins via single sign-on (SSO)."
>
> "To help customers satisfy the MFA requirement, MFA is a default part of the direct
> login experience for production orgs."
> — Salesforce Security Guide, *Multi-Factor Authentication*

Two clauses in there do most of the work. **"Applies equally to … SSO"** means
delegating authentication to an identity provider does not delegate the obligation.
And **"a default part of the direct login experience"** means the direct-login
population is already handled — so the remaining work is everything that is *not* a
direct interactive login.

What MFA actually is, per the same page: "requires users to prove their identity by
supplying two or more pieces of evidence (or factors) … One factor is something the
user knows, such as their username and password. Other factors include something the
user has, such as an authenticator app or security key."

That definition disqualifies the security token. A security token is something the
user knows, transmitted in the same channel as the password. It is not a second
factor, and no amount of policy language makes it one.

---

## Example 1: Segment the population, because the answer differs per segment

**Context:** An org of 4,000 users, an IdP, a dozen integrations, and a handful of
break-glass accounts.

**Problem:** "Enable MFA" is not an action that applies uniformly. Each population
has a different mechanism and a different owner, and the ones that break are never
the interactive users.

**Solution — the matrix, built first:**

| Population | Who enforces | Mechanism | What breaks if you get it wrong |
|---|---|---|---|
| Direct interactive login | Salesforce | Default part of the direct login experience in production orgs | Nothing — this is the handled case |
| SSO users | The IdP | IdP policy; the obligation stays with you | Coverage gap invisible in Salesforce reporting |
| Non-human integration | N/A | Token-based OAuth (client credentials, JWT bearer) — no interactive login exists | Nightly jobs fail at the cutover |
| Human using username/password against an API | Salesforce | Treat as a direct-login user | Silent gap: looks like an integration, is a person |
| Break-glass admin | Salesforce | Phishing-resistant MFA — they are a privileged user — plus a register row with a review date | Register row becomes permanent by neglect; or someone assumes an exemption still exists |
| Experience Cloud / external | Configured separately | Separate configuration from internal users | Assumed covered, is not |

**Why the matrix comes first:** every failed MFA rollout fails on a population nobody
listed. The interactive users were always going to be fine; the ETL job authenticating
with a username and password at 02:00 was not.

**How to build the integration half from data rather than memory:**

```sql
SELECT UserId, Application, LoginType, SourceIp, Status, COUNT(Id) logins
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:30
GROUP BY UserId, Application, LoginType, SourceIp, Status
ORDER BY COUNT(Id) DESC
```

Login History surfaces the OAuth flow in use, and Salesforce attaches an explicit
recommendation to two of them:

> "**Important:** For security, we recommend blocking user-agent and username-password
> flows."
> — Salesforce Security Guide, *Monitor Login History*

Every row showing a username-password flow is either an integration that needs
migrating or a human who needs treating as an interactive user. There is no third
category, and the query tells you which rows exist rather than which ones someone
remembers.

---

## Example 2: Migrate an integration off passwords, and prove it

**Context:** A nightly ETL authenticates with a username, password, and security
token.

**Problem:** It is a direct login with no second factor. Adding MFA to it is not
possible — there is no human to complete a challenge — so the answer is to remove the
interactive login entirely.

### WRONG — trying to exempt the integration

```text
Grant the integration user an MFA exemption and leave the password flow in place.
```

This treats the symptom. The credential remains a copyable string in a middleware
config store, subject to the profile's password expiry, and it is exactly the shape
of credential that credential stuffing and phishing target. It also creates a
permanent exception, which is the thing exceptions are worst at not being.

### RIGHT — remove the password from the flow

```xml
<!-- connectedApps/ETL_Warehouse.connectedApp-meta.xml (excerpt) -->
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>ETL Warehouse</label>
    <contactEmail>data-platform@example.com</contactEmail>
    <oauthConfig>
        <callbackUrl>https://warehouse.example.com/oauth/callback</callbackUrl>
        <isClientCredentialEnabled>true</isClientCredentialEnabled>
        <oauthClientCredentialUser>etl.warehouse@example.com</oauthClientCredentialUser>
        <isPkceRequired>true</isPkceRequired>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
    </oauthPolicy>
</ConnectedApp>
```

The platform enforces the design for you: `oauthClientCredentialUser` is documented as
"The execution user for the OAuth 2.0 client credentials flow. Salesforce returns
access tokens on behalf of this user. **This user must have the API Only
permission.**" You cannot bind the machine flow to an identity that can drive the UI.

For an integration that must never put a shared secret on the wire, use the JWT
bearer flow instead — the client signs an assertion with a private key.

**Proving the migration is complete.** The completion criterion is not "the new flow
works." Both flows work; the old one is still there in a fallback branch or a second
deployment nobody documented.

```text
Criterion: 30 consecutive days with NO username-password flow subtype in
           Login History for the integration identity.
Then:      block user-agent and username-password flows at the org level, per
           Salesforce's own recommendation, so the old path cannot resume.
```

**Why it works:** the integration now holds a token, not a credential; the identity
cannot log into the UI at all; and the MFA question stops applying because there is no
interactive login to protect.

---

## Example 3: SSO — the obligation does not transfer with the authentication

**Context:** The org federates to an identity provider. Leadership records "MFA is
handled by the IdP."

**Problem:** The contractual requirement "applies equally to direct logins with a
Salesforce username and password and to logins via single sign-on (SSO)." Delegating
*authentication* to an IdP does not delegate the *obligation*. Two failure modes
follow, and both look like success from inside Salesforce.

**Failure mode A — the IdP does not actually require MFA for this population.** An
IdP policy scoped to "employees" silently excludes contractors, service accounts, or a
legacy group. Salesforce sees a valid assertion and cannot tell the difference.

**Failure mode B — MFA happens but nothing in Salesforce records that it did.**
Salesforce's own instrument for this is Login History:

> "**Authentication Method References.** Monitor how your OpenID providers
> authenticate users that log in to your org through OpenID Connect. For example, see
> which users log in with multi-factor authentication (MFA). To show you how your
> OpenID provider is authenticating users, Salesforce pulls the authentication method
> from JSON strings in the OpenID Connect token returned by your provider. **Work with
> your provider to define the values used in the JSON strings.**"
> — Salesforce Security Guide, *Monitor Login History*

"Work with your provider to define the values" is the task. Without it, Login History
cannot show which logins met MFA, and the org has no evidence for an auditor.

**Solution:**

1. Get the IdP owner to enumerate, in writing, which populations its MFA policy covers
   — and specifically which it excludes.
2. Configure the provider to return the authentication method in the OIDC token, and
   agree the values with them.
3. Verify in **Setup → Login History** that Authentication Method References populate
   for real logins.
4. Where a Salesforce-side control must depend on the strength of the login, use
   session security levels rather than a report:

```xml
<!-- profileSessionSettings/Finance_Users.profileSessionSetting-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>Finance Users</profile>
    <requiredSessionLevel>HIGH_ASSURANCE</requiredSessionLevel>
    <sessionTimeout>60</sessionTimeout>
</ProfileSessionSetting>
```

The semantics are documented precisely:

> "Session security levels control access to certain types of resources based on the
> type of authentication used for logging in to the current session. For example,
> username and password authentication requires the standard session security level.
> Multi-factor authentication (MFA) requires `HIGH_ASSURANCE`."

`ProfileSessionSetting` is API 40.0 and later. `sessionTimeout` accepts 0, 15, 30, 60,
90, 120, 240, 480, 720, or 1440 minutes and "overrides the org-wide timeout value"
for users of that profile — note the consequence: "Changes to the org-wide timeout
value don't apply to users of this profile," so a per-profile setting takes that
profile permanently out of org-wide session policy changes.

**Why it works:** `HIGH_ASSURANCE` is enforced by the platform at resource-access
time rather than reported on after the fact. A session that did not meet MFA cannot
reach the protected resource, whatever the IdP claimed.

---

## Example 4: An elevated-access register — which is no longer an exemption

> ⚠ **Read this before building the object.** After the 2026 enforcement waves there
> is no platform mechanism that exempts a user from MFA. The **"Waive Multi-Factor
> Authentication for Exempt Users"** permission still exists — Salesforce Help
> documents it under *Exclude Exempt Users from MFA for Salesforce Orgs* — but it
> "no longer automatically exempt[s] users from MFA," and holders are "prompted to
> enroll and use an MFA verifier at login." The org-wide MFA setting can no longer
> be deselected either. Dates and quotes:
> [`security/mfa-enforcement-strategy`](../../mfa-enforcement-strategy/SKILL.md).
>
> So the object below is a **register**, not a waiver. If anyone on the programme
> describes a row in it as "this user doesn't need MFA," that is now a factual
> error, and it will surface as a locked-out administrator during an incident.

**Context:** Two cases needing standing scrutiny — a break-glass administrator, and
one legacy integration with a six-week decommission date.

**Problem:** Elevated access with no review date becomes permanent by neglect. A
year later nobody can say why it exists, and removing it feels risky because nobody
knows what depends on it.

**First, the thing that actually protects the break-glass admin.** A break-glass
account holds the System Administrator profile or one of *Modify All Data*, *View
All Data*, *Customize Application*, or *Author Apex* — so it is in the
phishing-resistant MFA population. It needs a built-in authenticator, a passkey, a
FIDO2 security key, or certificate-based authentication. Salesforce Authenticator
and TOTP apps are valid *standard* MFA and do **not** satisfy PRMFA. An org that
"already did MFA years ago" for its admins is precisely the org this strands.

Provision that verifier *and* rehearse recovery — admin-generated temporary
verification codes are the phishing-resistant fallback — before you write a single
register row. The register does not substitute for it.

**Then make the review structural, not procedural.**

```text
MFA_Elevated_Access__c
  User__c                  Lookup(User)         required
  Justification__c         Long Text Area       required
  Approver__c              Lookup(User)         required
  Review_Due__c            Date                 required
  Reviewed_On__c           Date
  Verifier_Type__c         Picklist             required
      (Security Key | Built-in Authenticator | Passkey | Certificate)
  Compensating_Control__c  Text                 required
```

`Verifier_Type__c` is required and its picklist contains only phishing-resistant
methods — the register cannot record an admin whose factor would not satisfy PRMFA.
That constraint is the part doing security work; the rest is evidence.

Validation rule — the review date cannot be pushed beyond 180 days:

```text
Review_Due__c > TODAY() + 180
```

with the error "Elevated-access reviews cannot be scheduled more than 180 days out.
Renew with a fresh approval instead of extending."

The 180 days is a **governance convention chosen here for illustration**, not a
Salesforce requirement, and it no longer bounds any platform waiver — it bounds how
long a justification goes unexamined. Set it against your own policy.

Renewal is a *new record* with a *new approval*, not an edit to the date. That
single design choice is what stops drift: an edit is invisible, a new record with a
new approver is an event.

**The compensating control field is not decoration.** A register row without one is
a gap with paperwork. For a break-glass admin the honest set is: credentials in a
vault with checkout logging, IP restriction where the address is static, a short
session timeout, and an alert on every login by that identity.

**The standing report:**

```sql
SELECT User__r.Name, Justification__c, Approver__r.Name,
       Review_Due__c, Verifier_Type__c, Compensating_Control__c
FROM MFA_Elevated_Access__c
WHERE Review_Due__c <= NEXT_N_DAYS:30
ORDER BY Review_Due__c
```

Send it monthly to the approvers, not to the security team — the approver is the
person who has to defend the access, and the review only works if it lands on them.

---

## Example 5: Sequence the rollout so the failures are visible

**Context:** The matrix is built, integrations are identified, exceptions are
approved.

**Problem:** Turning everything on at once produces a support queue in which nobody
can tell an integration failure from a user who has not enrolled.

**Solution:**

```text
T-30  Publish the population matrix. Run the LoginHistory query. Every
      username-password row gets an owner and a target date.
T-21  Announce to the affected populations. Publish enrolment guidance covering
      the authenticator app AND the fallback for users with no mobile device -
      a security key, or a TOTP app on a desktop.
T-14  Migrate integrations to client credentials or JWT bearer. Parallel-run;
      do not remove the old credentials yet.
T-7   Confirm IdP coverage in writing. Verify Authentication Method References
      populate in Login History.
T-3   Approve and record every exception, each with an expiry and a
      compensating control.
T-0   Enforce. Watch the login failure rate hourly for the first day.
T+7   Retrospective. Close every exception opened "for go-live" - these are the
      ones that become permanent.
T+30  Confirm no username-password flow subtype remains in Login History, then
      block user-agent and username-password flows at the org level.
```

**Why this order:** the integration migration (T-14) is the long pole and the only
step that can break a business process silently, so it happens first and runs in
parallel. The org-level block (T+30) is last because it is the irreversible step, and
it only makes sense once the evidence says nothing depends on the old path.

**The measure that matters at T+7** is not the ticket count. It is how many exceptions
were opened during the cutover window, because those are the ones nobody planned and
they are the ones that become permanent.
