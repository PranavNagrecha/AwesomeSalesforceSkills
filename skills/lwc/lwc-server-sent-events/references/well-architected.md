# Well-Architected Notes — LWC Streaming

## Relevant Pillars

- **Reliability** — delivery semantics (replayId) determine whether users
  see eventual consistency.
- **User Experience** — push beats poll when latency matters.
- **Scalability** — daily event delivery cap is a shared resource; design
  with other consumers in mind.

## Architectural Tradeoffs

- **Push vs polling LDS cache:** push gets sub-second updates but costs
  daily event budget; polling is simpler and may suffice.
- **One subscription per component vs one per page:** per-component is
  easy but multiplies delivery cost; per-page is efficient but requires
  fan-out plumbing.
- **Platform Events vs CDC:** CDC is cheaper when you just need field
  change notifications; PE is the right tool for domain-level events.

## Official Sources Used

- lightning/empApi — https://developer.salesforce.com/docs/platform/lwc/guide/use-comm-empapi.html
- Platform Events — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- CDC — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Streaming API replay — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/replay_process.htm
