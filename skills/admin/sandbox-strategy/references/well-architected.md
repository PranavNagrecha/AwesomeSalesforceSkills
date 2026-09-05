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
- Apex Reference Guide — `SandboxPostCopy Interface`: the `runApexClass(System.SandboxContext)` signature, the no-arg constructor requirement, and the statement that the class runs under an invisible Automated Process user without access to all objects and features (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf)
- Apex Reference Guide — `Test.testSandboxPostCopyScript()`: both overloads, and Salesforce's recommendation to use the five-argument form with `RunAsAutoProcUser = true` so the test runs under post-copy permissions (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf)
- Apex Developer Guide — "Enforce Object and Field Permissions" and "Set an Access Mode for Database Operations": user mode as the DML default, the `as system` / `AccessLevel.SYSTEM_MODE` escape, the API 67.0 versioned behaviour change, and the Automated Process user's inability to perform object/FLS checks without explicit permission sets (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf)
- Metadata API Developer Guide — `SandboxSettings` and `Settings`: the `Sandbox.settings` file location, `disableSandboxExpirationEmails` and the 180-day inactivity deletion notice, and the `<members>Sandbox</members><name>Settings</name>` manifest form (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)
- Metadata API Developer Guide — "Run the Same Tests in Sandbox and Production Deployments" and "Maintaining User References": no tests run by default on a non-production deploy, `RunLocalTests` enforcement, the sandbox username suffix rule, and the deployment halt on an unresolvable username (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)
- Salesforce Developer Limits and Allocations Quick Reference — the Full Sandbox 5,000,000-call allocation and its template exclusion, the 25 concurrent long-running requests shared by production and sandboxes, the sandbox/production split in the daily test-class queue ceiling, and the exclusion of sandboxes from over-limit grace (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf)
- REST API Developer Guide — the Tooling API base path `/services/data/vXX.X/tooling`, the sObject Basic Information create/response shape used for `SandboxInfo`, and the `MyDomainName--SandboxName.sandbox.my.salesforce.com` sandbox login URL (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf)

**Not consulted for this pass:** the Tooling API Developer Guide. `SandboxInfo` and `SandboxProcess` are Tooling API objects and are not documented in the Object Reference, Metadata API, REST API, or Apex guides beyond the cross-reference on the `SandboxPostCopy` page. Field-level claims about those two objects in `references/metadata-examples.md` Part 3 are marked UNVERIFIED for that reason.
