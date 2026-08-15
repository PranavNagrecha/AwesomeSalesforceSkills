# LLM Anti-Patterns — Shield Platform Encryption: BYOK / KMS Setup

Mistakes AI assistants reliably make when asked about customer-managed keys in
Salesforce.

## Anti-Pattern 1: Ranking the Key Models as a Security Ladder

**What the LLM generates:** "Salesforce-managed is basic, BYOK is better, and
Cache-Only Keys are the most secure — choose the highest tier you can support."

**Why it happens:** The three models genuinely increase customer key control, and
"more control is more secure" is a reasonable-sounding heuristic.

**Correct pattern:**

```
Each model answers a DIFFERENT compliance sentence and carries a DIFFERENT
operational obligation:

  "Data must be encrypted at rest"
      -> Salesforce-managed. Rotation + re-encryption.

  "The customer must originate the key material" / "must be able to destroy it"
      -> BYOK. Adds generation, wrapping, a secure store for your copy, and a
         24-hour production upload window.

  "Key material must never persist in the vendor's systems" / "revocation must
   be unilateral and immediate"
      -> Cache-Only. Adds a RUNTIME AVAILABILITY DEPENDENCY on your key service.

Require the requirement to be CITED before recommending a model. Cache-Only
without a contractual driver hands the org an availability dependency it
usually cannot operate. BYOK gives key provenance and crypto-shredding with no
runtime dependency, and is the right answer for most orgs that reach for
Cache-Only.
```

**Detection hint:** any recommendation of Cache-Only Keys that does not name the
specific compliance clause, or any framing of the three models as tiers.

---

## Anti-Pattern 2: "Cache-Only Keys Make a Callout on Every Decryption"

**What the LLM generates:** "Cache-Only Keys add a network round trip to every read
of an encrypted field, so measure decrypt latency under load."

**Why it happens:** "Fetched on demand from your key service" is the model's
headline description, and per-operation fetching is the intuitive reading.

**Correct pattern:**

```
The key is CACHED. Steady-state decryption does not call out, so per-operation
latency is not the concern.

  "After the cache is flushed, the Cache-Only Key Service fetches key material
   from your specified key service. The cache is regularly flushed every 72
   hours. Certain Salesforce operations flush the cache on average every 24
   hours."

The real requirement is AVAILABILITY AT AN ARBITRARY INSTANT that Salesforce
chooses - not throughput. The design implication is a multi-region,
health-checked key service with independent monitoring, not a latency budget.

Alert on the key service directly: one that is UP but answering incorrectly
produces the same user-visible symptom as one that is down, and Salesforce's
error will not distinguish them.
```

**Detection hint:** latency benchmarking advice for Cache-Only Keys, or any claim
about per-decrypt callout cost.

---

## Anti-Pattern 3: Treating Rotation as Complete on Upload

**What the LLM generates:** a rotation runbook ending at "upload the new tenant
secret and confirm it is active."

**Why it happens:** The upload produces a visible success state, and rotation in
most systems applies going forward with no separate backfill.

**Correct pattern:**

```
Rotation applies to SUBSEQUENT writes:

  "When customer-supplied tenant secrets are uploaded, subsequent data is
   encrypted either with the key derived from the current primary secret and
   the new customer-supplied tenant secret or the new DEK alone."

Existing data stays under the previous secret until re-encryption is explicitly
run AND completes. Re-encryption is a long background job on a large object.

Runbook must contain, as separate signed-off steps:
  1. upload and activate the new tenant secret
  2. trigger re-encryption per affected object
  3. verify on the Encryption Statistics page (NOT the key management page -
     that shows which secret is active, not which secret your data is under)
  4. only then close the change

And flag the retry constraint: "Customer-supplied key material can be uploaded
once every 24 hours in production and Developer Edition orgs, and every 4 hours
in sandbox orgs." A failed production upload cannot be retried for a day.
```

**Detection hint:** a rotation plan with no re-encryption step, or one that
verifies against the key management screen.

---

## Anti-Pattern 4: Recommending a Destroy-Key Test Without Saying Where

**What the LLM generates:** "Test your ability to revoke access by destroying the
tenant secret and confirming the data becomes unreadable."

