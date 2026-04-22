# LLM Anti-Patterns — Metadata API Retrieve / Deploy

Common mistakes AI coding assistants make when scripting retrieves and deploys.

## Anti-Pattern 1: Wildcard package.xml for CI deploys

**What the LLM generates:**

```xml
<types><members>*</members><name>ApexClass</name></types>
<types><members>*</members><name>CustomObject</name></types>
```

**Why it happens:** Model optimizes for "get everything" rather than diff-driven deploys.

**Correct pattern:**

```
CI deploys must be reproducible and reviewable. Wildcards pull
whatever exists in the source at retrieve time — drift becomes
invisible. Use explicit members tied to the change:

<types>
    <members>AccountTrigger</members>
    <members>AccountTriggerHandler</members>
    <name>ApexClass</name>
</types>

Reserve wildcards for one-off "baseline snapshot" captures.
```

**Detection hint:** `package.xml` in a CI repo with `<members>*</members>`.

---

## Anti-Pattern 2: `rollbackOnError=false` on production

**What the LLM generates:** `sf project deploy start --ignore-errors` or suggests `rollbackOnError=false`.

**Why it happens:** Model wants to get past a partial failure.

**Correct pattern:**

```
Partial production deploy = orphaned fields, half-migrated triggers,
profiles pointing to deleted metadata. The default (true) is safe:
if any component fails, the whole deploy rolls back.

If individual failures are expected, fix the manifest — don't suppress
the rollback. On sandbox scratch work, --ignore-warnings is usually
enough; reserve --ignore-errors only for explicit cleanup scripts
with rollback runbooks.
```

**Detection hint:** `--ignore-errors` flag on a production deploy command.

---

## Anti-Pattern 3: Destructive changes in the wrong file

**What the LLM generates:** Adds deletions to `package.xml` instead of a destructive manifest.

**Why it happens:** Model conflates "remove from org" with "remove from manifest."

**Correct pattern:**

```
package.xml is an ADD/UPDATE list. Removals belong in:

- destructiveChangesPre.xml: run BEFORE adds (use when renaming —
  drop the old field first so the new name is free)
- destructiveChanges.xml: run AFTER adds (use when new metadata
  replaces old — keeps old around until replacement deploys)

Pair with an empty package.xml containing only <version>.
```

**Detection hint:** CustomField or ApexClass name in `package.xml` that the author intends to delete.

---

## Anti-Pattern 4: `NoTestRun` for production

**What the LLM generates:** `--test-level NoTestRun` to speed up prod deploys.

**Why it happens:** Model assumes sandbox behavior extends to prod.

**Correct pattern:**

```
Production rejects NoTestRun. Valid levels for prod:

- RunSpecifiedTests: list the tests covering changed code (fastest)
- RunLocalTests: all non-managed tests (safest for broad changes)

Use validate → quick-deploy to avoid running the same tests twice:

sf project deploy validate --test-level RunLocalTests → <jobId>
sf project deploy quick --job-id <jobId>
```

**Detection hint:** Deploy command targeting production with `--test-level NoTestRun`.

---

## Anti-Pattern 5: Username/password auth in CI

**What the LLM generates:**

```
sf org login --username x --password y
```

**Why it happens:** Model reaches for the simplest auth path.

**Correct pattern:**

```
CI should use JWT bearer flow with a digitally-signed token:

1. Generate server.key + server.crt
2. Upload cert to a Connected App with OAuth → use digital signatures
3. Store CONSUMER_KEY + server.key as CI secrets
4. Login:
   sf org login jwt \
     --username ci@example.com \
     --jwt-key-file server.key \
     --client-id $CONSUMER_KEY \
     --instance-url https://login.salesforce.com

No passwords, no tokens rotated every 90 days, no MFA friction.
```

**Detection hint:** `sf org login --password` or hard-coded credentials in CI scripts.
