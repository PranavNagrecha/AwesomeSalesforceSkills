# Well-Architected Notes — FlexCard Composition

## Relevant Pillars

- **User Experience** — composition is what separates a console that feels
  instant from one that feels sluggish. Every data source on the page fires at
  render, so the user waits for the slowest path, not the average one.
- **Performant** — composition choices *are* performance choices. Collapsing
  four card-level data sources into one Integration Procedure is a larger win
  than any client-side optimisation available afterwards, because it removes
  round trips rather than shaving them.
- **Secure** — the pillar that gets designed last here. A card's data source
  determines whether field-level security is enforced; a card's state determines
  what is *shown*, not what is *permitted*. Conflating the two is the domain's
  characteristic security defect.
- **Adaptable** — a card that owns one concern and one data source can be reused
  on a second page. A card with seven states and five data sources can only be
  taken whole.

## Architectural Tradeoffs

- **Data Node vs Attributes for parent/child.** A Data Node is one round trip
  and a shape coupled to the parent's fetch; the child renders exactly what the
  parent has. Attributes plus the child's own fetch is two round trips and an
  independently evolvable child. Critically, these do not compose: selecting a
  Data Node *overrides* the child's data source. Choose one deliberately.
- **Parent/child vs siblings on a channel.** Parent/child is simpler and
  couples the pieces structurally. Siblings over a pubsub channel are
  independently deployable and testable but require a written event contract —
  channel, event, payload shape, publisher, consumers, version — because names
  live in a flat page-wide namespace.
- **One Integration Procedure per page vs per card.** One IP keeps the call
  count minimal and centralises error handling; per-card IPs let each card
  evolve alone. Default to per-card for independent concerns and to one IP where
  the sections genuinely render one record's story.
- **Integration Procedure vs Data Mapper as a card's source.** An IP gives you
  aggregation, a Cache Block, `requiredPermission`, and one error surface. A
  Data Mapper Extract is lighter for a single-object read and still enforces
  FLS via `fieldLevelSecurityEnabled`. Neither SOQL Query nor Custom belongs in
  a shipped card.
- **States vs separate cards.** States collapse several near-identical layouts
  into one adaptive card, at the cost of reviewability — overlapping conditions
  are invisible to a reader holding seven layouts in mind. Past about three
  states, separate cards plus a container are easier to reason about.
- **Reuse across hosts vs host-specific tuning.** FlexCards publish to Lightning
  pages, Experience Builder sites, external CMSs, and custom web containers.
  Designing for portability (Navigate actions rather than paths; audience-safe
  data sources) costs a little now and prevents a silent break the day the card
  is reused.

## Event Contract Hygiene

- Prefix channels by **workspace**, not by component: `quoteworkspace`, not
  `quotelistcard`. Prefixing by component breaks the moment a second consumer
  legitimately wants the event.
- Version the payload shape and record it where both the publisher's and the
  consumers' authors will see it.
- Retain the callback object on the component so teardown passes the same
  instance; the documentation requires "both the channel name and instance of
  your event handler objects."
- Never ship a generic name — `rowselected`, `refresh`, `update` — into a flat
  page-wide namespace.

## Composition Hygiene

- One data source per card, chosen by exact type name so a reviewer can check
  the decision.
- Immutables travel as input parameters and Attributes; mutables travel as
  channel events. Input parameters are evaluated at render and do not react.
- Never DML `OmniUiCard` — the object reference marks it internal use only.
- Test in the target host as a user from the target audience, comparing the
  network payload rather than the rendered output.

## Official Sources Used

- **Data Source Wizard Steps & FlexCard Configuration — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards/meet-the-data-source-wizard
  — source for the complete list of ten data source types and their verbatim
  descriptions: Apex REST, Apex Remote, Custom, SOQL Query, SOSL Search,
  Streaming API, SDK, Omnistudio Data Mapper, Integration Procedures, and None.
  Verified 2026-08-14.
- **Child FlexCards: Configuration & Benefits — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards-building-and-publishing/work-with-child-flexcards
  — source for the **Flexcard Name**, **Data Node** (`{record}`, `{records}`)
  and **Attributes** properties on the parent's Flexcard element, the child's
  **Input Map** section and `{Parent.Id}` reference syntax, the statement that
  "there's no limit to the number of child Flexcards on one Flexcard", and —
  load-bearing for this skill — the verbatim override rule: "If a child uses the
  parent data source, it doesn't matter if its data source is configured or set
  to None. Either way, the parent's data source overrides the child's data
  source if a data node is selected because the record is already set."
  Verified 2026-08-14.
- **FlexCards Capabilities Summary — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards/discover-the-key-capabilities-of-flexcards
  — source for "A Flexcard state determines what the user can see and do on the
  card", the statement that conditions evaluate data and display the matching
  state, the action categories (launching guided processes, flyout windows,
  navigating to records, listening for events from other FlexCards, notifying
  components), the embeddability facts (in other FlexCards, and inside an LWC
  OmniScript), and the publication targets: Lightning pages via Lightning App
  Builder, Community/portal pages via Experience Builder, external content
  management systems such as Adobe Experience Manager, and custom web containers
  such as Heroku. Verified 2026-08-14.
- **Omnistudio Pubsub — Lightning Component Reference** —
  https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-omnistudio-pubsub.html
  — source for the import (`import pubsub from "lightning/omnistudioPubsub"`),
  the three public methods `register(eventName, callbackobj)`,
  `unregister(eventName, callbackobj)` and `fire(eventName, action, payload)`,
  the complete code example (which registers on a *channel* with a callback
  object mapping event names to bound handlers), the lowercase naming
  convention, and the requirement to "always unregister event handlers when a
  component is disposed or disconnected" passing "both the channel name and
  instance of your event handler objects." Verified 2026-08-14.
- **OmniUiCard — Object Reference for the Salesforce Platform (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omniuicard.htm
  — source for the internal-use-only marking: "This object and associated
  records are only for internal use. Don't perform any create, edit, or delete
  operations on this object," and "modifying or deleting this object's records
  may result in errors" with your implementation. Present from API 51.0 through
  67.0. Verified 2026-08-14.
- **Omnistudio Metadata API Types — Industries Common Resources Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_metadata_api_parent.htm
  — source for the ten documented Omnistudio metadata types (Flow for
  Omnistudio, OmniDataTransform, OmniExtTrackingDef, OmniIntegrationProcedure,
  OmniInteractionAccessConfig, OmniInteractionConfig, OmniScript,
  OmniscriptDefinition, OmniStudioSettings, OmniTrackingGroup) and the
  observation that `OmniUiCard` is not among them. Verified 2026-08-14.
- **OmniDataTransform — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omnidatatransform.htm
  — source for `fieldLevelSecurityEnabled` ("Indicates whether the Omni Data
  Transformation must check the user field-level access") and
  `requiredPermission`, cited in the data-source security guidance above.
  Verified 2026-08-14.

### Sources deliberately not used

The Salesforce Help articles on FlexCards (`os_omnistudio_flexcards_*`,
`os_flexcard_events`, `os_flexcard_data_sources`) are canonical prose for this
topic, but `help.salesforce.com` renders no article text to a document fetcher,
so nothing from them is quoted. Every property label and API detail above is
grounded in Trailhead or `developer.salesforce.com` instead. Two open questions
— whether `unsubscribe` is a real alias for `unregister`, and what FlexCards'
absence from the Omnistudio Metadata API Types list means for deployment — are
marked inline with `<!-- UNVERIFIED -->` in `examples.md` and `gotchas.md`
rather than resolved by inference.
