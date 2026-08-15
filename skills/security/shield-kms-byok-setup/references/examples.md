# Examples — Shield Platform Encryption: BYOK / KMS Setup

Shield Platform Encryption derives a data encryption key (DEK) from a **tenant
secret**. Where that tenant secret comes from is the whole subject of this skill,
and there are three answers with materially different operational profiles.

| Model | Where key material lives | Salesforce availability depends on your KMS? |
|---|---|---|
| **Salesforce-managed** | Derived inside Salesforce's HSM | No |
| **BYOK** (customer-supplied tenant secret) | You generate it, wrap it, and upload it. Salesforce holds the uploaded material. | No |
| **Cache-Only Key Service** | Your key service, fetched on demand. "Salesforce doesn't retain or persist your cache-only keys in any system of record or backups." | **Yes** |

Field-level encryption itself is fixed: "FLE uses the Advanced Encryption Standard
(AES) with 256-bit keys by using Cipher Block Chaining (CBC) mode and a random
initialization vector (IV)."

Choosing between the three is a compliance-versus-availability decision, not a
security-maturity ladder. Most orgs that reach for Cache-Only Keys should be on
BYOK.

---

## Example 1: BYOK — generate, wrap, upload

**Context:** A regulated org must be able to demonstrate that key material
originated outside Salesforce and that it can destroy it unilaterally.

**Problem:** Salesforce-managed tenant secrets satisfy most encryption-at-rest
requirements but not a mandate that the customer be the sole origin of key
material.

> ## ⚠ DO NOT RUN THE COMMANDS BELOW AGAINST A PRODUCTION TENANT SECRET
>
> The `openssl` pipeline in this section is **illustrative — it has not been
> step-verified against Salesforce's BYOK documentation**, and the padding mode
> shown is a guess, not a citation. A wrong wrapping burns your one upload
> attempt per 24 hours in production. Work from *Generate a BYOK-Compatible
> Certificate*, *Generate and Wrap BYOK Key Material*, and *Upload Your BYOK
> Tenant Secret* in Salesforce Help for the authoritative padding mode,
> certificate path, and file format. Use the shape below only to understand
> what the procedure is *for*.

**Solution — the shape of the flow.**

```text
1. Generate a BYOK-compatible certificate. Salesforce documents a 4096-bit RSA
   certificate created in Setup → Certificate and Key Management (NOT handed to
   you by the Key Management page). Download it.
2. Generate 256 bits of key material in your KMS or on an offline host.
3. Wrap (encrypt) that material with the certificate's public key.
4. Compute the SHA-256 hash of the PLAINTEXT key material and encrypt that hash
   with the same public key. This is a separate, required artifact — Salesforce
   uses it to validate that the material you uploaded is the material you
   generated.
5. Base64-encode BOTH the wrapped key material and the wrapped hash. The Upload
   Tenant Secret screen takes TWO files, not one. An upload of the wrapped
   material alone is rejected.
6. Salesforce validates the wrapping and activates it as the current tenant secret.
7. Retain your copy of the unwrapped material in your KMS. Salesforce does not
   return it.
```

An **illustrative** wrapping — read the warning above before running any of it:

```bash
# 256 bits = 32 bytes of key material
openssl rand -out tenant_secret.bin 32

# Wrap with the BYOK certificate's public key.
# PADDING MODE UNVERIFIED — confirm against Salesforce's BYOK article before use.
openssl pkeyutl -encrypt \
  -pubin -inkey salesforce_cert_pubkey.pem \
  -pkeyopt rsa_padding_mode:oaep \
  -in  tenant_secret.bin \
  -out tenant_secret_wrapped.bin

# The second required artifact: SHA-256 of the PLAINTEXT secret, wrapped the
# same way. Omitting this is the most common reason an upload is rejected.
openssl dgst -sha256 -binary -out tenant_secret_hash.bin tenant_secret.bin
openssl pkeyutl -encrypt \
  -pubin -inkey salesforce_cert_pubkey.pem \
  -pkeyopt rsa_padding_mode:oaep \
  -in  tenant_secret_hash.bin \
  -out tenant_secret_hash_wrapped.bin

# Base64 both files for upload
base64 -i tenant_secret_wrapped.bin      -o BYOK.b64
base64 -i tenant_secret_hash_wrapped.bin -o BYOK_hash.b64
```

