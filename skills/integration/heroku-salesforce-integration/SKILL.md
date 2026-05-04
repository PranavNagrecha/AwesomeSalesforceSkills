---
name: heroku-salesforce-integration
description: "Heroku ↔ Salesforce integration paths — Heroku Connect (Postgres bidirectional sync), Heroku AppLink (expose Heroku APIs to Flow / Apex / Agentforce), Heroku External Objects (Salesforce Connect oData), Platform Events, REST API in either direction, and Salesforce Canvas for UI embedding. Decision matrix + Heroku Connect deep dive (OAuth integration user, plan-tier row limits, polling cadence, region co-location). NOT for AWS integration (see integration/aws-salesforce-patterns), NOT for generic PaaS, NOT for MuleSoft."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "heroku salesforce integration which path should I use"
  - "heroku connect postgres bidirectional sync"
  - "heroku applink expose api to flow apex"
  - "heroku external objects salesforce connect odata"
  - "heroku canvas embed app in salesforce ui"
  - "heroku connect demo plan row limit"
tags:
  - heroku
  - heroku-connect
  - heroku-applink
  - salesforce-connect
  - canvas
  - postgres
  - integration-pattern
inputs:
  - "Direction: Salesforce → Heroku, Heroku → Salesforce, or bidirectional"
  - "Whether the Heroku side needs a local Postgres copy or just API access"
  - "Whether end users will see Heroku UI inside Salesforce (Canvas)"
  - "Plan tier (demo vs Enterprise / Shield)"
outputs:
  - "Recommendation: which Heroku integration path (Connect / AppLink / External Objects / Platform Events / REST / Canvas)"
  - "Decision: integration user setup, region co-location, plan tier"
  - "Specific limits the chosen path will hit"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Heroku ↔ Salesforce Integration

Heroku and Salesforce share an owner (Salesforce, Inc.) and that's reflected
in the integration surface — there are six well-defined paths, each tuned to
a different shape of problem. Picking wrong is the same shape of cost as it
is on the AWS side: a custom Apex callout where Heroku Connect would have
synced, or Connect when the team really needed AppLink's API exposure into
Flow.

This skill is the **decision layer** for Heroku-specific paths. AWS has its
own decision skill (`integration/aws-salesforce-patterns`); MuleSoft has its
own.

---

## Before Starting

- Confirm the direction. **Heroku Connect** is bidirectional but Postgres-centric. **AppLink** exposes Heroku APIs *into* Salesforce. **External Objects** virtualizes Postgres data *into* Salesforce without copy.
- Confirm the **plan tier**. Demo Heroku Connect caps at 10,000 synced rows and 10-minute minimum polling — fine for a proof of concept, never for production. Enterprise / Shield have flexible polling and unlimited (per contract) row counts.
- Confirm **region co-location**. Heroku Connect's wall-clock latency is dominated by the network round-trip between the Heroku Postgres region, the Connect add-on region, and the Salesforce org's instance region. Mismatched regions can multiply sync lag by 2–3×.
- Decide whether the integration user is an **integration-only Salesforce user** (recommended) or a real human's account (problematic — query limits per user, password rotation breaks the OAuth tie).

---

## Core Concepts

### The six Heroku integration paths

1. **Heroku Connect** — managed bidirectional sync between Salesforce SObjects and Heroku Postgres tables. OAuth-based; uses an integration Salesforce user. *Right when the Heroku app needs a local database copy of Salesforce data, or when both sides own different parts of the truth and need eventual-consistency sync.*
2. **Heroku AppLink** — newer (2024+) feature that exposes a Heroku-hosted API as a first-class service inside Salesforce, callable from Flow, Apex, Data Cloud, and Agentforce. *Right when Salesforce-side users / agents need to invoke Heroku-side business logic without an Apex callout class.*
3. **Heroku External Objects (Salesforce Connect with oData)** — Heroku Postgres tables surface in Salesforce as External Objects via an oData wrapper. Read or read-write. *Right when Salesforce users want to view / search / report on Heroku data without copying it.*
4. **Salesforce Platform Events → Heroku** — Heroku app subscribes to Salesforce Pub/Sub or CometD streaming. *Right for event-driven Heroku reaction to Salesforce changes; lower-overhead than Connect for pure event flow.*
5. **Heroku → Salesforce REST API** — Heroku app calls Salesforce REST endpoints directly using OAuth (Connected App, JWT bearer flow). *Right for one-shot operations the Heroku side initiates — approvals, metadata reads, custom Apex REST endpoints.*
6. **Salesforce Apex / Workflow → Heroku REST** — Apex callout via Named Credential to a Heroku app endpoint. *Right for synchronous Salesforce-initiated calls into Heroku logic; same caveat as Apex callouts to Lambda — governor limits apply.*

