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

**Correct pattern.** `global` for both class and method, matching every Salesforce-authored sample
(Apex Reference Guide L228952, L228975).

UNVERIFIED (2026-09-05): the guide states nowhere that a `public` implementation is rejected, and its
interface member-signature line is itself written `public void runApexClass(System.SandboxContext context)`
(L228926). Treat `global` as the strongly-recommended shape, not a proven hard requirement — and note the
real cost of being wrong is that a failed refresh gives you no error to read.

**Detection hint.** Any post-copy class without `global`. Flag it; do not claim the platform will reject it.

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

**Correct pattern.** Always include a default branch (excerpt — the tail of the dispatch `if/else` chain):

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

**Correct pattern.** Named Credentials are a metadata type; deploy sandbox-pointing NC metadata via CI
as a separate step after the sandbox is unlocked. Custom Settings and Custom Metadata are the
Apex-mutable alternatives.

UNVERIFIED (2026-09-05): no statement about `NamedCredential` URL write-access appears in the guides
checked for this skill. The recommendation rests on the deployment shape, not a quoted sentence.

**Detection hint.** Any Apex DML against `NamedCredential` for the URL field.

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

---

## Anti-Pattern 9: The 4-arg `Test.testSandboxPostCopyScript`

**What the LLM generates.**

```apex
Test.testSandboxPostCopyScript(
    new SandboxPrep(), UserInfo.getOrganizationId(), sandboxId, 'MySandbox');
```

**Why it happens.** It is the older, shorter, more-frequently-quoted signature, and it compiles.

**Correct pattern.** The 5-arg overload with `RunAsAutoProcUser = true`. Salesforce recommends it
explicitly (Apex Reference Guide L241180–241184) and its own sample test uses it (L229004–229006).
The 4-arg form runs as the test initiator, so it cannot reproduce the restricted Automated Process
user's access — the failure mode that actually breaks refreshes.

**Detection hint.** Count the arguments. Four is the tell. A green test suite from a 4-arg call is
evidence of nothing about refresh-time behaviour.

---

## Anti-Pattern 10: A constructor that takes arguments and nothing else

**What the LLM generates.**

```apex
global class SandboxPrep implements SandboxPostCopy {
    private Boolean verbose;
    global SandboxPrep(Boolean verbose) { this.verbose = verbose; }
    global void runApexClass(SandboxContext context) { ... }
}
```

**Why it happens.** Constructor injection is good Apex style everywhere else, and the LLM is applying a
correct general habit to the one place it breaks.

**Correct pattern.** Keep a no-arg constructor. The guide's sample says so in a code comment:
"Implementations of SandboxPostCopy must have a no-arg constructor. This constructor is used during the
sandbox copy process" (L228955–228956), and constructors with arguments "won't be used by the sandbox
copy process" (L228958–228960). Parameterised constructors are fine *alongside* the no-arg one — chain
into them from it, as the guide's sample does.

**Detection hint.** A `SandboxPostCopy` implementation with no zero-argument constructor. It compiles,
deploys, passes tests that call `new SandboxPrep(true)`, and cannot be instantiated by the copy.

---

## Anti-Pattern 11: The three-state `CronTrigger` filter

**What the LLM generates.**

```apex
[SELECT Id FROM CronTrigger WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING')]
```

**Why it happens.** Those three states are what almost every blog post and code sample uses, so they
dominate the training distribution. They are also genuinely the three most common.

**Correct pattern.** Six live states. `PAUSED`, `BLOCKED` and `PAUSED_BLOCKED` all resolve back into
running jobs (Object Reference L86799–86811); only `COMPLETE`, `ERROR` and `DELETED` are terminal.

**Detection hint.** An `IN` list of exactly three states. Also worth flagging: any job inventory built
from `AsyncApexJob` instead of `CronTrigger` — "You can't abort a scheduled Apex job using an
AsyncApexJob ID" (L238678–238680).

---

## Anti-Pattern 12: Assuming the copy sanitises user identity

**What the LLM generates.** Advice along the lines of "Salesforce automatically modifies usernames and
email addresses when copying to a sandbox, so no masking is needed" — or a masking routine that derives
the new address from `Username`.

**Why it happens.** The `Username` mutation is real and visible, and generalising from it is the natural
inference. `Username` and `Email` sit adjacent on the record and look like peers.

**Correct pattern.** Only `Username` is rewritten: "In a sandbox named `test`, the username
`user@acme.com` becomes `user@acme.com.test`" (Metadata API Developer Guide L2711–2713). `Email` copies
through verbatim and routable. Derive the mask from `Email`; using `Username` double-suffixes it.

**Detection hint.** Any claim that email is auto-masked, and any masking code that reads `Username`.