**Why it works:** Salesforce can derive the DEK but never held the unwrapped
material in a form it generated. Destroying the tenant secret in Salesforce renders
data encrypted under it unreadable — crypto-shredding, which is the property the
compliance requirement is usually reaching for.

**Two rate limits that shape the runbook:**

> "Customer-supplied key material can be uploaded once every 24 hours in production
> and Developer Edition orgs, and every 4 hours in sandbox orgs."

So a rotation cannot be retried immediately if it goes wrong, and a production
rehearsal cannot be compressed. Rehearse in a sandbox, where the window is four
hours.

**Rotation semantics:**

> "When customer-supplied tenant secrets are uploaded, subsequent data is encrypted
> either with the key derived from the current primary secret and the new
> customer-supplied tenant secret or the new DEK alone."

Rotation applies to *subsequent* writes. Existing data stays under the previous
secret until it is re-encrypted, which is a separate, explicitly triggered job. A
rotation runbook that ends at "uploaded successfully" has done half the work.

---

## Example 2: Cache-Only Key Service — and the availability contract you are signing

**Context:** A financial services org's policy forbids key material persisting in
any third-party system, including in wrapped form.

**Solution shape:**

- Stand up an HTTPS key service you control, reachable by Salesforce.
- It returns 256-bit AES key material in a JSON response, wrapped using JSON Web
  Encryption (JWE): the service is "compatible with 256-bit AES keys returned in a
  JSON response, and then wrapped using JSON Web Encryption (JWE)."
- Register the callout endpoint in Key Management and activate the cache-only key.

**The behaviour that determines your SLO:**

> "After the cache is flushed, the Cache-Only Key Service fetches key material from
> your specified key service. The cache is regularly flushed every 72 hours. Certain
> Salesforce operations flush the cache on average every 24 hours."

Read that carefully, because it cuts both ways.

- **It is not a callout per decryption.** The key is cached, so steady-state
  latency is unaffected. The naive "every read makes an HTTP call" model is wrong.
- **It is a hard dependency on a schedule you do not control.** A flush can happen
  at any time, and "certain Salesforce operations" flush on average every 24 hours.
  If your key service is unavailable at that moment, encrypted fields cannot be
  decrypted until it returns.

So the availability question is not "can my KMS survive a burst of traffic" — it is
"can my KMS be unavailable for any window at all, at a time Salesforce chooses."

**Replay detection**, which is worth enabling and worth understanding:

> "When enabled, replay detection inserts an autogenerated, unique marker called a
> `RequestIdentifier` into every callout, which includes the key identifier, a nonce
> generated for that callout instance, and the nonce required from the endpoint."

Your key service must echo the required nonce. A service that ignores it will fail
the callout once replay detection is on — so implement and test that path *before*
enabling it, not after.

**The runbook this design obliges you to write:**

```text
Detection    Alert on Salesforce decryption errors AND on key service
             availability independently. A key service that is up but
             answering incorrectly produces the same user-visible symptom.
Escalation   Who can restore the key service, at 03:00, on a weekend.
Fallback     Documented and REHEARSED path back to a Salesforce-managed or
             BYOK tenant secret. If this path is not rehearsed, it does not
             exist.
Comms        What users see (errors on record pages, failing integrations)
             and who tells them.
```

**Why teams choose this anyway:** immediate, unilateral revocation. Stopping your
key service makes the data unreadable on the next cache flush without Salesforce's
involvement. If that is a contractual requirement, this is the only model that
provides it. If it is not, BYOK gives you key provenance and crypto-shredding
without the runtime dependency.

