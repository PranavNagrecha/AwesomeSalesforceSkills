# FlexCard Composition — Examples

## Example 1: Account Overview (Single Card)

- Layout: card.
- Data source: IP `getAccountOverview` — aggregates account, top
  opportunities, last 3 cases.
- Actions: "Open Case" (OmniScript launch), "Edit Industry" (DR Update).
- Cache: IP is cacheable with TTL 60s, key includes account id.

## Example 2: Quotes List → Quote Detail (Parent/Child)

- Parent FlexCard: layout=list, datasource IP `listQuotesForAccount`.
- Row click fires `quoteselected` with `{quoteId}`.
- Child FlexCard: subscribes on `quoteselected`, rerenders with new
  `quoteId` input, calls IP `getQuoteDetail`.
- Benefit: parent is agnostic of detail shape; child is agnostic of how
  it was selected.

## Example 3: Case Side Panel (FlexCard Inside Lightning Record Page)

- Card is placed on Case record page.
- Input param `recordId` from page context.
- Datasource: DR Extract on Case — lightweight.
- Action: "Escalate Case" → OmniScript modal.

## Example 4: Service Console Workspace Tabs

- Parent: none (Lightning tabset).
- Each tab hosts one FlexCard.
- Tabs do not share state; each card owns its datasource.
- Navigation between tabs uses Lightning messages, not cross-card events.

## Example 5: Event Contract

```json
{
  "event": "quoteselected",
  "payload": { "quoteId": "0Q0..." }
}
```

Contract is versioned in a skill-local doc so parent and child evolve
together.
