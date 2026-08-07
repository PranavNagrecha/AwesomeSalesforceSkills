# LLM Anti-Patterns — Sandbox Data Masking

Common mistakes AI coding assistants make when generating or advising on Salesforce Data Mask configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Data Mask Works on Shield-Encrypted Fields

**What the LLM generates:** "Configure Data Mask to mask the SSN field" without checking whether the field is encrypted with Shield Platform Encryption.

**Why it happens:** Training data rarely mentions the silent skip behavior. LLMs assume all field types are maskable because the Data Mask documentation emphasizes broad field coverage.

**Correct pattern:**

```
Before adding any field to a Data Mask policy, check whether Shield Platform
Encryption is enabled on that field (Setup > Platform Encryption > Encryption
Policy). Data Mask silently skips encrypted fields — no error, no warning in the
job log. The real value remains in the sandbox. Handle encrypted fields with a
separate anonymization strategy or deprovision them before sandbox copy.
```

**Detection hint:** If the advice configures masking on fields without verifying encryption status, it risks leaving real PII in the sandbox.

---

## Anti-Pattern 2: Recommending Null Masking on Required Fields

**What the LLM generates:** "Use Delete/Null masking on all PII fields to eliminate data" without checking field-level required settings.

**Why it happens:** Null masking is the simplest option and LLMs default to the simplest solution. Training data does not emphasize the batch-abort failure mode for required fields.

**Correct pattern:**

```
Never configure Null/Delete masking on a field that has a Required field-level
setting. The Data Mask batch job will abort mid-run with a DML error, leaving
some records masked and others with original values — a partial-mask state that
is worse than no masking at all. Use Library or Pattern masking for required fields
to replace values with realistic fakes while satisfying the required constraint.
```

**Detection hint:** If the advice uses Null masking without verifying required-field settings, it will cause batch failures and inconsistent data states.

---

## Anti-Pattern 3: Assuming Data Mask Cascades Across Related Objects

**What the LLM generates:** "Mask Contact.Email and all related records will be updated" or advice that implies masking automatically propagates to lookup-related objects.

**Why it happens:** LLMs infer cascading behavior from general database masking concepts. Salesforce Data Mask is per-field with no relationship traversal.

**Correct pattern:**

```
Data Mask does not cascade to related objects. If Contact.Email is masked but
the same email address appears on Support_Request__c.Requester_Email__c, the
custom object retains the real value. Every field containing PII must be
explicitly included in the masking policy, object by object. Cross-reference
all objects that copy or mirror PII fields before marking the policy complete.
```

**Detection hint:** If the advice masks a field on one object and claims related records are handled, it is wrong. Look for explicit per-field coverage across all objects.

---

## Anti-Pattern 4: Omitting SandboxPostCopy Automation

**What the LLM generates:** "After refreshing the sandbox, run the Data Mask job manually from the app."

**Why it happens:** Training data describes the manual workflow. LLMs do not consistently recommend automation because the SandboxPostCopy integration is a more advanced pattern.

**Correct pattern:**

```
Manual post-refresh masking creates a window where developers can access real
data before masking completes. Implement a SandboxPostCopy Apex class that
triggers the Data Mask job automatically at the end of each sandbox refresh.
Lock sandbox access behind a read-only permission set until the masking job
log confirms successful completion.
```

**Detection hint:** If the advice relies entirely on manual masking steps without mentioning SandboxPostCopy automation, it leaves a compliance gap during every refresh cycle.

---

## Anti-Pattern 5: Forgetting Data Mask Is Unavailable on Developer Sandboxes

**What the LLM generates:** "Set up Data Mask in your Developer sandbox to test the configuration."

**Why it happens:** LLMs do not consistently distinguish between sandbox tiers. Data Mask is only available on partial copy and full copy sandboxes.

**Correct pattern:**

```
Data Mask requires a partial copy or full copy sandbox. It is not available on
Developer or Developer Pro sandboxes. For Developer sandboxes, do not copy
production data at all — use synthetic seeded data instead. If testing Data Mask
configuration, use a partial copy sandbox.
```

**Detection hint:** If the advice mentions configuring Data Mask in a Developer sandbox, the sandbox tier constraint has been missed.

---

## Anti-Pattern 6: Not Verifying Masking with SOQL Spot-Checks

**What the LLM generates:** "Run the Data Mask job and confirm it completes successfully" without verifying that values actually changed.

**Why it happens:** LLMs equate job completion with success. The silent-skip behavior for encrypted fields and partial failures from required-field issues mean a successful job log does not guarantee all fields were masked.

**Correct pattern:**

```
After every Data Mask job, run SOQL spot-checks against known PII fields:
  SELECT Email FROM Contact LIMIT 5
  SELECT Phone FROM Contact LIMIT 5
Verify that values do not match known production patterns (real domains, real
phone formats). Check the Data Mask job log for any skipped fields or errors.
Do not grant sandbox access until spot-checks confirm masking.
```

**Detection hint:** If the advice considers the masking job log as sufficient verification without data-level spot-checks, it misses silent failures.

---

## Anti-Pattern: Inventing "Pseudonymous" and "Deterministic" Data Mask Masking Types

**What the LLM generates:** "Data Mask provides three masking strategies per field: Pseudonymous, Deterministic, and Null/Delete" — usually with a fluent, plausible description of each, and often an example configuring "Deterministic" masking so a value stays consistent across two objects.

**Why it happens:** Two distinct pressures. (1) *Pseudonymisation* and *deterministic masking* are real, standard data-privacy vocabulary (GDPR Article 4 defines pseudonymisation; deterministic masking is a genuine category in Informatica, Delphix and other masking tools), so the model reaches for the industry term instead of the product's own label. (2) "Deterministic" is *Salesforce* vocabulary — it is one of the two Shield Platform Encryption schemes — so it feels in-family, and the model imports it from the neighbouring product. Both wrong names sound more technical than the real ones, which is why they read as authoritative.

**Why the "Deterministic" one is worse than a naming error:** the capability it describes does not exist and cannot exist. Data Mask is irreversible by design — Salesforce Help: "When you mask sandbox data, you can't unmask it." A stable input-to-output mapping is exactly what would make masking reversible by frequency analysis, so it is a property the product deliberately does not offer. A team that plans its sandbox test strategy around cross-object masking consistency has planned around a guarantee no configuration can deliver, and will discover this only when the join-based tests fail after the first refresh.

**Correct pattern:**
```
Salesforce Data Mask masking types — all four, and there are only four:

  Replace with Random Characters   fast; result is not realistic-looking
  Replace from Library             realistic values from a Salesforce-supplied
                                   library; slowest of the four
  Replace Using Pattern            for fields that must keep a specific shape
  Delete                           fastest; not for required fields or fields
                                   under a non-blank validation rule

Speed, fastest to slowest: Delete → Random Characters → Pattern → Library.

Masking is IRREVERSIBLE. There is no same-input-same-output guarantee and no
setting that provides one. If two objects must carry a matching value after
masking, mask both and reconcile them with your own post-mask Apex/data job,
wired into the same SandboxPostCopy implementation.
```

**Detection hint:** the tokens `Pseudonymous` or `Deterministic` in any Data Mask context are always wrong — as is any count other than four. `Deterministic` is legitimate Salesforce vocabulary *only* alongside Shield Platform Encryption (`probabilistic` will normally be nearby); if it appears near `sandbox`, `Data Mask`, `SandboxPostCopy` or `partial copy`, it has been imported from the wrong product. A second, sharper tell: any claim that a masking setting preserves cross-object joins contradicts the documented irreversibility and is unsupportable on its face.
