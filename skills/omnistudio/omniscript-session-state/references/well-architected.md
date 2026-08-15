# Well-Architected Notes — OmniScript Session State

## Relevant Pillars

- **Resilient** — session loss is the top complaint on any long OmniScript, and
  the most common cause is not a bug but a version activation nobody treated as
  a migration event.
- **User Experience** — seamless resume beats "start over," and the gap is
  widest for exactly the users you least want to lose: the ones deep in a long
  application with a lot of entered data.
- **Trusted** — mid-flight state is a PII store. Whether it is one you can
  lawfully delete from decides the whole design, and it is decided by a fact in
  the object reference rather than in the feature documentation.
- **Secure** — resume credentials are capabilities. Everything that makes a
  capability safe (short life, hashed at rest, bound to a subject, revocable) is
  available; nothing about carrying state in a URL is.

## The Decision That Determines Everything Else

> Can you delete this state on your own schedule?

`OmniScriptSavedSession` is marked "for internal use only" with an explicit
instruction not to perform create, edit, or delete operations. So native Save
for Later is a store you can populate but cannot lawfully manage. That single
constraint decides native-vs-custom for most regulated flows, and it sits in the
object reference rather than in the Save for Later documentation — which is why
teams discover it during an audit rather than during design.

- **Retention obligation, cross-session queries, or a guest audience** → a
  custom object you own.
- **Authenticated, low-sensitivity, "let the user come back"** → native Save for
  Later is a configuration rather than a project, and building a custom store is
  over-engineering.

## Architectural Tradeoffs

- **Native Save for Later vs a custom session object.** Native is a
  configuration; custom is a data model plus save logic, resume logic, and a
  purge job. Native binds sessions to the OmniScript version and cannot survive
  a deactivate/reactivate cycle; custom survives version changes and gives you
  encryption, query shapes, and deletion. The build cost is real; so is the
  audit exposure of the alternative.
- **Short expiry vs user convenience.** Short expiry reduces the window of
  exposure and increases abandonment. Tier by data sensitivity, and treat the
  tier as a compliance decision confirmed with the data owner rather than a
  developer's default.
- **Big Object vs custom object.** Big Objects handle volume and long retention
  but fix query shapes to the index, which must be designed before the store is
  chosen. A custom object is usually right even at higher volume if any required
  query — purge by expiry, lookup by subject, resume by token hash — does not
  fit the index.
- **Encrypting the payload vs querying it.** Shield encryption restricts SOQL
  filtering, so the schema must separate operational metadata (`ExpiresAt`,
  `Status`, `Version`, `OwnerId`) from encrypted payload fields. The purge then
  filters on plaintext and deletes rows whose contents it never reads.
- **Save cadence.** Step boundaries by default. Each save posts the entire
  payload against a 4 MB ceiling, so a per-keystroke cadence is simultaneously
  the most expensive and least useful option. Mid-step debounced saves need a
  justification, not a preference.
- **Persisting fetched data vs re-fetching on resume.** Persisting is simpler
  and grows the payload monotonically toward the ceiling. Re-fetching from a
  cacheable Integration Procedure keeps the session small and usually makes
  resume faster. Persist answers; re-fetch everything shown to the user.

## Hygiene

- Never DML `OmniScriptSavedSession`.
- Any OmniScript activation change is planned as a migration when in-flight
  sessions exist.
- The request payload is measured at the **last** step of the script, not the
  Data JSON at a middle step.
- Save configuration lives on the **parent** OmniScript in an embedded
  composition.
- Handoff between users is a record-ownership change, never a shared session.
- Resume URLs carry an opaque token only; the server stores its hash; the resume
  page sets a referrer policy.
- Guest flows have native session persistence off, or a custom store purged in
  the same job as the intake row.
- Every session object has a plaintext expiry field and a scheduled job that
  references it.

## Official Sources Used

- **OmniScriptSavedSession — Object Reference for the Salesforce Platform (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omniscriptsavedsession.htm
  — source for the load-bearing constraint in this skill: the object is present
  from API 51.0 through 67.0 and is marked "This object and associated records
  are only for internal use. Don't perform any create, edit, or delete
  operations on this object," with the added warning that "modifying or deleting
  this object's records may result in errors with your implementation."
  Verified 2026-08-14.
- **OmniScript — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniscript.htm
  — source for `isActive` (default false), `versionNumber`, `uniqueName`
  ("Type_SubType_Language_VersionNumber"), `omniProcessKey` ("Type_SubType"),
  `isOmniScriptEmbeddable` ("Indicates whether the OmniScript can be embedded in
  other OmniScripts. Default: false."), `requiredPermission`,
  `responseCacheType`, `isMetadataCacheDisabled`, and `propertySetConfig`.
  Verified 2026-08-14.
- **Platform Cache Limits — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_limits.htm
  — source for session cache TTL minimum 300 s and maximum 28,800 s (8 hours),
  maximum size of a single cached item 100 KB, and maximum key size 50
  characters. Verified 2026-08-14.
- **Platform Cache Considerations — Apex Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_platform_cache_limitations.htm
  — source for "Cache isn't persisted. There's no guarantee against data loss.",
  "Data in the cache isn't encrypted.", and the statement that session cache
  expires at its TTL or when the user session expires, whichever comes first.
  Verified 2026-08-14.
- **Cache.Partition class — Apex Reference Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_cache_Partition.htm
  — source for the alphanumeric-only cache key constraint cited in
  `llm-anti-patterns.md` §3. Verified 2026-08-14.

### Save for Later behaviour — sourcing caveat

Four behavioural facts used throughout this package come from the Salesforce
Help knowledge article **"OmniScript Save for Later — Considerations and
Limitations"** (`help.salesforce.com/s/articleView?id=000394956`):

1. Saved sessions are tied to the OmniScript definition version that was active
   when the session was created; deactivating and reactivating an OmniScript
   means previously saved sessions do not resume as the same instance — a new
   instance is created and older saved instances remain stored in the system.
2. Save configuration must be defined on the **Parent** OmniScript.
3. Save for Later fails if the total request payload exceeds **4,194,304
   characters (4 MB)**, and the network payload can be significantly larger than
   the visible Data JSON.
4. Editing and saving the same session by multiple Community users is not
   supported; a second user's save can cause data inconsistencies or save errors
   when the original user resumes.

**These were obtained from search-engine extracts of that article, corroborated
across two independent queries, but not from a direct read.**
`help.salesforce.com` renders no article text to a document fetcher — the page
returns only a loading shell — so the article could not be fetched and quoted
directly. The four facts are consistent across both extracts and are internally
consistent with the version-identity model documented in the `OmniScript`
metadata reference, which is why they are stated here. Confirm the 4 MB figure
and the parent-configuration rule against the article before quoting either
number to a customer.

Salesforce Help also publishes parallel "(Managed Package)" variants of the Save
and Resume articles (`os_save_and_resume_an_omniscript` vs
`xcloud.os_save_and_resume_an_omniscript`), so verify which runtime an article
describes before applying it. No claim in this package is sourced from a
managed-package-specific article.
