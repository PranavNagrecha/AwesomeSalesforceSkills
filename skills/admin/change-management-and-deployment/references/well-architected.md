# Well-Architected Mapping: Change Management and Deployment

## Pillars Addressed

### Operational Excellence

Release methods, approvals, and validation steps are core operating mechanisms, not paperwork.

- Source-driven deployment reduces manual variance.
- Checklists and promotion rules make releases repeatable.

### Reliability

Reliable releases depend on realistic validation and credible rollback.

- Explicit sequencing reduces surprise regressions.
- Smoke tests and rollback plans shorten incident duration when things go wrong.

### Security

Permissions, sharing, and integration metadata often ride in deployments and need tighter review than ordinary layout changes.

- High-risk metadata gets explicit scrutiny before promotion.
- Environment-aligned auth and permission handling reduces accidental exposure.

## Pillars Not Addressed

- **User Experience** - this skill improves user outcomes indirectly through safer releases, not through interface design itself.
- **Scalability** - the emphasis is release discipline rather than runtime scale design.

## Official Sources Used

- Salesforce Well-Architected Overview — operational-quality framing for release design
- Metadata API Developer Guide — retrieve and deploy behavior for metadata movement
