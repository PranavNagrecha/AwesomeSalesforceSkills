# Gotchas — Heroku ↔ Salesforce Integration

Non-obvious behaviors that cause real production problems when wiring
Heroku and Salesforce.

---

## Gotcha 1: Demo plan caps at 10,000 synced rows — silently

**What happens.** Heroku Connect demo plan has a hard 10K-row cap across
all mappings combined. Once you hit it, sync stops; the dashboard shows
the cap was reached but no error fires up into the Heroku app or
Salesforce.

**When it occurs.** A POC works fine, then production data lands and
sync goes quiet. Hours later the team notices Postgres is stale.

**How to avoid.** Demo plan is for POC only. Procure Enterprise / Shield
*before* going to production. Document the row-count budget as part of
the deployment runbook. (Source: [Heroku Connect docs](https://devcenter.heroku.com/articles/heroku-connect))

---

## Gotcha 2: One Salesforce integration user per Heroku Connect add-on

**What happens.** Salesforce caps concurrent queries at 10 *per user*
and active OAuth tokens at 5 *per user*. Multiple Connect add-ons
sharing one integration user contend for those caps; sync lag spikes
unpredictably; large pulls fail with `REQUEST_LIMIT_EXCEEDED` that
doesn't name the cause.

**When it occurs.** Teams treating "the Heroku integration user" as a
shared identity across multiple Heroku apps.

**How to avoid.** Provision a dedicated integration user per add-on.
Name them explicitly (`heroku_connect_app_a`, `heroku_connect_app_b`).
Document the rotation cadence.

---

## Gotcha 3: Re-authenticating Connect to a different Salesforce org is not supported

**What happens.** Sandbox refresh, org migration, or moving from full
sandbox to production — you cannot just re-point an existing Connect
add-on at a new org. The OAuth tie is bound at provision time.

**When it occurs.** Discovered during environment cutover, often on a
deadline.

**How to avoid.** Recreate the Connect connection from scratch when the
target org changes. Plan for the re-mapping cost (usually a day of
configuration work) in the cutover runbook. (Source:
[Heroku Connect docs](https://devcenter.heroku.com/articles/heroku-connect))

---

## Gotcha 4: Heroku Postgres connection pooling breaks Connect

**What happens.** A Heroku app dyno using a connection-pooler add-on
(PgBouncer-style) on top of the same Postgres database that Heroku
Connect attached to — Connect's trigger-based writes get lost or
duplicated because the pooler doesn't carry transaction state through
correctly.

**When it occurs.** Adding a connection pooler to "speed up" the
dyno-to-database path on a Connect-enabled database.

**How to avoid.** Use direct Postgres connections from your dynos when
the database has Connect attached. If the dyno truly needs pooling,
isolate the pooler on a *different* database (read replica or sharded
tables that Connect doesn't manage).

---

## Gotcha 5: `OPERATION_TOO_LARGE` on Connect's pulls without `View All` permission

**What happens.** Heroku Connect's polling queries against Salesforce
fail intermittently with `OPERATION_TOO_LARGE`. The error doesn't name
a missing permission — it looks like a query-shape problem.

**When it occurs.** Integration user has `API Enabled` and standard
object permissions but is missing `View All` on the synced objects.
Salesforce uses a slower query path without `View All`, which exceeds
internal size limits on large pulls.

**How to avoid.** Grant `View All` (and `Modify All` for write paths)
on every object the Connect add-on syncs. Document this in the
integration-user provisioning checklist. (Source: [Heroku Connect docs](https://devcenter.heroku.com/articles/heroku-connect))

---

## Gotcha 6: Canvas Signed Request and OAuth Web Server Flow are not interchangeable

**What happens.** A Canvas app configured for Signed Request auth is
hand-modified to add an OAuth dance "for safety". The user opens the
Canvas app inside Salesforce, gets the signed payload AND a separate
consent prompt for OAuth. The two auth flows produce different access
tokens with different scopes — the app gets confused about which one
to use.

**When it occurs.** Refactor where someone adds OAuth thinking it
hardens the auth model.

**How to avoid.** Pick one. Embedded-only Canvas app → Signed Request
(default, no consent screen, simpler). App that runs both inside and
outside Canvas → OAuth Web Server Flow throughout (the standalone app
already needs it; reuse it inside Canvas via session bridging, not
double-auth). (Source: [Canvas Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.platform_connect.meta/platform_connect/canvas_app_authentication.htm))

---

## Gotcha 7: Connect cannot be added to review apps via `app.json`

**What happens.** A Heroku review-app workflow (PR-driven preview apps)
has `Heroku Connect` listed as an add-on in `app.json`. Review apps
fail to provision because Connect can't be auto-attached this way.

**When it occurs.** Adopting review apps in a CI pipeline that already
has Connect on the main app.

**How to avoid.** Provision Connect manually per-app. For PR previews,
use a smaller alternative (Postgres-only, populate via REST or fixture
data) — review apps aren't the place for full Connect sync anyway.

---

## Gotcha 8: Region mismatch multiplies Connect sync lag

**What happens.** Heroku Postgres in `us-east-1`, Connect add-on in
`eu-west-1`, Salesforce org on a US instance — sync lag is 2–3× what
the team expected based on the polling cadence alone.

**When it occurs.** Regions chosen independently per service without
co-location intent.

**How to avoid.** Pick one region and pin all three (Postgres, Connect,
Salesforce instance) to it. The primary latency lever for Connect is
co-location, not polling cadence.
