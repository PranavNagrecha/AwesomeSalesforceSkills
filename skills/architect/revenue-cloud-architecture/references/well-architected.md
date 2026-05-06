# Well-Architected Notes — Revenue Cloud Architecture

## Relevant Pillars

- **Reliability** — RLM <-> ERP integration is on the critical path
  for revenue. The architect-recommended event-driven shape (CDC /
  Platform Events) provides durable replay; synchronous coupling
  ties revenue capture to ERP availability.
- **Operational Excellence** — LegalEntity governance, period close
  cadence, and integration replay are operational concerns that
  determine whether RLM scales smoothly or accumulates technical
  debt.
- **Security** — Multi-entity scoping has implications for who can
  see and post to which entity. Sharing on `LegalEntity`,
  `Invoice`, and `BillingSchedule` must reflect legal-jurisdiction
  separation.

## Architectural Tradeoffs

- **Native RLM vs CPQ classic vs hybrid.** Greenfield builds should
  target native RLM. Existing investments in CPQ classic
  (`SBQQ__`) carry sunk cost; rip-and-replace is rarely justified
  on cost alone. Hybrid is common during transition.
- **Eventing (CDC / Platform Events) vs Apex callouts for ERP
  integration.** Eventing is durable and decoupled. Callouts are
  immediate and tied to the originating transaction. For high-volume
  order / invoice flow, eventing wins. For low-volume "post and
  confirm" patterns where Salesforce needs the ERP response, async
  callouts may be acceptable.
- **Few LegalEntity vs many.** Few = simpler reporting and tax
  config; many = closer alignment with legal structure but heavier
  operational burden. Default to fewest entities legal allows.
- **Asset state-period model vs delete-and-replace.** State periods
  preserve audit history. Delete-and-replace loses it. RLM's model
  trades a more complex query story for full history.

## Anti-Patterns

1. **Synchronous trigger callouts to ERP.** Blocked by the platform.
2. **Mixing `blng__` (Salesforce Billing managed package) and
   native RLM objects** in the same code without namespace
   discipline.
3. **LegalEntity per region without legal / tax justification.**
4. **Hard-deleting Asset / Contract / Order rows.** Breaks the
   state-period model.
5. **Skipping PricebookEntry for "RLM Pricing".** Pricebook is still
   the linkage; RLM extends it.

## Official Sources Used

- Plan Your Revenue Cloud Implementation — https://help.salesforce.com/s/articleView?id=ind.plan_your_revenue_cloud_implementation.htm&type=5
- Revenue Cloud Billing Data Model — https://developer.salesforce.com/docs/industries/rev-cloud-billing/guide/rev-cloud-billing-data-model.html
- Transaction Management: Order Data Model — https://developer.salesforce.com/docs/industries/revenue-cloud-transaction-mgmt/guide/revenue-cloud-transaction-mgmt-order-data-model.html
- ERP Integration Architectural Considerations for Lead to Cash — https://architect.salesforce.com/decision-guides/erp-integration
- Salesforce Architects: Quote-to-Cash — https://architect.salesforce.com/well-architected/adaptable/composable
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/well-architected/trusted/resilient