Plus a separate UI option: **Salesforce Canvas** embeds a Heroku web app inside the Salesforce UI (App Launcher, Service Console, Lightning page). Canvas is not Heroku-specific — any web app can be a Canvas app — but Heroku is a common host because of how easy the Connected App + Heroku app pairing is to wire.

### Heroku Connect mechanics

| Aspect | Detail |
|---|---|
| Auth | One Salesforce integration user per add-on. Distinct users for distinct add-ons (concurrent-query and token caps are *per user*). |
| Sync model | Trigger-based on the Postgres side (writes Postgres → Salesforce via the trigger log); polling on the Salesforce side (reads Salesforce → Postgres on the polling cadence). |
| Plan tiers (2026) | *Demo*: 10K rows, 10-minute polling, 7-day trigger log. *Enterprise* / *Shield*: per-contract row counts, configurable polling, 31-day trigger log. |
| Required permissions | `API Enabled`, `View All`, `Modify All`. Without `View All`, large queries can throw `OPERATION_TOO_LARGE`. |
| Not supported | Postgres connection pooling (use direct connections), `postgres_fdw`, Heroku review-app `app.json` add-on provisioning. |

### Salesforce Canvas: Signed Request vs OAuth Web Server Flow

Canvas has two auth models — Salesforce (the embedding container) signals to the Heroku app (the embedded UI) which user is logged in.

- **Signed Request (default)** — Salesforce POSTs a signed payload to the Heroku app when the user opens the Canvas app. No consent screen. The signed payload includes the user context, an OAuth token, and Salesforce instance URL. Right for embedded UIs where the user has already authenticated to Salesforce.
- **OAuth 2.0 Web Server Flow** — The Canvas app initiates a normal OAuth dance, including the Salesforce consent screen. Right for apps that also run outside the Canvas frame and need their own user identity.

Recommend Signed Request for any embedded-only Canvas app; OAuth for hybrid (embedded + standalone) apps.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Heroku app needs a local Postgres copy of Account / Contact / Custom Objects | **Heroku Connect** | Managed bidirectional sync; eventual consistency |
| Salesforce Flow needs to call a Python ML scoring service hosted on Heroku | **Heroku AppLink** | Exposes the API as a Flow-native action, no Apex callout class |
| Salesforce users want to search / report on Heroku transactional data without copying | **Heroku External Objects** | Salesforce Connect (oData) virtualizes the tables |
| Heroku service must react to Salesforce record changes within seconds | **Platform Events → Heroku subscriber** (Pub/Sub API) | Lower overhead than Connect for pure event flow |
| Heroku app needs occasional Salesforce data — not a continuous mirror | **Heroku → Salesforce REST API** with JWT bearer flow | No add-on, just OAuth |
| Salesforce trigger needs synchronous data from a Heroku microservice | **Apex callout via Named Credential** | Same governors as any callout — bulkify |
| Embed a Heroku UI inside Salesforce for end users | **Canvas (Signed Request)** | Default auth; no consent prompt |
| Demo / proof-of-concept: 1,000 records, daily check-ins | **Heroku Connect demo plan** | Free, 10K-row cap, 10-min polling — fine for POC |
| Production: 1M+ rows, sub-minute lag | **Heroku Connect Enterprise / Shield** | Demo plan cannot meet production SLAs |
| Cross-org integration where Heroku is just a passthrough | Probably **none of these** — use a direct Salesforce → Salesforce path or MuleSoft | Heroku adds latency without buying you anything |

---

## Common Patterns

### Pattern A — Heroku app with local Postgres mirror

**When to use.** A Heroku web app whose business logic is database-heavy
(joins, aggregates, full-text search) and whose source of truth lives in
Salesforce.

**How it works.** Heroku Connect add-on provisions on top of Heroku Postgres.
Configure object mappings in the Connect dashboard (Salesforce → Postgres
read-only, or bidirectional). Use a dedicated Salesforce integration user
with `API Enabled` + `View All` + `Modify All`. Region-align Heroku Postgres,
Connect, and Salesforce.

**Why not the alternative.** A custom polling job hitting Salesforce REST
API has zero managed retry, no trigger-log replay, and no easy way to
write back. Connect is the managed equivalent.

### Pattern B — Heroku-hosted API exposed to Flow / Agentforce

**When to use.** A Python / Node service does ML scoring, document parsing,
or any computation Apex isn't suited for, and a Salesforce admin / agent
needs to invoke it from a Flow or Agentforce action.

