# LLM Anti-Patterns — OmniScript Session State

Mistakes AI coding assistants reliably make when designing OmniScript
save-and-resume. Each entry names the wrong output, the mechanism producing it,
the corrected version, and a mechanical check.

---

## Anti-Pattern 1: A Purge Job Against `OmniScriptSavedSession`

**What the LLM generates:** a clean, plausible retention job:

```apex
// UNSUPPORTED — this object is marked internal use only
global class PurgeSavedSessions implements Schedulable {
    global void execute(SchedulableContext ctx) {
        delete [SELECT Id FROM OmniScriptSavedSession
                WHERE CreatedDate < LAST_N_DAYS:30];
    }
}
```

**Why it happens:** The object is real, queryable, and has a `CreatedDate` —
everything that makes an object look like a normal target for a retention job.
The internal-use-only marking lives in the *object reference*, not in the Save
for Later documentation the model is reasoning from, so nothing in the immediate
context contradicts it. And the generated code is idiomatic Salesforce that will
compile and may even run.

**Correct pattern:**

```text
Object reference, OmniScriptSavedSession (API 51.0 - 67.0):

  "This object and associated records are only for internal use. Don't
   perform any create, edit, or delete operations on this object."
  "Modifying or deleting this object's records may result in errors with
   your implementation."

If a retention obligation attaches to the state, the state must live in an
object you own:

  1. Turn native Save for Later OFF for that OmniScript.
  2. Persist answers to Application_Session__c at step boundaries.
  3. Purge Application_Session__c on your schedule.
  4. Resume by pre-populating from your object.

Read OmniScriptSavedSession for inventory or counts. Never write to it.
```

**Detection hint:** Mechanical. Any `insert`, `update`, `upsert`, or `delete`
DML — or any Data Loader / Bulk API job — targeting `OmniScriptSavedSession`.
Also flag any compliance or retention design whose deletion step targets an
object marked "for internal use only" in the object reference.

---

## Anti-Pattern 2: Answers Serialised Into The Resume URL

**What the LLM generates:**

```text
Resume link: https://portal.example.com/s/resume?state=eyJhcHBsaWNhbnQiOnsi...
```

**Why it happens:** The stateless-token pattern is genuinely elegant and
genuinely correct in several architectures the model has learned from — signed
JWTs carrying claims, stateless session cookies, magic links encoding a
redirect. Encoding state into the link avoids a server-side store, which reads
as a simplification. Base64 also *looks* like a protective transformation, and
nothing in the generated output signals that it is a rename rather than an
encryption.

**Correct pattern:**

```text
The URL carries an OPAQUE token and nothing else.

  Never in the URL: answers in any encoding; PII; a raw session record Id;
                    anything still valid tomorrow.
  In the URL:       a random token indexing a server-side row.
  On the server:    store a HASH of the token, bind it to its subject,
                    expire in hours not days, single-use where possible.
  On the page:      set a referrer policy - any outbound link can otherwise
                    leak the token in the Referer header.

Practical failure too: URLs have length limits a serialised multi-step
application will exceed, so this breaks for exactly the long sessions it
was meant to serve.
```

**Detection hint:** Any `btoa`, `JSON.stringify` → base64, or `encodeURIComponent`
of a state object reaching a URL. Any resume URL parameter longer than ~64
characters. Any resume link containing a Salesforce record Id.

---

## Anti-Pattern 3: Platform Cache As The Session Store

**What the LLM generates:** `Cache.Session` to hold answers between steps,
justified as fast and requiring no data model:

```apex
// WRONG STORE — this is user input, not a cached read
Cache.Session.put('omniAnswers', JSON.serialize(answers));
```

**Why it happens:** "Session state" and "session cache" share a word, and the
model matches on it. Cache also genuinely solves the shape of the problem —
key/value, scoped to a user, fast — so nothing about the fit feels wrong. The
disqualifying properties are all in a limits table the model is not consulting.

**Correct pattern:**

```text
Session cache's documented properties disqualify it for user input:

  max TTL 28,800 s (8 hours)
  "expires when its specified time-to-live value is reached OR when the
   user session expires, whichever comes first"     -> logout destroys it
  "Cache isn't persisted. There's no guarantee against data loss."
  "Data in the cache isn't encrypted."
  maximum size of a single cached item: 100 KB
  cache keys: alphanumeric only, max 50 characters

Right store per requirement:
  survive a refresh in one session   -> native Save for Later, or custom object
  survive a logout / device change   -> custom object. Not cache.
  multi-day resume with retention    -> custom object + expiry field + purge job
  very high volume, long retention   -> Big Object (design the index FIRST)
  speed up a repeated READ           -> Platform Cache, via a cacheable IP
```

**Detection hint:** Any `Cache.Session` or `Cache.Org` write whose value is user
input rather than a fetched read. Any design where losing the cache loses the
user's work rather than costing a round trip.

---

## Anti-Pattern 4: Saving On Every Keystroke

**What the LLM generates:** an `onchange` handler that persists on every input
event, for a "real-time" feel.

**Why it happens:** Autosave-on-change is the modern web default — it is what
every document editor and form builder does, and the model reproduces the
familiar UX. What it does not carry from that context is that those systems
persist a small delta to a purpose-built store, whereas here each save posts the
*entire* accumulated payload, against a 4 MB ceiling, through the platform's
save path.

**Correct pattern:**

```text
Save at STEP boundaries, not on input.

Each save posts the whole payload, not a delta. At a 4,194,304-character
ceiling, per-keystroke saves are simultaneously the most expensive and the
least useful cadence available.

If a mid-step save is genuinely required (a long single step, a known
abandonment point), debounce it - and justify it in the design, because the
default answer is the step boundary.
```

