# LLM Anti-Patterns — Sandbox Post-Refresh Automation

Mistakes AI assistants make when advising on `SandboxPostCopy`.

---

## Anti-Pattern 1: `public class` instead of `global class`

**What the LLM generates.**

```apex
public class SandboxPrep implements SandboxPostCopy {
    public void runApexClass(SandboxContext context) { ... }
}
```

**Why it happens.** Default Apex access modifier is `public`; the
LLM emits the safe-looking option.

**Correct pattern.** `global` for both class and method.
`SandboxPostCopy` is a system interface; implementations need
`global` to be invokable by the platform.

**Detection hint.** Any post-copy class without `global` won't
satisfy the interface.

---

## Anti-Pattern 2: Non-idempotent email masking

**What the LLM generates.**

```apex
for (User u : [SELECT Id, Email FROM User]) {
    u.Email = u.Email.replace('@', '+sandbox@') + '.invalid';
    update u;
}
```

**Why it happens.** Single-pass logic looks correct.

**Correct pattern.** Filter out already-masked records:

```apex
for (User u : [SELECT Id, Email FROM User WHERE Email NOT LIKE '%.invalid' AND Email != NULL]) {
    ...
}
```

**Detection hint.** Any masking / scrubbing code that doesn't
filter out the already-applied state will compound on re-run.

---

## Anti-Pattern 3: Forgetting to abort scheduled jobs

**What the LLM generates.** Post-copy that masks emails and
scrubs endpoints but doesn't touch CronTrigger.

**Why it happens.** Scheduled jobs are out-of-sight; the LLM
focuses on the visible concerns.

**Correct pattern.** `System.abortJob` for every CronTrigger that
might mutate external state (or every CronTrigger, with
documented exceptions for sandbox-needed jobs).

**Detection hint.** Any post-copy class that doesn't query
`CronTrigger` is leaving production batches running in sandbox.

---

## Anti-Pattern 4: Hardcoded sandbox name branching with no fallback

**What the LLM generates.**

```apex
if (context.sandboxName() == 'Dev') { ... }
else if (context.sandboxName() == 'Full') { ... }
// no else
```

**Why it happens.** The LLM emits the conditions for known
sandboxes; doesn't surface that an admin-renamed or new sandbox
falls through.

**Correct pattern.** Always include a default branch:

```apex
} else {
    // Unknown sandbox name — apply common safety steps.
    maskEmails();
    abortAllScheduledJobs();
}
```

**Detection hint.** Any sandbox-name branch chain without a
fallback will silently skip prep on new sandboxes.

---

## Anti-Pattern 5: Mutating Named Credential URL via Apex

**What the LLM generates.**

```apex
NamedCredential nc = [SELECT Id, Endpoint FROM NamedCredential WHERE DeveloperName = 'Acme_API' LIMIT 1];
nc.Endpoint = 'https://sandbox.example.com';
update nc;
```

**Why it happens.** Looks like normal SObject DML.

**Correct pattern.** Named Credentials' URL is metadata-only; not
Apex-mutable. Pre-deploy sandbox-pointing NC metadata via CI
metadata deploy as a separate post-copy step.

**Detection hint.** Any Apex DML against `NamedCredential` for
the URL field is wrong.

---

## Anti-Pattern 6: Building post-copy in sandbox without prod deployment

**What the LLM generates.** "Implement `SandboxPostCopy` and
configure it on your sandbox."

**Why it happens.** "Sandbox automation" sounds like sandbox-only
code.

**Correct pattern.** The class must be deployed to PRODUCTION
first; the sandbox copies it from prod on refresh. Configure on
each sandbox in Setup → Sandboxes.

**Detection hint.** Any deployment plan that skips "deploy to
prod first" leaves sandbox refresh with no class to invoke.

---

## Anti-Pattern 7: No test class for the post-copy

**What the LLM generates.** Just the post-copy class, no test.

**Why it happens.** Test classes are extra work; the LLM emits
the visible code only.

**Correct pattern.** Test class using
`Test.testSandboxPostCopyScript`. Asserts each method's effects.
Required for prod deploy under the org-wide 75% coverage rule.

**Detection hint.** Any sandbox-prep recipe without a
corresponding test class will fail the prod deploy.

---

## Anti-Pattern 8: Single huge `runApexClass` method

**What the LLM generates.**

```apex
global void runApexClass(SandboxContext context) {
    // 200 lines of mixed concerns inline
}
```

**Why it happens.** Convenience.

**Correct pattern.** One `private static` helper per concern
(mask, deactivate, scrub, abort, populate, configure). The
`runApexClass` body is a flat list of helper calls. Readable;
testable individually; failure of one helper doesn't break the
others (with try/catch wrapping).

**Detection hint.** Any post-copy class with `runApexClass` >
40 lines is going to be hard to maintain; should refactor into
helpers.
