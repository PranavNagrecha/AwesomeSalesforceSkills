# Well-Architected Notes — Data Cloud Code Extensions

## Relevant Pillars

- **Security** — code extensions run arbitrary Python against customer data, so the guard
  rails are organizational: the Data Cloud Architect permission set gates who can run,
  monitor, and migrate; the feature is off until enabled in Feature Manager and is not
  supported at all with BYOK. The sharpest edge is the Logs DLO
  (`DataCustomCodeLogs__dll`) — any user with access to it can view its contents, so
  stdout must never carry PII or credentials. Governance tags on DLOs/DMOs the script
  creates or updates are assigned and audited manually, not inferred.
- **Operational Excellence** — the documented lifecycle is local → sandbox → production,
  with validation in the sandbox before a DevOps Data Kit promotes the transform, its
  auto-included code extension, and its manually added DLOs/DMOs in a fixed dependency
  order. The Logs DLO is the observability surface; review it after every first run.
- **Reliability** — compute is isolated and ephemeral: Salesforce's architecture blog
  describes the compute resources as spinning up to execute the task and tearing down
  immediately after, "leaving no residual footprint or persistent backdoor access."
  Scripts and functions should therefore be
  self-contained per run; chunking functions must process each request independently
  because Data 360 can invoke them multiple times depending on batching. Deployment stops
  on the first failed data-kit component, so ordering and completeness are reliability
  concerns, not just process hygiene.
- **Performance** — keep the deployed container lean: runtime dependencies only in
  `requirements.txt`, dev/test packages in `requirements-dev.txt`, and the Dockerfile
  unmodified so builds stay reproducible.

## Architectural Tradeoffs

- **Native transform vs. code extension.** A code extension buys expressiveness (string
  manipulation, custom computations, data cleansing beyond native transforms) at the cost
  of a full toolchain — Python 3.11, JDK 17, Docker, CLI plugin — plus a container
  lifecycle and a data-kit promotion process. If a native transform can express the logic,
  use it.
- **In-platform Python vs. external pipeline.** An external ETL avoids the BYOK and edition
  gates but adds an integration to secure, operate, and reconcile; a code extension keeps
  compute, logs, and governance inside Data 360. Choose external only when the gates rule
  the feature out.
- **Custom chunking vs. default chunking.** A chunking function improves retrieval quality
  when default boundaries split related content, but it adds deployed code to version and
  monitor for every search index that selects it. Adopt it after observing retrieval
  failures, not preemptively.

## Anti-Patterns

1. **Sensitive data in stdout** — logging record payloads "for debugging" publishes them to
   every user with Logs-DLO access. Log metadata, never field values.
2. **Cross-type transforms** — designing a script that reads DLOs and writes DMOs ignores
   the parity rule (DLOs→DLOs, DMOs→DMOs, transform-type DMO targets only) and forces a
   late redesign.
3. **Undocumented promotion paths** — the DevOps Data Kit is the documented promotion
   mechanism for code extensions and their transforms; a plan built on any other vehicle
   isn't grounded in the Code Extension developer guide and risks stranding the transform
   in the sandbox.

## Official Sources Used

- Extend Data 360 with Custom Code (overview, BYOK restriction, permission model) — https://developer.salesforce.com/docs/data/data-cloud-code-ext/guide/use-custom-code.html
- Set Up Salesforce CLI for Code Extension (toolchain versions, editions, scaffold anatomy) — https://developer.salesforce.com/docs/data/data-cloud-code-ext/guide/set-up-sdk.html
- Use Custom Scripts in Data 360 (object-type parity, Logs DLO, governance tags) — https://developer.salesforce.com/docs/data/data-cloud-code-ext/guide/use-custom-script.html
- Use Custom Functions in Data 360 (chunking contract, payload types, logging cautions) — https://developer.salesforce.com/docs/data/data-cloud-code-ext/guide/use-custom-function.html
- Migrate Code Extension to Production (DevOps Data Kits, deployment order) — https://developer.salesforce.com/docs/data/data-cloud-code-ext/guide/migrate-code-to-prod.html
- The Salesforce Developer's Guide to the Summer '26 Release (isolated containers, Python-only, roadmap) — https://developer.salesforce.com/blogs/2026/06/the-salesforce-developers-guide-to-the-summer-26-release
- How to Power Data 360 with Code Extension (ephemeral compute: spin up per task, tear down after, "no residual footprint or persistent backdoor access"; runtime isolation) — https://www.salesforce.com/blog/power-data-360-code-extension/
