# Examples — Heroku ↔ Salesforce Integration

## Example 1 — "Heroku web app needs Account + Contact data with sub-second queries"

**Context.** A customer-facing portal hosted on Heroku needs to render
account dashboards. The dashboards do joins, aggregates, and full-text
search across ~500K accounts. Latency budget is 200 ms per render.

**Wrong instinct.** Heroku app calls the Salesforce REST API on every
render.

**Why it's wrong.** REST API has its own latency floor (100–300 ms per
call), shared per-org limits, and no query language as expressive as
SQL. The portal team would build a cache layer that drifts.

**Right answer.** **Heroku Connect** with bidirectional mappings on
Account and Contact. Sync target: a `salesforce` schema in Heroku
Postgres. Portal queries Postgres directly with sub-millisecond joins.
Eventual-consistency lag is acceptable for a dashboard.

```
Heroku Postgres  ←→  Heroku Connect  ←→  Salesforce
  (portal queries)    (managed sync)      (source of truth for some objects)
```

Plan tier: Enterprise (production volume). Integration user: dedicated,
`API Enabled` + `View All` + `Modify All`. All three regions co-located.

---

## Example 2 — "Salesforce admin wants to add a Heroku-hosted ML score to a Flow"

**Context.** Data-science team owns a Python service on Heroku that
scores customer churn. Sales-Ops wants the score field on the Account
record, surfaced to flow-builder admins so they can branch on it.

**Wrong instinct.** Build an Apex `@InvocableMethod` class that wraps
an HTTP callout to the Heroku endpoint.

**Why it's wrong-ish.** It works, but it adds an Apex maintenance
surface. New endpoint params require a new deployment. Auth is hand-rolled
via Named Credential.

**Right answer.** **Heroku AppLink.** Configure the AppLink add-on on
the Heroku app. The scoring API surfaces as a Flow-native action.
Sales-Ops wires it into the Account flow without writing Apex. Auth is
handled by AppLink.

---

## Example 3 — "Service agents want to see Heroku-side order history without copying"

**Context.** Heroku is the system-of-truth for orders (a custom Node
service). Service agents need order history visible on the Salesforce
Contact record but the team doesn't want to maintain a sync.

**Right answer.** **Heroku External Objects (Salesforce Connect with
oData).** The Heroku app exposes the orders table via the External
Objects oData endpoint; Salesforce Connect consumes it as an External
Object. Agents see the related list on the Contact page; data stays in
Postgres.

```
Salesforce Connect (oData consumer)  ←  Heroku External Objects (oData server)  ←  Postgres
                                                                                   (source)
```

Plan note: External Object queries cost no Salesforce data storage but
each query is a round trip to Heroku — be mindful of join performance.

---

## Example 4 — "Heroku service needs to react to Opportunity stage changes"

**Context.** When an opportunity reaches Closed-Won, a Heroku service
should kick off provisioning logic.

**Right answer.** **Salesforce Pub/Sub API** subscriber on the Heroku
side. The Heroku app subscribes to an Opportunity Change Data Capture
event (or a custom Platform Event published by Apex). At-least-once
delivery, replay window, no Apex callout governor in scope.

This is the Heroku equivalent of using Event Relay → EventBridge on
the AWS side; the Pub/Sub API is the same source for both targets.

---

## Example 5 — "Embed a Heroku-hosted dashboard inside the Lightning Service Console"

**Context.** Service-Ops wants a real-time call-center dashboard
(updates every 5 seconds) inside the Service Console — the dashboard
is already built and runs on Heroku.

**Right answer.** **Salesforce Canvas with Signed Request auth.**
Configure a Connected App that points at the Heroku app's Canvas URL.
Canvas posts a signed payload to Heroku containing the Salesforce user
context, OAuth token, and instance URL. Heroku app renders the
dashboard inside the Canvas iframe. No consent screen because the user
is already authenticated to Salesforce.

**Wrong instinct.** OAuth Web Server Flow forcing a consent screen
every time the agent opens the dashboard. That's the right model only
if the dashboard also runs standalone outside Salesforce.

---

## Anti-Pattern: Sharing one integration user across multiple Heroku Connect add-ons

```
add-on A  →  integration_user_X
add-on B  →  integration_user_X    ← wrong
add-on C  →  integration_user_X    ← wrong
```

**What goes wrong.** Salesforce caps concurrent queries at 10 *per user*
and active OAuth tokens at 5 *per user*. Three add-ons sharing one
integration user contend for those slots; sync lag spikes; large pulls
hit `REQUEST_LIMIT_EXCEEDED` errors that don't clearly name the cause.

**Correct.**

```
add-on A  →  integration_user_A
add-on B  →  integration_user_B
add-on C  →  integration_user_C
```

Each gets its own slice of the per-user budget.