---

## Example 3: Rehearse destruction, in a sandbox, on a schedule

**Context:** A control statement claims "we can render customer data unreadable on
demand." Nobody has ever done it.

**Problem:** Key destruction is the one control whose *first* execution must not be
in production during an incident. It is also the one nobody wants to test, because
success looks like data loss.

**Solution — a quarterly sandbox rehearsal:**

```text
1. In a sandbox with the same encryption policy as production, confirm a
   representative record's encrypted field is readable.
2. Destroy the active tenant secret.
3. Confirm the field is now unreadable, and capture what the failure looks like:
   the UI error, the Apex exception, the integration response.
4. Restore or generate a new tenant secret.
5. Confirm that data written AFTER the new secret is readable, and that data
   written before remains unreadable.
6. Record the elapsed time for each step.
```

Step 3 is the deliverable. "The data becomes unreadable" is a claim; a screenshot of
the actual error message, the Apex exception type, and the integration's HTTP
response is evidence — and it is what your support desk will need when it happens
for real.

Step 5 is the part people get wrong: destroying a tenant secret is **not**
reversible for data already written under it. There is no recovery path. That is the
feature, and it is why this is rehearsed in a sandbox.

The sandbox upload window is four hours rather than 24, which is precisely why the
rehearsal belongs there.

---

## Example 4: Choosing the model — a decision you write down once

**Context:** A security architect is asked "should we use BYOK?"

**The wrong framing:** BYOK is more secure than Salesforce-managed, and Cache-Only
is more secure than BYOK, so pick the highest one you can afford.

**The right framing:** each model answers a different compliance sentence, and each
carries a different operational obligation.

| The requirement says | Model | What you take on |
|---|---|---|
| "Data must be encrypted at rest" | Salesforce-managed | Key rotation schedule, re-encryption after rotation |
| "The customer must be the origin of key material" or "the customer must be able to destroy the key" | **BYOK** | The above, plus generating and wrapping material, a secure store for your copy, and a 24-hour upload window in production |
| "Key material must never persist in the vendor's systems" or "the customer must be able to revoke access unilaterally and immediately" | **Cache-Only** | All of the above, plus a key service with an availability SLO at least as strong as your Salesforce SLO, replay detection, and a rehearsed fallback |

**Write the decision down in this form:**

```text
Model chosen:      BYOK
Requirement:       <cite the specific clause, policy, or regulation>
Rejected:          Cache-Only — no contractual requirement for non-persistence,
                   and we cannot commit to a key service SLO matching our
                   Salesforce availability target.
Rotation cadence:  Quarterly, with re-encryption of existing data as a distinct
                   step in the same runbook.
Destroy rehearsal: Quarterly in the UAT sandbox. Owner: <name>.
Fallback:          Documented and rehearsed path to Salesforce-managed secrets.
```

**Why this matters:** without the requirement cited, the next reviewer cannot tell
whether Cache-Only was rejected on analysis or on effort — and the org drifts toward
the strongest-sounding option regardless of whether it can operate it.

---

## Anti-Pattern: Treating a key model as a substitute for field-level security

**What practitioners do:** deploy BYOK or Cache-Only Keys and record "customer PII
is protected by customer-managed keys" as the access control.

**What goes wrong:** the key model changes *who controls the key*. It does not
change *who can read the field*. Shield Platform Encryption is transparent above the
storage layer: every user with field-level security Read sees plaintext, exactly as
before, regardless of whether the tenant secret is Salesforce-managed, uploaded, or
fetched from your own KMS. The strongest possible key model protects against a
storage-layer compromise and against Salesforce itself; it protects against nothing a
logged-in user does.

**Correct approach:** run key management and access control as two separate
workstreams with two separate deliverables. The key model answers "who can decrypt
the database." The FLS matrix answers "who can see the value," and it is the only
lever that changes need-to-know. A design document that cites a key model in the
access-control section has conflated them.
