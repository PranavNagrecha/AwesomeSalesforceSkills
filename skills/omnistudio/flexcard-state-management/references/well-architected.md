# Well-Architected Notes — FlexCard State Management

## Relevant Pillars

- **User Experience** — predictable, targeted refresh feels faster and less flickery than aggressive full-card reload.
- **Reliability** — parent/child/sibling contracts remain stable when any one card is redesigned.
- **Performance** — avoiding unnecessary data source calls reduces governor-limit pressure on heavy pages.

## Architectural Tradeoffs

- **Pubsub vs parameter-driven rerender:** parameters are simpler for parent-child; pubsub is required for sibling-to-sibling or across nested layouts.
- **Optimistic UI vs server-authoritative UI:** optimistic feels faster but needs reconciliation on failure; server-authoritative is simpler but slower.
- **Full card refresh vs element-level refresh:** full refresh is safer but more expensive; element-level is faster but can leave stale derived state.

## Anti-Patterns

1. Reaching into another card's cache via DOM or framework internals.
2. Using a generic pubsub event name (`refresh`) that any card can trigger.
3. Caching server state in session variables instead of using data sources.

## Official Sources Used

- OmniStudio FlexCard Designer documentation — https://help.salesforce.com/s/articleView?id=sf.os_flexcards.htm
- OmniStudio FlexCard Actions reference — https://help.salesforce.com/s/articleView?id=sf.os_flexcard_actions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
