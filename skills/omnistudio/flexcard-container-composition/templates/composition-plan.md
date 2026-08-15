# FlexCard Composition Plan

## Context

- Host: [ ] Lightning page (App Builder)  [ ] Experience Builder site
        [ ] External CMS (e.g. Adobe Experience Manager)
        [ ] Custom web container (e.g. Heroku)
- Primary record context / input parameter:
- Audience: [ ] internal  [ ] authenticated portal  [ ] **guest**
- Form factors: [ ] Desktop  [ ] Tablet  [ ] Phone

## Card Inventory

Name the data source by its **exact** wizard label, so a reviewer can check the
decision. Valid values: Apex REST, Apex Remote, Custom, SOQL Query, SOSL Search,
Streaming API, SDK, Omnistudio Data Mapper, Integration Procedures, None.

| Card | Role (Container / Child / Sibling) | Data source type | Source name | Fields returned |
|---|---|---|---|---|
|  |  |  |  |  |

Data source checks:

- [ ] No **SOQL Query** or **Custom** source on a shipping card — neither has
      anywhere to put FLS enforcement, a Cache Block, `requiredPermission`, or
      an error branch
- [ ] Every source projects down to the fields the template actually renders
      (the payload lands in the browser regardless of what is displayed)
- [ ] `fieldLevelSecurityEnabled` = true on any **Omnistudio Data Mapper** source
- [ ] Total data sources on the page: ______ — each one fires at render

## Parent → Child Wiring

The two mechanisms **do not compose**. Selecting a Data Node silently overrides
the child's own data source.

| Parent card | Child card | Mechanism | Data Node value | Attributes passed | Child data source |
|---|---|---|---|---|---|
|  |  | Data Node / Attributes | `{record}` / `{records}` / — |  | None / <type> |

- [ ] Every child fed by a **Data Node** has its data source set to **None**
      (for legibility — the override happens either way)
- [ ] Every child expected to **fetch its own** data has **no** Data Node
      selected on the parent, and receives an Attribute instead
- [ ] `{Parent.…}` merge syntax used only where an Attribute actually arrived
      in the child's Input Map

> Verbatim rule: "If a child uses the parent data source, it doesn't matter if
> its data source is configured or set to None. Either way, the parent's data
> source overrides the child's data source if a data node is selected because
> the record is already set."

## Event Contract (siblings and custom LWCs)

Module: `import pubsub from "lightning/omnistudioPubsub";`
Methods: `register(eventName, callbackobj)` · `unregister(eventName, callbackobj)` · `fire(eventName, action, payload)`

| Channel | Event | Payload shape | Fired by | Consumed by | Version |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

- [ ] Channels prefixed by **workspace**, not by component (`quoteworkspace`,
      not `quotelistcard`) — component prefixes break when a second consumer
      wants the event
- [ ] No generic names (`rowselected`, `refresh`, `update`) — the namespace is
      flat and page-wide
- [ ] `register()` is passed a **channel** as its first argument and a
      **callback object** (event name → bound handler) as its second
- [ ] The callback object is retained on the component and the **same instance**
      is passed to teardown
- [ ] Teardown present in `disconnectedCallback()`

## Input Parameters vs Events

Input parameters are evaluated at render and do **not** react.

| Value | Immutable (input param / Attribute) | Mutable (channel event) |
|---|---|---|
|  |  |  |

- [ ] Nothing that must change during the card's life is an input parameter

## States

| Card | State | Condition | Elements / actions unique to it |
|---|---|---|---|
|  |  |  |  |

- [ ] State conditions do not overlap
- [ ] More than three states on one card? → consider separate cards + a container
- [ ] **No state is relied on for authorization.** States are evaluated
      client-side against data the browser already holds. Enforce on the
      action's target: `requiredPermission` on the OmniScript or Integration
      Procedure, plus object/field/sharing permissions.

## Actions

| Card | Action label | Type (guided process / flyout / navigate / listen / notify) | Target |
|---|---|---|---|

- [ ] Navigation uses the **Navigate** action type — no `/lightning/r/...`,
      `/s/`, or full-domain literals, and no string-concatenated paths
- [ ] Update actions target an Integration Procedure, not a direct write
- [ ] Any action that must be *prevented* (not merely hidden) is gated on its
      target's permissions

## Datasource Caching

| Card | Cached? | Cache type (org / session) | TTL | Key inputs |
|---|---|---|---|---|

- [ ] No org cache on a guest-reachable or PII card
- [ ] TTL within Platform Cache bounds (5 min – 48 h org, 5 min – 8 h session)
- See `omnistudio/integration-procedure-cacheable-patterns` for the Cache Block
  boundary rules

## Verification

- [ ] Previewed on every required form factor
- [ ] Verified in the **target host** as a user from the **target audience** —
      the author's preview runs with the author's permissions
- [ ] **Network payload compared**, not only the rendered card — an
      over-permissive data source is invisible in the render and obvious in the
      response

## Sign-Off

- [ ] Exactly one data source per card, named by exact type
- [ ] No SOQL Query or Custom source shipped
- [ ] No child with both a parent Data Node and its own data source
- [ ] Event contract written down, versioned, workspace-prefixed
- [ ] Callback object retained and reused at teardown
- [ ] No state relied on for authorization; no overlapping conditions
- [ ] No hardcoded navigation paths
- [ ] **No DML anywhere against `OmniUiCard`** — the object reference marks it
      internal use only
- [ ] Verified in the target host as a target-audience user
