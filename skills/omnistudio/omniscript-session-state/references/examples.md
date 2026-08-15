# OmniScript Session State — Examples

Two distinct things are called "session state" in this domain and they have
opposite properties. Getting the distinction right is most of the design.

Metadata field names are from the `OmniScript` metadata type (Industries Common
Resources Developer Guide, API 67.0). Save for Later behaviour is from the
Salesforce Help article *OmniScript Save for Later — Considerations and
Limitations* (article 000394956) — see the sourcing caveat in
`references/well-architected.md`.

---

## Example 0: Native Save For Later vs A Custom Session Object

**Context:** Every session-state conversation starts by choosing between these,
and most start by not knowing there is a choice.

| | **Native Save for Later** | **Custom session object** |
|---|---|---|
| Where state lives | `OmniScriptSavedSession` — a standard object | your `Session__c` |
| Can you query it usefully? | it is marked **internal use only** | yes, any shape you index for |
| Can you DML it? | **no** — "Don't perform any create, edit, or delete operations on this object" | yes |
| Can you purge it on your schedule? | not through supported DML | yes |
| Can you encrypt specific fields? | not with field-level control you own | yes, Shield on the fields you choose |
| Build cost | a configuration | a data model, save logic, resume logic, purge job |
| Version coupling | tied to the OmniScript version active when the session was created | none, unless you build it |
| Payload ceiling | Save for Later fails above 4,194,304 characters (4 MB) | your own field/storage limits |

**The decision rule:** if the state contains PII you are obliged to purge on a
schedule, or you need to query across sessions, or the flow is guest-facing —
you need a custom object, because the native store is one you cannot lawfully
manage. If the flow is authenticated, low-sensitivity, and the requirement is
genuinely "let the user come back," native Save for Later is a configuration
rather than a project.

**Why it works:** It puts the constraint that actually decides the answer —
"can I delete this on demand?" — ahead of the constraint everyone starts with,
which is build effort.

---

## Example 1: `OmniScriptSavedSession` Is Internal Use Only

**Context:** A compliance requirement says abandoned applications must be
destroyed after 30 days. The team plans a scheduled Apex job to delete old
saved sessions.

**Problem:** `OmniScriptSavedSession` is a real standard object, present in the
object reference from API 51.0 through 67.0, and the object reference says:

> "This object and associated records are only for internal use. Don't perform
> any create, edit, or delete operations on this object."
>
> "Modifying or deleting this object's records may result in errors with your
> implementation."

The purge job is therefore not a supported design. It may run today and break
on an upgrade, and it is the kind of thing that is discovered during an audit
rather than during testing.

**Solution:**

```text
Requirement: destroy abandoned application state after 30 days.

WRONG:
    scheduled Apex -> DELETE FROM OmniScriptSavedSession WHERE ...

RIGHT:
    1. Turn native Save for Later OFF for this OmniScript.
    2. Persist state to Application_Session__c that you own.
    3. Scheduled job purges Application_Session__c on your schedule.
    4. Resume by loading Application_Session__c and pre-populating,
       not by resuming a native saved session.
```

**Why it works:** The retention obligation attaches to a store you can lawfully
delete from. Any design where the compliance answer is "we delete records from
an object Salesforce marks internal use only" has a defect regardless of
whether the delete currently succeeds.

---

## Example 2: Saved Sessions Are Bound To The OmniScript Version

**Context:** A 12-step onboarding OmniScript. A defect is found in step 7. The
team deactivates version 3, ships version 4, and reactivates.

**Problem:** Saved sessions are tied to the OmniScript definition version that
was active when the session was created. Per the Save for Later considerations:
if an OmniScript is deactivated and reactivated, previously saved sessions do
not resume as the same instance — a new OmniScript instance is created, and the
older saved instances remain stored in the system.

Two consequences, both bad if unplanned:

1. Every in-flight user loses their place. They do not get an error explaining
   why; they get a fresh script.
2. The orphaned instances are still stored — in an object you cannot delete
   from — so the abandoned state persists past the point anyone is tracking it.

**Solution — treat an OmniScript activation change as a migration event:**

