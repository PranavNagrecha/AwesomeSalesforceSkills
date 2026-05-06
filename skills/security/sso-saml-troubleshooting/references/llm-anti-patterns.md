# LLM Anti-Patterns — SAML SSO Troubleshooting

Mistakes AI assistants commonly make when advising on SAML SSO
diagnostics.

---

## Anti-Pattern 1: "Re-upload the certificate" as a default fix

**What the LLM generates.**

> SAML SSO not working? Re-upload the IdP signing certificate in
> Setup -> Single Sign-On Settings.

**Why it happens.** Cert rotation is a common cause; the LLM
generalizes it as "the answer".

**Correct pattern.** Diagnose first via Login History or SAML
Assertion Validator. Cert mismatch is one of several possible
causes. Audience mismatch, NameID, clock skew, JIT failures, and
RelayState issues are equally common.

**Detection hint.** Any "fix SSO" recommendation that jumps to a
single fix without naming the failing check.

---

## Anti-Pattern 2: Recommending the SAML Assertion Validator as IdP truth

**What the LLM generates.**

> Run the SAML Assertion Validator. If it shows Signature
> Successful, the IdP cert is correct.

**Why it happens.** Validator output sounds authoritative.

**Correct pattern.** The validator runs Salesforce's checks against
your SSO Settings. It tells you "given this configuration, the
response would pass". It does not tell you whether the cert in SSO
Settings actually matches the IdP's published cert; both can be
the wrong cert in the same way.

**Detection hint.** Any recommendation that uses validator output
as proof the IdP is correctly configured.

---

## Anti-Pattern 3: Generic "increase the assertion lifetime" without root cause

**What the LLM generates.**

> Set NotOnOrAfter to 24 hours to avoid Assertion Expired errors.

**Why it happens.** Symptom-fix shortcut.

**Correct pattern.** Long-lived assertions weaken security. The
right fix is to address clock skew (NTP-sync the IdP host).
Increase the lifetime only when drift is unavoidable — and even
then, 5–10 minutes, not 24 hours.

**Detection hint.** Any "extend assertion lifetime to N hours"
recommendation.

---

## Anti-Pattern 4: Confusing IdP-initiated and SP-initiated diagnostics

**What the LLM generates.**

> Send a SAMLRequest from the IdP to start the flow.

**Why it happens.** Mixing the two flows' terminology.

**Correct pattern.** SAMLRequest is sent by the SP (Salesforce) in
SP-initiated flow. In IdP-initiated, no SAMLRequest is sent; the
IdP unilaterally POSTs a SAML response.

**Detection hint.** Any flow description where the IdP "sends a
SAMLRequest" or the SP "sends an unsolicited assertion".

---

## Anti-Pattern 5: Enabling JIT Provisioning as a fix for "User does not exist"

**What the LLM generates.**

> Enable Just-in-Time Provisioning so the user is auto-created when
> they SSO.

**Why it happens.** Surface-level mapping of error -> "auto-create
the missing user".

**Correct pattern.** JIT must be configured carefully — the
assertion must carry every Salesforce required-field attribute
(profile, email, last name, etc.). Enabling JIT without configuring
the attribute mapping creates broken users. The right initial fix
is often to provision the user via SCIM or a one-time bulk load.

**Detection hint.** Any JIT recommendation without the attribute-
mapping caveat.

---

## Anti-Pattern 6: Suggesting My Domain disable to "simplify"

**What the LLM generates.**

> If My Domain is causing complications, you can disable it
> temporarily for testing.

**Why it happens.** Misunderstanding the My Domain prerequisite.

**Correct pattern.** SAML SSO requires My Domain. Disabling it
breaks SSO entirely. My Domain is essentially mandatory now and
cannot be disabled in many recent orgs.

**Detection hint.** Any recommendation to disable or work around
My Domain in a SAML SSO context.

---

## Anti-Pattern 7: Hand-waving NameID format

**What the LLM generates.**

> Set NameID to the user's email.

**Why it happens.** Email is the obvious value.

**Correct pattern.** NameID has both a *value* (e.g. the email
address) and a *format* (the URI declaring how to interpret the
value). Salesforce's SSO Settings expects a specific format URI; a
mismatch fails the login even when the value is correct.

**Detection hint.** Any NameID guidance that does not specify the
Format URI.
