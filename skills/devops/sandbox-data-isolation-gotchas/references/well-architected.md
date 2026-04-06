# Well-Architected Notes — Sandbox Data Isolation Gotchas

## Relevant Pillars

- **Security** — The primary pillar for this skill. Sandbox data isolation directly prevents the exposure of production customer data (email addresses, PII) to unintended recipients. Misconfigured sandboxes have sent bulk emails to real customers, triggered external API calls against live payment processors, and exposed production records to QA contractors who should only have access to anonymized data. Every isolation control in this skill is a security control.
- **Reliability** — Scheduled jobs that fire against production systems from a sandbox degrade the reliability of production integrations: they consume rate-limited API quotas, insert duplicate records, and create noise in production monitoring. Isolation controls are also reliability controls for the production org.
- **Operational Excellence** — A repeatable, automated isolation process reduces manual effort and eliminates the human error that causes incidents. The SandboxPostCopy pattern and the post-refresh runbook are operational excellence artifacts. Orgs that skip this investment pay repeatedly in incident response time.
- **Performance** — Less directly applicable. Large Contact/Lead email scrub operations in SandboxPostCopy must be designed carefully (chunked Queueable, SOQL within governor limits) to avoid hitting CPU time or heap limits. Poorly written SandboxPostCopy classes can delay sandbox availability for users.

## Architectural Tradeoffs

**Automated isolation via SandboxPostCopy vs. manual runbook only.**
SandboxPostCopy is the correct default. It runs before users can log in and trigger automations. The tradeoff: the Automated Process user's limited permissions mean some isolation steps cannot be automated and must remain in the manual runbook (Named Credential URLs, deliverability setting, OAuth re-authorization). An incomplete SandboxPostCopy that tries to do everything and fails on one step is worse than a targeted SandboxPostCopy with a documented manual complement — use try/catch blocks and log failures rather than letting one failed step abort all isolation work.

**Deliverability set to `No Access` vs. `System Email Only`.**
`No Access` is the safest setting and eliminates email leakage risk entirely. However, it suppresses system emails that QA teams need (password resets, sandbox activation links). `System Email Only` is the recommended default for most sandboxes: it allows system emails while suppressing workflow alerts and Apex emails. Teams that need to test email deliverability for specific features should create a dedicated sandbox with `All Email` enabled and with a restricted set of test Contact records (all with `.invalid` addresses).

**Scrubbing Contact/Lead emails in SandboxPostCopy vs. relying on deliverability alone.**
Relying solely on deliverability is fragile — one accidental change to the deliverability setting exposes all Contact/Lead email addresses. Defense in depth calls for both: scrub email addresses AND set deliverability to `System Email Only`. If one control drifts, the other still provides protection.

## Anti-Patterns

1. **Assuming missing Named Credential secrets make integrations safe** — Practitioners often believe that because secrets are blanked on refresh, sandbox integrations cannot reach production. In orgs using certificate-based auth, IP-allowlisted APIs, or sandbox callout whitelists, this assumption is false. The correct posture is to audit endpoint URLs and abort scheduled jobs regardless of whether credentials are present.

2. **Writing a single SandboxPostCopy class with no error handling** — A class that throws on the first failed DML leaves all subsequent isolation steps unexecuted. If the Automated Process user cannot abort a CronTrigger (permissions), the class throws and Contact email scrubbing never runs. Use fine-grained try/catch blocks so the class is resilient to partial failures.

3. **Using the sandbox for performance or load testing without verifying endpoint config first** — Performance tests in a Full sandbox using unmodified Named Credentials pointing at production endpoints can saturate production API rate limits. Verify all outbound integration targets before any load or stress testing begins in a sandbox.

## Official Sources Used

- Salesforce Help: Sandbox Email Deliverability — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_email.htm
- Salesforce Help: Sandbox Setup Considerations — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_implementation_tips.htm
- Salesforce Help: Refresh Your Sandbox — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_refresh.htm
- Salesforce Help: Create or Edit Sandbox Templates — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_create_templates.htm
- Apex Reference Guide: SandboxPostCopy Interface — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_SandboxPostCopy.htm
- Apex Reference Guide: SandboxContext Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_SandboxContext.htm
- Salesforce Help: Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Salesforce Well-Architected: Security Pillar — https://architect.salesforce.com/well-architected/secure/overview