```text
Before deactivating a version with in-flight saved sessions:

  1. Count them. Decide whether the change can wait for the tail to drain.
  2. If it cannot, notify affected users BEFORE the deploy, not after they
     find an empty form.
  3. If state must survive the version change, it cannot live in the native
     saved session. Mirror the answers into a custom object at each step
     boundary and resume from there.
  4. Record the orphaned-instance growth in the retention risk register:
     they persist and you cannot purge them through supported DML.

Deployment ordering note: activation is per Type/SubType/Language/Version.
The OmniScript metadata identity fields are:
    uniqueName    = Type_SubType_Language_VersionNumber
    omniProcessKey = Type_SubType
    isActive      (boolean, default false)
```

**Why it works:** It converts a silent data-loss event into a planned one, and
it names the only design — mirroring into a store you own — that actually
survives a version change.

---

## Example 3: The 4 MB Payload Ceiling Is Reached Sooner Than You Think

**Context:** A long insurance application with several file-upload steps and a
large embedded product catalog. Save for Later starts failing intermittently,
then consistently, in the later steps.

**Problem:** Save for Later fails if the total request payload exceeds
**4,194,304 characters (4 MB)**. The critical subtlety: the network payload can
be substantially larger than the Data JSON you see in the debug panel — it
carries the full request, not just the answers you consider "the state."

The failure mode is characteristic: it works in testing (short scripts, small
data) and fails in production for exactly the users who most need it (long
sessions, lots of entered data), and it fails progressively later in the script
as the payload grows.

**Solution:**

```text
Keep the saved payload small by construction:

  1. Do NOT carry lookup data in the OmniScript's data JSON. A product
     catalog, a code table, a list of options loaded once for a picklist —
     re-fetch these on resume from a cacheable Integration Procedure
     instead of persisting them with the session.

  2. Do NOT carry file content. Store the document, keep an id.

  3. Prune derived values. Anything recomputable from the answers is
     payload you are paying for twice.

  4. Measure the actual payload, not the Data JSON, at the LAST step of
     the script - the worst case - and leave headroom.

The rule of thumb: the saved session should contain the user's ANSWERS
and nothing else. Everything the script fetched to display those answers
belongs in a re-fetch on resume.
```

**Why it works:** The ceiling is fixed, so the only lever is what you put under
it. Separating "what the user told us" from "what we showed the user" typically
cuts the payload by an order of magnitude and makes resume faster as a side
effect.

---

## Example 4: Save Configuration Lives On The Parent OmniScript

**Context:** An OmniScript composed of embedded child OmniScripts, one per
product line. Save is configured on the child that the team was working in.
Nothing persists.

**Problem:** Save configuration must be defined on the **Parent** OmniScript.
Configuring it on an embedded child is a no-op that produces no error — the
designer accepts it, and the behaviour is simply absent.

**Solution:**

```text
Composition:
    Parent  Onboarding_Main            <- save configuration HERE
      ├── Child  Onboarding_Identity     isOmniScriptEmbeddable = true
      ├── Child  Onboarding_Financials   isOmniScriptEmbeddable = true
      └── Child  Onboarding_Consent      isOmniScriptEmbeddable = true

The relevant metadata flag on an embeddable child:
    isOmniScriptEmbeddable   "Indicates whether the OmniScript can be
                              embedded in other OmniScripts. Default: false."
```

**Why it works:** The parent owns the session because the parent owns the
composite data JSON. Once that is stated, the configuration location stops
being arbitrary.

---

## Example 5: Two Users, One Session — Not Supported

**Context:** A broker portal where a supervisor is expected to pick up an
application a junior started.

**Problem:** Editing and saving the same session by multiple Community users is
not supported. If a second user edits and saves a session created by another
user, data inconsistencies or save errors can occur when the original user
resumes.

Note what this is *not*: it is not a locking mechanism that blocks the second
user. The second save appears to work. The damage surfaces later, when the
original user resumes.

**Solution — model the handoff explicitly rather than sharing a session:**

```text
WRONG:
    both users open the same saved session, edit, save.

RIGHT:
    1. Junior completes their portion and submits it to a record you own
       (Application__c), ending their session.
    2. Supervisor starts a NEW OmniScript instance pre-populated from
       Application__c.
    3. Ownership of the record moves; sessions do not.

If genuine concurrent editing is required, native Save for Later is not
the mechanism. Use a custom session object with a version field and an
explicit conflict branch.
```

