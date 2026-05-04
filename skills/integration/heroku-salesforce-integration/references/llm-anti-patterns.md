# LLM Anti-Patterns — Heroku ↔ Salesforce Integration

Mistakes AI coding assistants commonly make when advising on Heroku
↔ Salesforce integration. The consuming agent should self-check against
this list before recommending a path.

---

## Anti-Pattern 1: Recommending REST API polling when Heroku Connect would have synced

**What the LLM generates.** "Write a Heroku worker that queries the
Salesforce REST API every 5 minutes and updates the local Postgres
copy."

**Why it happens.** REST API polling is the most-documented
"Salesforce client" pattern across general Salesforce training data;
Heroku Connect is platform-specific and underrepresented.

**Correct pattern.** Heroku Connect is the managed equivalent. It
handles polling, trigger-based writes back to Salesforce, OAuth
refresh, and retry — all of which the hand-rolled worker has to
reinvent. Prefer Connect for any "keep a Postgres copy of these
Salesforce objects" use case.

**Detection hint.** Any "every N minutes, query Salesforce and upsert
to Postgres" pseudocode in a Heroku context is suspect.

---

## Anti-Pattern 2: Recommending Apex `@InvocableMethod` + HTTP callout when Heroku AppLink fits

**What the LLM generates.** "Create an Apex class with an
`@InvocableMethod` annotation that issues a callout to your Heroku
endpoint via Named Credential. Then surface it in Flow Builder."

**Why it happens.** Apex callouts are a 2018-era pattern; AppLink (2024+)
is newer and underrepresented in training data.

**Correct pattern.** **Heroku AppLink** exposes the Heroku API as a
first-class Salesforce action without writing the Apex wrapper. New
endpoint params don't require a code deploy.

**Detection hint.** Any "Apex callout to Heroku, then expose via
Invocable" recipe is the long way around when AppLink is available.

---

## Anti-Pattern 3: Recommending Heroku Connect demo plan for production volumes

**What the LLM generates.** Setup steps for Heroku Connect that
default to the demo plan, with no warning about the row cap.

**Why it happens.** Tutorial / quickstart docs use the demo plan;
the LLM doesn't transfer "demo plan = POC only" to a production
recommendation.

**Correct pattern.** Recommend Enterprise / Shield for any production
deployment. Note the demo plan's 10K-row cap and 10-minute polling
floor explicitly. Plan the upgrade before launch.

**Detection hint.** Any production design with "Heroku Connect" and
no plan-tier discussion is incomplete.

---

## Anti-Pattern 4: Recommending one integration user across multiple Connect add-ons

**What the LLM generates.** "Create a Salesforce user named
`heroku_integration` and use it for all your Heroku Connect add-ons."

**Why it happens.** Reusing identities is the simpler answer in most
contexts. Salesforce's per-user concurrent-query and OAuth-token caps
are documented but not on the LLM's salient path.

**Correct pattern.** One dedicated integration user per add-on.
Permissions: `API Enabled` + `View All` + `Modify All` (only on the
synced objects).

**Detection hint.** Any "single shared integration user" recommendation
across multiple Heroku apps is wrong.

---

## Anti-Pattern 5: Confusing Salesforce Canvas Signed Request with OAuth Web Server Flow

**What the LLM generates.** A Canvas integration recipe that includes
both the Signed Request setup AND a separate OAuth dance.

**Why it happens.** Both are valid Canvas auth options; the LLM
combines them assuming "more auth = more secure".

**Correct pattern.** Pick one based on whether the app also runs
outside the Canvas frame. Embedded-only → Signed Request. Hybrid
(embedded + standalone) → OAuth Web Server Flow throughout.

**Detection hint.** Any Canvas recipe with both "verify signed payload"
AND "redirect to OAuth consent screen" steps is double-auth and wrong.

---

## Anti-Pattern 6: Treating External Objects and Connect as interchangeable

**What the LLM generates.** "Use Heroku External Objects to keep your
Heroku data in sync with Salesforce."

**Why it happens.** Both surface Heroku data in Salesforce; the LLM
doesn't internalize that Connect *copies* data, External Objects
*virtualizes* it.

**Correct pattern.** External Objects: read-mostly, no copy, every
query is a round trip to Heroku. Connect: bidirectional sync, copy
into Salesforce storage, queries hit local indexes. The choice is
"copy and pay storage" vs "virtualize and pay per-query latency".

**Detection hint.** "External Objects to keep data in sync" is a
contradiction in terms — External Objects don't sync, they virtualize.

---

## Anti-Pattern 7: Recommending Heroku as a passthrough between two Salesforce orgs

**What the LLM generates.** "Heroku Connect to Postgres, then a Heroku
worker pushes to a second Salesforce org."

**Why it happens.** "Heroku is good at integration" is a general truth
that the LLM over-applies to org-to-org cases.

**Correct pattern.** Org-to-org integration should use Salesforce-native
paths: org-to-org REST API, Salesforce-to-Salesforce, or MuleSoft if
the topology is more complex. Heroku in the middle adds latency, a
second managed service, and a second integration user — without buying
anything.

**Detection hint.** Any architecture diagram with two Salesforce orgs
and Heroku in between is suspect. Question whether Heroku is genuinely
necessary or just middleware-by-habit.
