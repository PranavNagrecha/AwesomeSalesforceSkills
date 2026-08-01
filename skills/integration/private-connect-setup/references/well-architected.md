# Well-Architected Notes — Private Connect Setup

**Security:** Private Connect changes the path packets take. It does not authenticate
callers and it replaces none of the other controls — network access restrictions,
Connected App policy, certificate authentication and the endpoint service's own allow-list
all still apply and all still have to be configured. Treating it as a trust boundary is
how teams end up relaxing the controls that were doing the real work.

**Performance:** the benefit is a predictable path rather than a faster one, and it is
regional by construction. The org's instance region and the endpoint service's region must
match, which is a design-time constraint discovered at configuration time if nobody checks
first.

**Operational Excellence:** because the public hostname keeps resolving and working, a
successful callout is not evidence of migration. Verification belongs on the receiving
side — source address in the access log, bytes on the endpoint service, and a negative
test that blocks the public route.

## Official Sources Used

- Private Connect overview and prerequisites (Hyperforce, inbound and outbound connections) — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Named Credentials — endpoint configuration and External Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- NamedCredential metadata type — the parameters used to repoint an endpoint — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_namedcredential.htm
- Salesforce Trust — instance and infrastructure lookup used to confirm region — https://help.salesforce.com/s/articleView?id=sf.instance_status.htm
- Apex Callouts — the Unauthorized endpoint exception and endpoint authorisation, which Private Connect does not change — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