**Concurrency on a custom object, if you go that way:**

```text
Application_Session__c
    Version__c        Number      incremented on every save
    LastSavedBy__c    Lookup(User)
    LastSavedAt__c    DateTime

On save:  compare the in-memory Version__c to the stored value.
          Match    -> write, increment.
          Mismatch -> route to a "this session changed elsewhere" step.
                      Never silently overwrite.
```

**Why it works:** It replaces an unsupported behaviour with a modelled one, and
it makes the handoff visible in data (who owns the application now) rather than
implicit in who happened to save last.

---

## Example 6: Session State Is Not Platform Cache

**Context:** A team reaches for `Cache.Session` to hold OmniScript answers
between steps because it is fast and requires no data model.

**Problem:** Platform Cache session cache is the wrong shape for this in four
independent ways:

| Constraint | Consequence for session state |
|---|---|
| Maximum TTL **28,800 s (8 hours)** | no multi-day resume |
| "Expires when its specified time-to-live value is reached **or when the user session expires, whichever comes first**" | logout destroys it |
| "Cache isn't persisted. There's no guarantee against data loss." | eviction is normal operation |
| "Data in the cache isn't encrypted." | PII sits in plaintext |
| Maximum single cached item **100 KB** | a long script's answers may not fit |

**Solution:** Use the right store for the requirement.

| Requirement | Store |
|---|---|
| Survive a page refresh within one session | native Save for Later, or a custom object |
| Survive a logout / device change | a custom object. Not cache. |
| Multi-day resume with retention control | a custom object with an explicit expiry field and a purge job |
| Very high volume, long retention, narrow query shapes | Big Object — design the index before you need to query |
| Speed up a *read* the script performs repeatedly | Platform Cache, via a cacheable Integration Procedure |

**Why it works:** Cache is an accelerator for reads. Session state is durable
storage of user input. The only overlap is that both are "temporary," and that
word is doing far too much work.

---

## Example 7: What The Resume Link May Carry

**Context:** A tokenized resume link emailed to an applicant.

**Solution:**

```text
The URL carries an OPAQUE, SHORT-LIVED token and nothing else.

  Never in the URL:
    - answers, in any encoding (base64 is not an encoding for this purpose,
      it is a rename)
    - PII of any kind
    - a raw session record Id
    - anything that is still valid tomorrow

  In the URL:
    - a random token that indexes a server-side row

  On the server:
    - store a HASH of the token, not the token
    - bind the token to the subject it was issued for
    - expire in hours, not days; long-term resume requires re-authentication
    - single-use where the flow allows it

  On the resume page:
    - set a referrer policy. Any outbound link on that page can otherwise
      leak the token in the Referer header.
```

**Guest flows specifically:** Experience Cloud session lifetime and OmniScript
session lifetime are independent. The platform can log the user out while the
script still believes it has a session, so the resume path must detect the need
to re-authenticate rather than assuming identity.

**Why it works:** The token is a capability, not data. Everything that makes a
capability safe — short life, hashed at rest, bound to a subject, revocable —
is available; nothing about putting state in the URL is.

---

## Anti-Pattern: Guest Save-For-Later As A Second, Unmanaged PII Store

**What practitioners do:** enable native Save for Later on a public Experience
Cloud application so anonymous visitors can come back later. It is a
configuration checkbox and it looks free.

**What goes wrong:** the session blob now holds exactly the personal data that
the intake purge job was written to destroy — in `OmniScriptSavedSession`, an
object you cannot delete from through supported DML. The purge job deletes the
application rows and reports success. The same data survives in a second store
nobody put in the retention register, indefinitely, associated with an
unauthenticated visitor whose identity you cannot verify on resume.

Version churn makes it worse: every deactivate/reactivate cycle orphans another
generation of saved instances, which "remain stored in the system."

**Correct approach:** turn native session persistence **off** for guest flows.
If save-and-resume is genuinely required for an unauthenticated audience,
persist to a custom object with an explicit expiry field, encrypt the sensitive
fields, keep resume credentials server-side as a hashed token, and purge in the
**same scheduled job** that purges the intake row — so the two can never drift
apart.