**How it works.** Configure Heroku AppLink on the Heroku app. Salesforce
admins discover the exposed actions in Setup → External Services / Flow
Builder; agents discover them as registered tools. No Apex callout class
needed; auth + parameter shape is handled by AppLink.

**Why not the alternative.** Writing an Apex `@InvocableMethod` wrapper
around an HTTP callout works but adds a code maintenance surface for
something the platform handles natively now.

### Pattern C — Virtualized Heroku Postgres data inside Salesforce

**When to use.** Heroku is the system-of-truth for some transactional data
(orders, sessions, telemetry) and Salesforce users need to view / search /
report on it from a Lightning record page.

**How it works.** Heroku External Objects exposes Postgres tables as oData
endpoints; Salesforce Connect consumes them as External Objects. The data
stays in Postgres; Salesforce queries it on demand.

**Why not the alternative.** Heroku Connect copies the data into Salesforce
storage (data + index costs). External Objects is read-mostly virtualization
— no storage cost, but join + filter performance is bounded by oData round
trips.

---

## Recommended Workflow

1. **State the integration in one sentence.** Direction, latency, volume, where the source of truth lives.
2. **Walk the Decision Guidance table.** First match wins. If two rows match, the more specific one (volume / latency) takes precedence.
3. **Choose plan tier.** Demo = POC only; Enterprise / Shield = production. The 10K-row cap on demo is the most common surprise.
4. **Set up the integration Salesforce user.** One per Heroku Connect add-on; `API Enabled` + `View All` + `Modify All`. Document the rotation cadence in your runbook.
5. **Co-locate regions.** Heroku Postgres, Connect add-on, Salesforce instance. Mismatched regions are the #1 latency surprise.
6. **For Canvas: Signed Request first.** OAuth Web Server Flow only if the app also lives outside Salesforce.

---

## Review Checklist

- [ ] Decision: which of the six paths, with one sentence justifying it against the alternatives.
- [ ] Plan tier explicit (demo vs Enterprise vs Shield).
- [ ] Integration user is dedicated to the Heroku Connect add-on (not shared with other integrations).
- [ ] Salesforce integration user has `View All` (large-query performance depends on it).
- [ ] Heroku Postgres / Connect / Salesforce regions are co-located.
- [ ] If Canvas: Signed Request unless explicit reason for OAuth.
- [ ] If Connect: trigger-log retention matches recovery SLO (7d demo, 31d Enterprise).
- [ ] No Postgres connection pooling on the Connect-attached database.

---

## Salesforce-Specific Gotchas

1. **Demo plan caps at 10,000 rows.** Hit silently — sync stops; status dashboard shows the cap. Plan for Enterprise / Shield before going to production. (Source: [Heroku Connect docs](https://devcenter.heroku.com/articles/heroku-connect))
2. **One integration user per add-on.** Salesforce caps concurrent queries (10) and active OAuth tokens (5) *per user*. Sharing a user across add-ons causes throttling. (See `references/gotchas.md` § 2.)
3. **Re-authenticating Connect to a different org is not supported.** Sandbox refresh requires recreating the Connect connection from scratch. (See `references/gotchas.md` § 3.)
4. **Postgres connection pooling breaks Connect.** Use direct connections from your Heroku app dyno. (See `references/gotchas.md` § 4.)
5. **`OPERATION_TOO_LARGE` on Connect's Salesforce queries** when the integration user lacks `View All`. The error doesn't name the missing permission; it surfaces as a generic large-query failure. (See `references/gotchas.md` § 5.)
6. **Canvas Signed Request and OAuth Web Server Flow are not interchangeable.** Mixing them (signing then re-running OAuth) creates a confused-deputy situation. (See `references/gotchas.md` § 6.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision recommendation | One paragraph naming the chosen path, plan tier, integration user model, and region. |
| Connection runbook | Integration user provisioning, plan tier procurement, region pinning, OAuth refresh cadence. |
| Risk register | Limits the design will get within 50 % of (row count, polling cadence, region latency) plus mitigation. |

---

## Related Skills

- `integration/aws-salesforce-patterns` — sibling skill for the AWS path; same decision-matrix shape.
- `integration/event-relay-configuration` — Pub/Sub → EventBridge for AWS; for Heroku-side Pub/Sub subscribers the same Pub/Sub API is the entry point.
- `architect/hybrid-integration-architecture` — broader topology decisions; consult before picking a Heroku path if AWS, MuleSoft, or self-hosted are also options.
- `standards/decision-trees/integration-pattern-selection.md` — the master integration decision tree; Heroku is one branch.
