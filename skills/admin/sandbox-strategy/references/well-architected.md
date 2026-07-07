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

- Salesforce Well-Architected Overview — environment strategy and governance framing (https://architect.salesforce.com/well-architected/trusted/overview)
- Metadata API Developer Guide — metadata movement constraints across environments
- Sandbox Types and Templates (Salesforce Help, platform.data_sandbox_environments) — storage sizes, storage-upgrade options, refresh intervals, and per-edition sandbox license entitlements (https://help.salesforce.com/s/articleView?id=platform.data_sandbox_environments.htm&language=en_US&type=5)
- Sandbox Refresh Intervals (Salesforce Help, article 000387743) — daily/5-day/29-day refresh windows and sequential (in-series) processing of concurrent refresh requests (https://help.salesforce.com/s/articleView?id=000387743&language=en_US&type=1)
- Partial Copy Sandbox — template prerequisite and external-user record exclusion (Salesforce Help, article 000381868) (https://help.salesforce.com/s/articleView?id=000381868&language=en_US&type=1)
- Sandbox License Consumption (Salesforce Help, article 000385966) — higher-tier license substitutes for a lower sandbox type when the lower pool is exhausted (https://help.salesforce.com/s/articleView?id=000385966&language=en_US&type=1)
