# Well-Architected Mapping: Data Import and Management

## Pillars Addressed

### Reliability

Good load design prevents duplicates, broken relationships, and partial cutovers.

- External IDs and upsert design preserve identity across reruns.
- Reconciliation steps catch silent failures before users depend on bad data.

### Scalability

Bulk tooling and batch design determine whether a load works at real production volume.

- Bulk API and chunking patterns prevent admin tooling from becoming the bottleneck.
- Load-order design reduces lock contention and failed retries.

### Operational Excellence

Runbooks, rollback plans, and rehearsals separate controlled migrations from heroic recovery work.

- Clear cutover ownership and checkpointing make failures diagnosable.
- Explicit automation and duplicate-rule handling reduce surprise during release windows.

## Pillars Not Addressed

- **Security** - this skill touches permissions only as a prerequisite for running loads, not as a security-design pattern.
- **User Experience** - the concern here is cutover safety, not end-user page behavior.

## Official Sources Used

- Salesforce Well-Architected Overview — reliability framing for large data change plans
- Object Reference — object semantics and relationships that affect load design
- REST API Developer Guide — API-oriented load and integration behavior context
