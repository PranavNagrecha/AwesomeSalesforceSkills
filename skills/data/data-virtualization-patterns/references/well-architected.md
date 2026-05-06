# Well-Architected Notes — Data Virtualization Patterns

## Relevant Pillars

- **Performance** — External Object queries add a network round-trip
  on every page render. The performance budget for Lightning page
  load (typically a few hundred ms before users complain) caps the
  remote source's response time. A slow source breaks UX.
- **Security** — External Objects pass through named credentials and
  run-as user contexts that differ from native sharing. The security
  model is the source's plus the connector's auth, not Salesforce's
  sharing model. Audit accordingly.
- **Reliability** — Source unavailability surfaces as blank related
  lists or page-load timeouts in Salesforce. Without explicit
  fallback or caching, the user experience is determined by the
  source's uptime.

## Architectural Tradeoffs

- **Virtualize vs replicate.** Virtualization wins on storage cost,
  data residency, and freshness. Replication wins on automation
  surface (triggers, flows, validation), reporting, search, and
  resilience to source outages. For high-volume historical data the
  hybrid (replicate recent N months, virtualize the tail) is
  frequently the right answer.
- **OData 4.0 vs 2.0 vs custom Apex.** OData 4.0 is the default for
  new external sources that can speak OData. Custom Apex is the
  escape hatch but adds engineering ownership of pagination, type
  mapping, auth refresh, error mapping, and metadata refresh.
- **Cross-org adapter vs CDC + Platform Event push.** Cross-org is
  read-time virtualization across two Salesforce orgs. CDC + Platform
  Events is push replication. Pick by the freshness / staleness
  contract and the automation requirements on the consuming side.
- **Writable External Objects vs custom-object staging.** Writable
  External Objects work for editable display. Custom-object staging
  + outbound trigger callout is required when Salesforce automation
  needs to react to the write.

## Anti-Patterns

1. **Adding triggers, validation, or record-triggered flows to
   `__x` objects.** Not supported; will not work.
2. **Indirect Lookup against a non-unique parent field.** Misbehaves
   with duplicate matches.
3. **Ignoring callout-budget arithmetic.** Page renders with several
   External Object components quickly hit the 100-per-transaction
   sync callout cap.
4. **Promising features the adapter does not support** (search,
   reports, roll-ups). Validate adapter capability before scoping
   requirements.
5. **Bypassing sharing assumptions in the cross-org adapter.** The
   source org's sharing applies via the connector identity.

## Official Sources Used

- Salesforce Connect Overview — https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5
- External Objects — https://help.salesforce.com/s/articleView?id=sf.platform_connect_about_external_objects.htm&type=5
- OData Adapter for Salesforce Connect — https://help.salesforce.com/s/articleView?id=sf.platform_connect_odata_about.htm&type=5
- Cross-Org Adapter for Salesforce Connect — https://help.salesforce.com/s/articleView?id=sf.platform_connect_xorg_about.htm&type=5
- Salesforce Connect Apex Custom Adapter — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_connect_api_intro.htm
- Salesforce Well-Architected Composable — https://architect.salesforce.com/well-architected/adaptable/composable
