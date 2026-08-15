# OmniScript Session State — Gotchas

Behaviour that loses a user's work, creates an unmanageable PII store, or fails
only for the users who most need the feature.

Save for Later behaviour below is from the Salesforce Help article *OmniScript
Save for Later — Considerations and Limitations* (article 000394956); see the
sourcing caveat in `references/well-architected.md`. Metadata field names are
from the `OmniScript` metadata type at API 67.0.

---

## 1. `OmniScriptSavedSession` Is Marked Internal Use Only

**What happens:** A retention or cleanup job that DMLs saved sessions is
designed, built, and shipped. It may work today.

**When it occurs:** `OmniScriptSavedSession` is a real standard object in the
object reference from API 51.0 through 67.0, and it carries the standard
internal-use marking:

> "This object and associated records are only for internal use. Don't perform
> any create, edit, or delete operations on this object."
>
> "Modifying or deleting this object's records may result in errors with your
> implementation."

**How to avoid:** Never make it the store of record for anything you have a
legal or contractual obligation to delete. If a retention requirement attaches
to the state, the state belongs in an object you own. Read the saved-session
object if you need an inventory or a count; do not write to it.

This is the single fact that decides native-vs-custom for most regulated flows,
and it is not where people look — it is in the object reference, not in the
Save for Later documentation.

---

## 2. Deactivating And Reactivating An OmniScript Orphans Every Saved Session

**What happens:** Users with saved progress resume into a blank script. No
error tells them why.

**When it occurs:** Saved sessions are tied to the OmniScript definition version
that was active when the session was created. If an OmniScript is deactivated
and reactivated, previously saved sessions do not resume as the same instance —
a new OmniScript instance is created, and the older saved instances **remain
stored in the system**.

So a routine defect fix that goes out as deactivate → new version → reactivate
is a data-loss event for every in-flight user, plus a permanent addition to a
store you cannot purge.

**How to avoid:** Treat any activation change on an OmniScript with in-flight
sessions as a migration:

- Count in-flight sessions and decide whether the change can wait for the tail
  to drain.
- Notify affected users before the deploy, not after they find an empty form.
- If state must survive version changes, mirror the answers into a custom
  object at each step boundary and resume from there. The native saved session
  cannot do this.
- Track orphaned-instance growth in the retention risk register.

---

## 3. Save For Later Fails Above 4 MB — And The Payload Is Bigger Than The Data JSON

**What happens:** Save works in testing and fails in production, later in the
script, for the users with the most entered data.

**When it occurs:** Save for Later fails if the total request payload exceeds
**4,194,304 characters (4 MB)**. The network payload can be significantly
larger than the visible Data JSON, so inspecting the Data JSON in the debug
panel understates the real figure.

The progression is characteristic: fine through step 4, intermittent at step 8,
consistently failing at step 11 — because the payload grows monotonically.

**How to avoid:** Keep the saved payload to the user's *answers*.

- Lookup data (product catalogs, code tables, picklist option sets) is
  re-fetched on resume from a cacheable Integration Procedure, not persisted.
- File content is stored as a document; the session keeps an id.
- Derived values recomputable from the answers are pruned.
- Measure the real request payload at the **last** step, not the Data JSON at a
  middle step, and leave headroom.

---

## 4. Save Configuration Must Be On The Parent OmniScript

**What happens:** Save is configured, the designer accepts it, and nothing
persists. No error.

**When it occurs:** Save configuration must be defined on the **Parent**
OmniScript. In a composition of embedded child OmniScripts
(`isOmniScriptEmbeddable` = true), configuring save on a child is a silent
no-op.

**How to avoid:** Configure on the parent, which owns the composite data JSON.
When debugging "save does nothing," check the configuration's location before
checking its content.

---

## 5. Two Users On One Session Is Not Supported — And Does Not Block

**What happens:** A supervisor picks up a session a colleague started. Both
saves appear to succeed. The original user resumes into inconsistent data, or
gets a save error.

**When it occurs:** Editing and saving the same session by multiple Community
users is not supported. If a second user edits and saves a session created by
another user, data inconsistencies or save errors can occur when the original
user resumes.

The dangerous property is that this is **not** enforced as a lock. The second
save is accepted. The failure surfaces later, to a different user, in a
different session — which is why it is diagnosed as flakiness rather than as a
design error.

**How to avoid:** Model handoff as a record-ownership change, not a shared
session: the first user submits to a record you own and ends their session; the
second starts a new instance pre-populated from that record. If genuine
concurrent editing is required, native Save for Later is the wrong mechanism —
use a custom object with a `Version__c` field, compare on save, and route a
mismatch to an explicit conflict branch. Never silently overwrite.

