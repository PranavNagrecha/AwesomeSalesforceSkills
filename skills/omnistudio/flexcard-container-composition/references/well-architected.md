# Well-Architected Notes — FlexCard Composition

## Relevant Pillars

- **User Experience** — card composition is the difference between a
  responsive console and a sluggish one.
- **Performance** — nested cards each hit the server; composition
  choices ARE performance choices.
- **Operational Excellence** — named events + IP datasources centralise
  behaviour for later change.

## Architectural Tradeoffs

- **Single fat card vs composed cards:** fat card is simpler but harder
  to reuse; composed cards reuse and scale but need event contracts.
- **IP per card vs one IP for the page:** one IP keeps the call count
  low; per-card IPs are easier to evolve. Default to per-card.
- **Direct SOQL vs IP-based datasource:** direct is fastest to build and
  slowest to secure. Prefer IP.

## Event Naming Hygiene

- Namespace by widget.
- Version the payload in the skill-local contract file.
- Avoid generic names like `rowselected` on shared pages.

## Official Sources Used

- FlexCards Overview —
  https://help.salesforce.com/s/articleView?id=sf.os_flexcards_overview.htm
- FlexCard Events —
  https://help.salesforce.com/s/articleView?id=sf.os_flexcard_events.htm