**Detection hint:** Any persistence call bound to an input/change/keyup event
rather than a navigation or step-completion event. Any autosave interval under a
few seconds.

---

## Anti-Pattern 5: A Session Object With No Expiry Field

**What the LLM generates:** a session custom object modelled like any other
business record — the state fields, a status, an owner — and no retention
mechanism:

```text
Application_Session__c
    Applicant_Name__c    Text(255)
    SSN__c               Text(11)
    DOB__c               Date
    Answers_JSON__c      Long Text Area
    Step__c              Text(50)
```

**Why it happens:** The model designs the object from the *functional*
requirement it was given — hold the answers, know the step — and retention is a
non-functional requirement nobody stated. Salesforce data modelling conventions
also do not include an expiry field by default, so nothing in the pattern
library prompts for one. The result is a permanent store built to hold
transient data.

**Correct pattern:**

```text
Application_Session__c
    Answers_JSON__c    Long Text Area   ENCRYPTED   (payload)
    SSN_Token__c       Text             tokenized, not the value
    ExpiresAt__c       DateTime         PLAINTEXT - the purge filters on it
    Status__c          Picklist         PLAINTEXT - the purge filters on it
    Version__c         Number           concurrency detection
    LastSavedAt__c     DateTime

Rules:
  - the fields you FILTER on are never the fields you ENCRYPT (Shield
    encryption restricts SOQL filtering)
  - a scheduled purge deletes on ExpiresAt__c
  - retention tier is a compliance decision, confirmed with the data owner,
    recorded in the design - not chosen by the developer
```

**Detection hint:** Any session or staging object with no expiry/TTL field, or
with no scheduled job referencing it. Any PII field on such an object stored as
plain text. Any encrypted field used in a `WHERE` clause.

---

## Anti-Pattern 6: Silent Last-Write-Wins

**What the LLM generates:** a save path that writes unconditionally, because
concurrency was not mentioned in the prompt.

**Why it happens:** Optimistic concurrency is extra code solving a problem that
is invisible in a single-user test. The model implements the requirement as
stated. Worse, the platform will not correct it: multi-user editing of a saved
session is *unsupported* rather than *blocked*, so the second write is accepted
and the damage surfaces later, to a different user.

**Correct pattern:**

```text
Native Save for Later: multi-user editing is NOT SUPPORTED and NOT BLOCKED.
"If a second user edits and saves a session created by another user, data
inconsistencies or save errors can occur when the original user resumes."

So model handoff as a record-ownership change, not a shared session:
    user A submits to a record you own and ends their session
    user B starts a NEW instance pre-populated from that record

If genuine concurrent editing is required, use a custom object:
    on save: compare in-memory Version__c to stored Version__c
             match    -> write, increment
             mismatch -> route to an explicit conflict branch
             never silently overwrite
```

**Detection hint:** Any session save with no version or timestamp comparison.
Any design proposing that two users work the same saved session. Any "supervisor
picks up an agent's application" requirement satisfied by sharing a session
rather than transferring a record.

---

## Anti-Pattern 7: Ignoring Version Binding On Deploy

**What the LLM generates:** a deployment plan that deactivates an OmniScript,
ships a new version, and reactivates — with no mention of in-flight sessions.

**Why it happens:** Deactivate/reactivate is the standard OmniScript release
motion, and it is correct for the component. The interaction with saved sessions
is stated only in the Save for Later considerations, which a deployment-focused
prompt gives the model no reason to consult. The model is answering a deployment
question correctly and a data question by omission.

**Correct pattern:**

```text
"Saved sessions are tied to the OmniScript definition version that was
active at the time the session was created. If an OmniScript is deactivated
and reactivated, previously saved sessions don't resume as the same
instance; instead, a new OmniScript instance is created, and older saved
instances remain stored in the system."

So an activation change is a MIGRATION EVENT:
  1. count in-flight saved sessions; can the change wait for the tail?
  2. notify affected users BEFORE the deploy, not after an empty form
  3. if state must survive version changes, mirror answers into a custom
     object at step boundaries - the native saved session cannot do this
  4. record orphaned-instance growth in the retention risk register:
     they persist, and you cannot purge them through supported DML
```

**Detection hint:** Any OmniScript release plan that changes `isActive` without
a section on in-flight sessions. Any answer to "how do I ship a fix to a live
OmniScript" that does not mention the saved-session consequence.

---

## Anti-Pattern 8: Persisting Lookup Data With The Session

**What the LLM generates:** a session payload containing everything in the
script's data JSON — the answers *and* the product catalog, code tables, and
picklist option sets the script loaded to render them.

**Why it happens:** "Save the session" reads as "save the state," and from the
model's vantage point the data JSON *is* the state — there is no visible
distinction between what the user supplied and what the script fetched. The
resulting payload is also correct in the sense that resuming from it works,
until it crosses the ceiling.

**Correct pattern:**

```text
Save for Later fails above 4,194,304 characters (4 MB), and the network
payload is significantly larger than the visible Data JSON.

The saved session contains the user's ANSWERS. Nothing else.

  Re-fetch on resume:  catalogs, code tables, picklist option sets,
                       anything loaded to DISPLAY the answers
  Store elsewhere:     file content - keep an id
  Prune:               derived values recomputable from the answers

Typical reduction: an order of magnitude, and resume gets faster too.

Failure signature if you skip this: works in test (short scripts, small
data), fails in production, later in the script, for the users with the
most entered data.
```

**Detection hint:** Any saved payload containing a collection the user did not
enter. Any session design with no measurement of the request payload at the
final step. Ask for the byte count at the last step; if nobody has it, the
design is unverified.
