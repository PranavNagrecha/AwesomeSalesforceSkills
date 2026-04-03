# Well-Architected Mapping: Sandbox Strategy

## Pillars Addressed

### Operational Excellence

Environment purpose, refresh ownership, and post-refresh runbooks reduce release friction and admin firefighting.

- Clear sandbox roles reduce confusion and rework.
- Repeatable refresh procedures make failures diagnosable.

### Security

Sandbox strategy directly affects whether sensitive data is copied and protected appropriately.

- Masking requirements prevent non-production from becoming a hidden risk surface.
- Environment-specific access review reduces overexposure after refresh.

### Reliability

Testing reliability depends on whether the right environment exists with the right level of parity.

- Full and Partial Copy sandboxes support realistic validation when used deliberately.
- Separation of development and test environments reduces accidental interference.

## Pillars Not Addressed

- **Scalability** - the focus is environment governance rather than runtime scale.
- **User Experience** - this skill improves delivery quality indirectly, not user-facing design directly.

## Official Sources Used

- Salesforce Well-Architected Overview — environment strategy and governance framing
- Metadata API Developer Guide — metadata movement constraints across environments
