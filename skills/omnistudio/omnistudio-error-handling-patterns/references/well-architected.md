# Well-Architected Notes — OmniStudio Error Handling

## Relevant Pillars

- **Reliability** — explicit failure boundaries keep data consistent across Salesforce and downstream systems.
- **User Experience** — meaningful fault screens and retry paths reduce abandon rates.
- **Operational Excellence** — correlation IDs and structured error responses support incident investigation.

## Architectural Tradeoffs

- **Fail-fast vs continue-with-defaults:** fail-fast protects integrity but can block user flow; continue-with-defaults keeps the flow moving but needs clear "unavailable" messaging.
- **Client retry vs server retry:** client retry is simpler but needs idempotency; server retry is more reliable but needs a queue.
- **Compensating action vs eventual consistency:** compensating actions are precise but complex; eventual consistency is simpler but the user sees a lag.

## Anti-Patterns

1. Defaulting every step to `Continue on Error`.
2. Returning 200 with an `errors` array the caller is expected to parse but no caller does.
3. Generic "Something went wrong" messages that give the user no action.

## Official Sources Used

- OmniStudio Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm
- OmniStudio DataRaptor — https://help.salesforce.com/s/articleView?id=sf.os_dataraptor.htm
- Salesforce Well-Architected Reliability — https://architect.salesforce.com/docs/architect/well-architected/trusted/reliable
