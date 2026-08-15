---
name: omniscript-session-state
description: "Use when an OmniScript must persist mid-flow state across refresh, navigation, multi-device resume, or abandonment recovery. Covers session objects, staging data, OmniScript tracking, and resume URLs. NOT for OmniScript UI step layout — use omnistudio/omniscript-design-patterns. NOT for general Flow pause/resume — use flow/pause-elements-and-wait-events."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Security
triggers:
  - "omniscript save and resume"
  - "persist omniscript state refresh"
  - "resume omniscript multi device"
  - "abandoned cart omniscript"
  - "omniscript tracking session object"
  - "omniscript save for later not working"
tags:
  - omnistudio
  - omniscript
  - session
  - resume
  - state
inputs:
  - OmniScript that requires persistence
  - Abandonment tolerance
  - Cross-device resume requirement
outputs:
  - Session object model
  - Save/resume trigger design
  - Resume URL strategy
  - Expiry + cleanup plan
dependencies: []
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# OmniScript Session State

Long-running OmniScripts — onboarding, quote configuration, compliance
questionnaires, benefits applications — lose users when a refresh wipes
progress. OmniStudio ships native Save for Later, and most teams either
under-use it (rebuilding a session store that was not needed) or over-use it
(putting regulated PII into a store they cannot lawfully delete from). This
skill covers the one constraint that decides between those, plus the four
platform behaviours that make save-and-resume fail in production after passing
in test.

---

## The Decision That Determines Everything Else

> **Can you delete this state on your own schedule?**

`OmniScriptSavedSession` is a real standard object — present in the object
reference from API 51.0 through 67.0 — and it is marked:

> "This object and associated records are only for internal use. Don't perform
> any create, edit, or delete operations on this object."

So native Save for Later is a store you can populate but cannot lawfully
manage. This sits in the object reference rather than in the Save for Later
documentation, which is why teams find it during an audit rather than during
design.

| Situation | Store |
|---|---|
| Retention obligation, cross-session queries, or a guest audience | a custom object you own |
| Authenticated, low sensitivity, "let the user come back" | native Save for Later — a configuration, not a project |

Building a custom store for the second case is over-engineering. Using the
native store for the first case is an audit finding.

---

## Four Behaviours That Fail Only In Production

These come from *OmniScript Save for Later — Considerations and Limitations*
(see the sourcing caveat in `references/well-architected.md`).

**1. Saved sessions are bound to the OmniScript version.** Sessions are tied to
the definition version active when they were created. Deactivate and reactivate
an OmniScript and previously saved sessions do not resume as the same instance —
a new instance is created, and older saved instances *remain stored in the
system*. A routine defect fix is therefore a data-loss event for every in-flight
user, plus a permanent addition to a store you cannot purge. Treat any
activation change with in-flight sessions as a migration.

**2. Save fails above 4,194,304 characters (4 MB)** — and the network payload is
significantly larger than the visible Data JSON, so inspecting the debug panel
understates it. The failure signature is characteristic: fine in test, fine
through step 4, intermittent at step 8, consistently failing at step 11, for the
users with the most entered data.

**3. Save configuration must be on the parent OmniScript.** In an embedded
composition (`isOmniScriptEmbeddable` = true on the children), configuring save
on a child is a silent no-op. The designer accepts it; nothing persists.

**4. Two users on one session is unsupported — and not blocked.** Editing and
saving the same session by multiple Community users is not supported; a second
user's save can cause data inconsistencies or save errors when the original user
resumes. The second save *is accepted*, so the damage surfaces later, to a
different user, and gets diagnosed as flakiness.

---

## Keep The Payload To The Answers

The 4 MB ceiling is fixed, so the only lever is what goes under it.

| Category | Treatment |
|---|---|
| The user's answers | persist |
| Lookup data — catalogs, code tables, picklist option sets | **re-fetch on resume** from a cacheable Integration Procedure |
| File content | store the document, keep an id |
| Derived values recomputable from answers | prune |

Typical reduction is an order of magnitude, and resume gets faster as a side
effect. Measure the real request payload at the **last** step, not the Data JSON
at a middle step.

---

## Platform Cache Is Not A Session Store

"Session state" and "session cache" share a word, and the word is doing far too
much work. Session cache's documented properties disqualify it for user input:

| Property | Consequence |
|---|---|
| Max TTL 28,800 s (8 hours) | no multi-day resume |
| Expires at TTL *or when the user session expires, whichever comes first* | logout destroys it |
| "Cache isn't persisted. There's no guarantee against data loss." | eviction is normal operation |
| "Data in the cache isn't encrypted." | PII in plaintext |
| Max single cached item 100 KB | long scripts may not fit |

Cache accelerates *reads the script performs*. It does not hold *what the user
typed*.

---

## Custom Session Object Shape

When you own the store, the schema decision that matters is which fields you
encrypt — because Shield encryption restricts SOQL filtering.

```text
Application_Session__c
    Answers_JSON__c    Long Text Area   ENCRYPTED    <- the payload
    SSN_Token__c       Text             tokenized, not the value
    ExpiresAt__c       DateTime         PLAINTEXT    <- the purge filters here
    Status__c          Picklist         PLAINTEXT    <- and here
    Version__c         Number           concurrency detection
    LastSavedAt__c     DateTime
```