---

## 6. Platform Cache Is Not A Session Store

**What happens:** Answers held in `Cache.Session` disappear at logout, at
session timeout, after 8 hours, or under memory pressure.

**When it occurs:** Session cache is an accelerator, not storage. Its documented
properties make it unfit for user input:

- Maximum TTL **28,800 s (8 hours)**.
- "Expires when its specified time-to-live value is reached or when the user
  session expires, whichever comes first."
- "Cache isn't persisted. There's no guarantee against data loss."
- "Data in the cache isn't encrypted."
- Maximum size of a single cached item is **100 KB**.

**How to avoid:** Use cache to speed up *reads* the script performs repeatedly;
use a custom object (or native Save for Later) to hold *what the user typed*.
The two are conflated because both get called "temporary," which is the least
informative word available.

---

## 7. Shield Encryption Changes What You Can Query

**What happens:** A session-purge job filters on an encrypted field and either
fails or silently matches nothing.

**When it occurs:** Encrypting a custom session object's PII fields is correct,
but encrypted fields have restricted behaviour in SOQL filters, sorting, and
some index usage.

**How to avoid:** Design the schema so the fields you *filter on* — `ExpiresAt`,
`Status`, `OwnerId`, `Version` — are never the fields you encrypt. Encrypt the
payload fields. The purge job then filters on plaintext operational metadata and
deletes rows whose sensitive content it never has to read.

---

## 8. Big Object Query Shapes Are Fixed By The Index

**What happens:** A Big Object chosen for volume turns out not to support the
query the purge or reporting job needs.

**When it occurs:** Big Objects restrict filtering to the defined index, and the
index is not something you evolve casually afterwards.

**How to avoid:** Design the index before choosing the store, from the queries
you know you will need: purge by expiry, lookup by subject, resume by token
hash. If any required query does not fit the index, a custom object is the
right answer even at higher volume.

---

## 9. Resume Tokens Leak Through The Referer Header

**What happens:** A resume token appears in a third party's web logs.

**When it occurs:** The resume page contains any outbound link. Following it can
send the current URL — token included — in the `Referer` header.

**How to avoid:** Set a referrer policy on the resume page. Better, make the
token single-use and short-lived so a leaked one is already spent. Best, do not
put anything in the URL that is still valid tomorrow.

---

## 10. Experience Cloud Session Lifetime And OmniScript Session Lifetime Are Independent

**What happens:** The platform logs the user out while the script still believes
it has a session. The next save or resume behaves unpredictably.

**When it occurs:** They are separate lifetimes with separate expiry. An
Experience Cloud session timeout does not notify the running OmniScript.

**How to avoid:** Design the resume path to *verify* identity rather than assume
it. On resume, re-establish who the user is before loading state, and handle the
re-authentication branch explicitly. For guest flows this is not optional —
there is no authenticated identity to fall back on, so the token is doing all of
the work.

---

## 11. Base64 Is Not Encryption, And URLs Are Not Storage

**What happens:** A team serialises the OmniScript data JSON to base64 and puts
it in the resume URL. Email clients clip the URL, browser history retains PII,
Experience Cloud access logs capture it, and any proxy in the path sees it.

**When it occurs:** The "stateless" instinct — avoid the server-side store by
carrying state in the link. It is a genuinely elegant pattern in other contexts
and completely wrong here.

**How to avoid:** The URL carries an opaque token that indexes a server-side
row. Nothing else. Store a hash of the token rather than the token. And note the
practical failure too: URLs have length limits that a serialised multi-step
application will exceed, so this design also breaks for exactly the long
sessions it was meant to serve.

---

## 12. Guest Save-For-Later Creates A Second PII Store Outside Your Purge

**What happens:** The intake purge job deletes application rows on schedule and
reports success. The same personal data persists in saved sessions
indefinitely.

**When it occurs:** Native Save for Later enabled on a public Experience Cloud
OmniScript. The session blob holds the data the purge was written to destroy,
in an object you cannot delete from through supported DML (§1), growing an
extra orphaned generation on every version change (§2).

**How to avoid:** Turn native session persistence **off** for guest flows. If
save-and-resume is required for an unauthenticated audience: a custom object
with an explicit expiry field, encrypted payload fields, a hashed server-side
resume token, and purge in the **same scheduled job** as the intake row so the
two cannot drift.
