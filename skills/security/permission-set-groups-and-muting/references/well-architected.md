# Well-Architected Notes - Permission Set Groups And Muting

## Relevant Pillars

- **Security** - least privilege depends on coherent bundles and controlled subtraction.
- **Operational Excellence** - PSGs reduce access-management sprawl only when they are named and governed well.

## Architectural Tradeoffs

- **Direct permission-set assignment vs PSGs:** flexibility versus compositional clarity.
- **Clone a bundle vs mute it:** simpler mental model versus less duplication.
- **Profile-heavy access vs profile-minimized access:** short-term familiarity versus long-term maintainability.

## Anti-Patterns

1. **Junk-drawer PSGs** - unrelated access grouped without a clear purpose.
2. **Muting as cleanup for bad design** - subtraction should not replace modeling.
3. **Profile-heavy org with token PSG adoption** - complexity increases without real governance gain.

## Official Sources Used

- Metadata API Developer Guide, Summer '26 (release 262): PermissionSetGroup (fields, `status`, `hasActivationRequired`, retrieve PermissionSet with the group, package.xml sample), MutingPermissionSet ("settings enabled by MutingPermissionSet are turned off"), PermissionSet (API 40.0+ full-content deploy) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference, Summer '26: PermissionSetGroup (`Status` values, aggregate ObjectPermissions query), PermissionSetGroupComponent (recalculation), MutingPermissionSet, FieldPermissions > Muting Permissions, PermissionSetAssignment (`ExpirationDate`), PermissionSet (`IsOwnedByProfile`, `PermissionSetGroupId`, `Type`) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce Security Guide, Summer '26: Revoke Permissions and Access (grants are additive; muting permission sets in PSGs), Object Permissions, record type assignment through permission sets and PSGs - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf
- Salesforce CLI 2.151.7 source-deploy-retrieve metadata registry (`permissionsetgroups`, `mutingpermissionsets` directory and suffix names), local install at /usr/local/lib/sf/node_modules/@salesforce/source-deploy-retrieve/lib/src/registry/metadataRegistry.json
