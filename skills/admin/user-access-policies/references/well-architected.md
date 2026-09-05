# Well-Architected Notes — User Access Policies

## Relevant Pillars

### Security

User Access Policies are a direct implementation of least privilege. Tying assignment to user attributes means users receive the access appropriate to their current profile, role, or department, and lose it when those attributes change. This removes a class of stale-access findings that manual provisioning routinely leaves behind.

What makes it auditable rather than merely automated is the provenance record. When user access policies are enabled, `PermissionSetAssignment` carries `IsRevoked`, `LastCreatedByChangeId`, and `LastDeletedByChangeId`, the last two pointing at `UserAccessChange` rows whose `Source` names what caused the change. An access review can therefore separate policy-driven grants from human ones on the assignment row itself, rather than reconciling a permission snapshot against a Setup Audit Trail export. Design for this: if the audit question is "prove no human granted this", the answer has to be a query written before go-live.

### Operational Excellence

UAP removes manual provisioning steps from onboarding and transfer checklists and makes the provisioning rule inspectable in Setup without reading code. The rules are metadata (`UserAccessPolicy`, suffix `.useraccesspolicy`), so they version-control and deploy with everything else.

The operational cost is the activation seam. A policy deployed with status `Active` arrives as `Design`, so every release that ships a policy needs a named owner and a Setup step after the deployment. Pipelines that treat a green deploy as done will ship dead policies.

## Architectural Tradeoffs

**UAP vs. Apex triggers.** UAP covers attribute-based provisioning where the criteria are user attributes: profile, role, group or licence membership, or any user field via `type` `User`. Its filter language is more expressive than it is usually credited for — `booleanFilter` supports `OR` as well as `AND`, and `operation` `in` matches several profiles or roles in one row. Apex remains necessary where the decision needs cross-object traversal, computed values, or conditional branching, none of which the filter schema expresses. The two should not overlap: running both leaves two independent writers of the same assignment rows with no defined ordering.

**Expressiveness inside a policy vs. arbitration between policies.** This is the central design tension. Salesforce gives a rich filter language *within* a policy and exactly one lever *between* policies: `order`, an int 0–10,000, where only the active policy with the lowest value is applied. Matching is single-winner, not additive. Every population you split across two policies buys arbitration you then have to reason about; every population you keep in one policy costs filter complexity but nothing at evaluation time. Prefer expressiveness inside a policy — `OR`, `in` — and reserve multiple policies for populations that genuinely need different action sets.

**Read-only at runtime.** `UserAccessPolicy` supports only `describeSObjects()`, `query()`, and `retrieve()`. There is no create/update path over the API, no REST resource, and no Apex surface. Policies are a deployed artifact, not runtime-tunable state — which is good for change control and means an incident cannot be resolved by a quick data fix.

## Anti-Patterns

1. **Fanning one population out into several policies to fake OR.** The premise is wrong — `booleanFilter` supports `OR` and `operation` `in` matches multiple values in one row — and the workaround is worse than the problem, because the resulting policies compete on `order` and only one of them ever runs for an overlapping user.

2. **Adding a narrow policy on top of a broad one without auditing what it suppresses.** A lower-`order` policy does not layer over the baseline; it replaces it. Everything the outranked policy was granting has to be repeated in the winner. Keep a register of active policies, their `order` values, the criteria they match, and the actions they contribute, and consult it before adding a policy.

3. **Running UAP and an Apex trigger in parallel for the same users.** The two mechanisms are not coordinated by the platform, and the final state belongs to whichever wrote last. Treat UAP adoption as a cutover — deactivate the trigger in the release that activates the policy — not as an additive step. Note that this is a contested-state problem, not the `MIXED_DML_OPERATION` exception, which is about setup and non-setup DML inside a single transaction.

4. **Relying on activation for bulk remediation.** `triggerType` is event-based — `Create`, `Update`, or `CreateAndUpdate` — so a user who already matches and is not subsequently touched is not evaluated. Use UAP for ongoing governance and a separate one-time operation for the existing population.

## Official Sources Used

- Metadata API Developer Guide — `UserAccessPolicy` field table (`booleanFilter` supporting `1 AND 2` or `1 OR 2`; `order` as an int 0–10,000 where only the lowest-value active policy applies; `status` deployed as `Active` being changed to `Design`; `triggerType` enum; file suffix `.useraccesspolicy` and API version 57.0+; Manage User Access Policies special access rule): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `UserAccessPolicyAction` and `UserAccessPolicyFilter` child types plus their enumerations (`Grant`/`Revoke` as actions on one policy; the six action target types; the nine filter target types; `operation` values and their API-version gates; the `in` operator for multiple profiles or roles; the two sample definitions and the wildcard package.xml): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `UserManagementSettings` (`userAccessPoliciesEnabled` at API v58.0+ as the master switch; `enableEnhcUiUserAccessPolicies` at v60.0+ auto-setting to true and being reversible): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — `UserAccessPolicy` standard object (supported calls limited to `describeSObjects()`, `query()`, `retrieve()`; `Status` default `Design`; `Order` field description) and `UserAccessChange` (read-only calls, `Source` field, View Setup and Configuration): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference for the Salesforce Platform — `PermissionSetAssignment` (`IsRevoked`, `LastCreatedByChangeId`, `LastDeletedByChangeId` available only when user access policies are enabled), `GroupMember` (public-group membership, and its note naming user access policies in Setup), `QueueSobject` (queue-to-object mapping, not membership): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Developer Guide — "sObjects That Can't Be Used Together in DML Operations" (the setup-object list and the same-transaction scope of `MIXED_DML_OPERATION`; the "assign permission sets in a future method" guidance): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
