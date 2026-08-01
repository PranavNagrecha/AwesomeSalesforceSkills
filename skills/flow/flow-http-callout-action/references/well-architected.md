# Well-Architected Notes — Flow HTTP Callout Action

**Reliability:** the action has two distinct failure classes and they need different
handling. Transport failures — timeout, 5xx, authentication — belong on the fault
connector. Successful-but-unhelpful responses, which are far more common, belong on a
Decision after the success connector. A flow with only a fault path handles the rarer of
the two. Use `templates/flow/FaultPath_Template.md` rather than re-authoring a fault path
per flow.

**Operational Excellence:** the integration becomes admin-owned, which is the point — but
the schema is derived from a pasted sample, so the sample is effectively the contract.
Capture it from the live endpoint and prefer a non-ideal response, because fields absent
from the sample do not exist as flow resources at all.

**Performance:** run callouts from the asynchronous path of a record-triggered flow. On
the synchronous path the partner's latency becomes the user's save latency, and inside a
loop the transaction meets the documented 100-callouts-per-transaction limit and the
120-second cumulative callout timeout — usually the timeout first.

## Official Sources Used

- Named Credentials and External Credentials — the credential model the HTTP Callout action requires, including principal access grants — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- ExternalCredential metadata type — authentication protocol, named principal and auth parameters — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_externalcredential.htm
- Flow Builder — HTTP Callout actions and schema from a sample response — https://help.salesforce.com/s/articleView?id=platform.flow_build_extend_httpcallout.htm
- Apex Governor Limits — 100 callouts per transaction and a 120-second cumulative callout timeout, which apply to a flow transaction — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Flow Builder — record-triggered flow run order, including the asynchronous path after the transaction completes — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_recordchange.htm
