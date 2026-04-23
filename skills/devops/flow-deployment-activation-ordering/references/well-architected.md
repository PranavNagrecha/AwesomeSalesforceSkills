# Well-Architected Notes — Flow Deployment & Activation

## Relevant Pillars

- **Reliability** — paused-interview survival and deterministic rollback
  are the load-bearing properties.
- **Operational Excellence** — repeatable pre-deploy inventory and
  post-deploy verification eliminate "deploy and pray."
- **Security** — version retention policies interact with audit
  obligations (some industries require prior versions retained).

## Architectural Tradeoffs

- **Auto-activate vs inactive-then-activate:** auto is fast but risky;
  inactive-first is safer for flows with paused interviews or critical
  callers.
- **Delete vs retain prior versions:** retention protects paused
  interviews but costs storage.
- **Redeploy for rollback vs pointer flip:** redeploy creates a new
  version and complicates forensics; pointer flip preserves history.

## Official Sources Used

- Flow Metadata — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flow.htm
- Paused Interviews — https://help.salesforce.com/s/articleView?id=sf.flow_admin_paused.htm
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