**Why it happens:** It is genuinely good advice, and the destructive scope is
implicit rather than stated.

**Correct pattern:**

```
Say the environment, every time, in the same sentence as the instruction:

  "Rehearse destruction QUARTERLY IN A SANDBOX. Destroying a tenant secret is
   NOT reversible for data already written under it - there is no recovery
   path. That is the feature, and it is why this is never first executed in
   production."

The rehearsal's deliverable is EVIDENCE, not confirmation:
  - the UI error a user sees
  - the Apex exception type
  - the integration's HTTP response
  - elapsed time per step

Production destruction is a data destruction event: second approver, explicit
statement that the data under that secret is being abandoned, governed as such.

The sandbox upload window is 4 hours rather than 24, which is exactly why the
rehearsal belongs there.
```

**Detection hint:** "destroy the key to test" with no environment named, or no
statement that the operation is irreversible.

---

## Anti-Pattern 5: Presenting the Key Model as an Access Control

**What the LLM generates:** "With BYOK, only your organisation can decrypt the
data, so PII is protected from unauthorised access."

**Why it happens:** "Only you hold the key" is true at the storage tier and reads
like an access-control statement.

**Correct pattern:**

```
Shield Platform Encryption is transparent above the storage layer. Under EVERY
key model, every user with field-level security Read sees the same plaintext
they saw before encryption. There is no masked rendering and no decrypt
permission.

The key model protects against:
  - a storage-tier compromise
  - Salesforce itself
  - and, for BYOK/Cache-Only, gives you unilateral crypto-shredding

It protects against NOTHING a logged-in user does.

If the requirement is need-to-know, the deliverable is an FLS matrix, and it is
orthogonal to the key model. Never put a key model in the access-control
section of a design.

Related permission confusion: Manage Encryption Keys (with Customize
Application) governs ADMINISTERING the feature - generating, uploading,
rotating, DESTROYING secrets. It does not govern who can read an encrypted
field.
```

**Detection hint:** a key model cited as the control for a need-to-know or
least-privilege requirement, or **Manage Encryption Keys** described as controlling
read access.

---

## Anti-Pattern 6: Assuming Encryption Is Retroactive

**What the LLM generates:** "Enable the encryption policy on the field and the data
will be encrypted."

**Why it happens:** Enabling a policy is one visible action and models treat it as
complete.

**Correct pattern:**

```
Enabling a policy encrypts data written AFTER activation. Existing records stay
as they are until a re-encryption job is explicitly run AND COMPLETES.

This is the common case, not the edge case: every production org adding Shield
after go-live is a retroactive rollout.

Make re-encryption completion a GATING CRITERION for compliance sign-off, not a
follow-up task. Verify per object on the Encryption Statistics page. Stage the
rollout object by object so each completes before the next begins.

Also flag the interaction with archived history: previously archived Field
Audit Trail data remains unencrypted after Platform Encryption is turned on.
```

**Detection hint:** an encryption rollout plan with no re-encryption step, or one
that treats re-encryption as optional cleanup.

---

## Anti-Pattern 7: Omitting the Key Service's Own Operational Design

**What the LLM generates:** a Cache-Only Key recommendation covering the Salesforce
side — register the endpoint, activate the key — and nothing about the service.

**Why it happens:** The prompt is a Salesforce prompt, so the answer stops at the
Salesforce boundary.

**Correct pattern:**

```
Choosing Cache-Only Keys means committing to operate a key service whose
availability gates your org's ability to read encrypted data. The design owes:

  Availability   SLO at least as strong as the org's Salesforce availability
                 target; multi-region; health-checked
  Response       "compatible with 256-bit AES keys returned in a JSON response,
                 and then wrapped using JSON Web Encryption (JWE)"
  Replay         Implement and TEST the RequestIdentifier / nonce path when the
                 service is first written, even if detection is initially off -
                 enabling it later must be a config change, not a code change
                 under pressure
  Monitoring     On the key service INDEPENDENTLY of Salesforce
  On-call        Who restores it at 03:00 on a weekend
  Fallback       A REHEARSED path back to BYOK or Salesforce-managed. An
                 unrehearsed fallback does not exist.
```

**Detection hint:** a Cache-Only recommendation with no key service SLO, no
monitoring, and no fallback path.