The fields you **filter on** are never the fields you **encrypt**. The purge job
then deletes rows whose sensitive contents it never has to read.

On save, compare the in-memory `Version__c` to the stored value: match → write
and increment; mismatch → route to an explicit conflict branch. Never silently
overwrite.

---

## Resume Links Carry A Capability, Not Data

```text
In the URL      : an opaque random token indexing a server-side row
Never in the URL: answers in any encoding; PII; a raw session record Id;
                  anything still valid tomorrow
On the server   : store a HASH of the token, bound to its subject,
                  expiring in hours not days, single-use where the flow allows
On the page     : set a referrer policy — any outbound link can otherwise
                  leak the token in the Referer header
```

Base64 is a rename, not an encryption. And Experience Cloud session lifetime and
OmniScript session lifetime are independent: the platform can log a user out
while the script still believes it has a session, so the resume path must
*verify* identity rather than assume it.

---

## Recommended Workflow

1. Answer the deciding question first: does a retention obligation, a
   cross-session query, or a guest audience attach to this state? If yes, you
   need a custom object — native Save for Later cannot be lawfully purged.
2. Define the state schema as *the user's answers only*. Everything the script
   fetched to display those answers is a re-fetch on resume, not a persisted
   value. Measure the request payload at the final step against the 4 MB
   ceiling.
3. Configure save on the **parent** OmniScript and at **step boundaries** — not
   on a child, and not on input change. Each save posts the whole payload.
4. Design the resume path: opaque token in the URL, hash stored server-side,
   short expiry, referrer policy on the page, explicit re-authentication branch
   for Experience Cloud and guest flows.
5. Model concurrency explicitly. Handoff between users is a record-ownership
   change, not a shared session. If concurrent editing is genuinely required,
   use a custom object with a `Version__c` field and a conflict branch.
6. Set retention as a compliance decision confirmed with the data owner, and
   give the object a plaintext `ExpiresAt__c` plus a scheduled purge that
   references it. For guest flows, purge session state in the **same** job as
   the intake row so the two cannot drift.
7. Plan every OmniScript activation change as a migration when in-flight
   sessions exist: count them, decide whether the change can wait, notify users
   before the deploy, and record orphaned-instance growth as a retention risk.

---

## Review Checklist

- [ ] No DML anywhere against `OmniScriptSavedSession`
- [ ] Retention obligation, if any, attaches to a store you can delete from
- [ ] Saved payload contains answers only — no catalogs, no file content
- [ ] Request payload measured at the **last** step, with headroom under 4 MB
- [ ] Save configured on the **parent** OmniScript
- [ ] Save fires at step boundaries, not on input change
- [ ] Resume URL carries an opaque token only; hash stored server-side
- [ ] Referrer policy set on the resume page
- [ ] Re-authentication branch handled for Experience Cloud and guest flows
- [ ] Handoff modelled as record ownership, not a shared session
- [ ] `Version__c` comparison with an explicit conflict branch
- [ ] Plaintext `ExpiresAt__c` / `Status__c`; encryption only on payload fields
- [ ] Scheduled purge exists and references the expiry field
- [ ] Guest flows: native persistence off, or purged in the same job as intake
- [ ] Activation changes planned as migrations when sessions are in flight

---

## Worked Examples (see `references/examples.md`)

- *Native vs custom* — the comparison table that decides it
- *`OmniScriptSavedSession` is internal use only* — the compliance consequence
- *Version binding* — why a routine fix loses everyone's progress
- *The 4 MB ceiling* — what to persist and what to re-fetch
- *Save config on the parent* — the silent no-op
- *Two users, one session* — modelling handoff instead
- *Session state is not Platform Cache* — the store-selection table
- *What the resume link may carry* — token design

## Common Gotchas (see `references/gotchas.md`)

- `OmniScriptSavedSession` is marked internal use only
- Deactivate/reactivate orphans every saved session, permanently
- The network payload is bigger than the Data JSON you inspected
- Save config on a child OmniScript is a silent no-op
- Multi-user editing is unsupported *and not blocked*
- Shield encryption changes what the purge job can filter on
- Experience Cloud and OmniScript session lifetimes are independent

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- A purge job against `OmniScriptSavedSession`
- Answers serialised into the resume URL
- Platform Cache as the session store
- Saving on every keystroke
- A session object with no expiry field
- Silent last-write-wins
- Ignoring version binding on deploy
- Persisting lookup data with the session

---

## Related

- **omnistudio/omniscript-design-patterns** — step layout and element design.
  This skill starts where that one ends.
- **omnistudio/omniscript-versioning** — the activation model whose interaction
  with saved sessions is documented above.
- **omnistudio/integration-procedure-cacheable-patterns** — the cacheable read
  path that lets you re-fetch lookup data on resume instead of persisting it.
- **omnistudio/omnistudio-security** — guest exposure, `requiredPermission`, and
  the wider Experience Cloud posture.

## Official Sources Used

See `references/well-architected.md` for the full source list, including an
explicit caveat about which Save for Later facts could not be fetched directly.
