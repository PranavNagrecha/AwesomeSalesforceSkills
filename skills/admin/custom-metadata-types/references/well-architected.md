# Well-Architected Notes - Custom Metadata Types

## Relevant Pillars

### Operational Excellence

Custom Metadata Types improve operational consistency because configuration can move through source control, code review, deployment automation, and rollback paths instead of living only in manual production edits.

### Reliability

Metadata-driven configuration reduces environment drift and hardcoded IDs. The same release artifact can promote rules and defaults consistently across sandboxes and production.

### Security

Security matters because teams often misuse CMT for secrets or misunderstand protected visibility. The right design keeps credentials in Named Credentials and uses packaging visibility intentionally.

## Architectural Tradeoffs

- **Deployable control vs rapid production edits:** CMT is safer for release-managed config, but it is intentionally less convenient for ad hoc operational editing.
- **Public subscriber flexibility vs protected package defaults:** Public records are easier for admins to adjust, while protected defaults preserve package-owned internals.
- **One shared config store vs clear separation of concerns:** It is tempting to put every value in CMT, but user overrides, secrets, and reportable data often belong elsewhere.

## Anti-Patterns

1. **Secrets in public custom metadata** - configuration becomes readable in places where credentials should never live.
2. **Treating metadata as transactional data** - operations workflows become awkward because the storage model fights the runtime behavior.
3. **Hardcoded org-specific IDs alongside CMT** - the team pays the complexity cost of metadata without actually removing deployment drift.

## Official Sources Used

- Metadata API Developer Guide - https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadata.htm
- Custom Metadata Types (Help) - https://help.salesforce.com/s/articleView?id=sf.custommetadata_about.htm&type=5
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
