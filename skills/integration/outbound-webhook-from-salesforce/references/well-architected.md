# Well-Architected Notes — Outbound Webhook

## Relevant Pillars

- **Reliability** — retry + DLQ is the load-bearing design, not the
  callout itself.
- **Security** — HMAC signing + Named Credential External Credential keep
  secrets out of metadata.
- **Operational Excellence** — correlation ids make the pipeline
  debuggable across Salesforce and the receiver.

## Architectural Tradeoffs

- **Flow vs Apex:** Flow lowers barrier but lacks retry primitives; Apex
  gives full control but requires dev ownership.
- **Sync vs async callout:** async is correct for most producers; sync is
  only justified when the UI needs the response.
- **Fine-grained DLQ vs coarse alert:** fine-grained helps replay; coarse
  is cheaper to build.
- **Outbound Message legacy vs modern:** outbound messages still exist
  but are hard to evolve; treat as end-of-life.

## Official Sources Used

- Apex HTTP Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_http.htm
- Flow HTTP Callout — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_action_http_callout.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
