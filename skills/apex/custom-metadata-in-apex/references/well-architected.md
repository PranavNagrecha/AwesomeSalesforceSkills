# Well-Architected Notes - Custom Metadata In Apex

## Relevant Pillars

- **Reliability** - configuration should be versioned, predictable, and not depend on accidental org state.
- **Operational Excellence** - teams should know where config is read, how it is promoted, and who owns changes.

## Architectural Tradeoffs

- **CMT vs Custom Settings:** deployable versioned configuration versus older runtime-oriented patterns.
- **Direct queries vs reader service:** faster initial coding versus clearer ownership and testability.
- **Subscriber freedom vs package protection:** easier local edits versus stronger publisher control. `fieldManageability` makes this per-field and irreversible in one direction: a `SubscriberControlled` field "can't be updated with a package upgrade" (Metadata API Developer Guide L43406–43413).
- **Cache accessor vs SOQL:** `getAll()` / `getInstance()` read the application cache but truncate every field at 255 characters; SOQL returns the full value and costs nothing against the query limit (Apex Reference Guide L204569–204572, Apex Developer Guide L19616–19619). The trade is convenience against correctness on long values, not performance.
- **Read-only config vs an Apex write path:** adding `Metadata.Operations.enqueueDeployment` buys self-service configuration and costs an asynchronous job, a callback class, a partial-success branch, and a delay before the new value is live (Apex Developer Guide L28194–28196, L28226–28229).

## Anti-Patterns

1. **Treating `__mdt` like ordinary `__c` data** - the read/write model is different.
2. **Hidden org-metadata dependency in tests** - green tests with brittle assumptions.
3. **Using labels for structured configuration** - text storage is not rule architecture.
4. **`protected` records outside a managed package** - they are readable by every profile including guest, so they are not a secret store (Apex Reference Guide L170826–170832).
5. **Reading a deployed value back in the transaction that deployed it** - the write is queued, and the callback lags even the deployment (Apex Reference Guide L171091–171094).

## Official Sources Used

- **Apex Reference Guide — Custom Metadata Type Methods** (`getAll()`, `getInstance(recordId | developerName | qualifiedApiName)`), L204513–204681 — the read API surface, the "empty map when no records" behaviour, the "returns null if no record matches" contract, and the 255-character truncation that Gotcha 4 and Anti-Pattern 1 rest on. https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_custom_metadata_types.htm
- **Apex Reference Guide — `Metadata` namespace** (`CustomMetadata`, `CustomMetadataValue`, `DeployContainer`, `DeployCallback`, `DeployCallbackContext`, `DeployResult`, `DeployDetails`, `DeployMessage`, `DeployStatus`, `Operations`), L170824–174200 — every class, property, and enum value used by the deployer and callback in `references/code-examples.md` §§ 5–7, including the `SucceededPartial` status (Gotcha 5), the duplicate-`fullName` warning (Gotcha 7), and the "relationship values are API names, not Ids" rule (Gotcha 10). https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_namespace_Metadata.htm
- **Apex Developer Guide — Retrieving and Deploying Metadata / Security Considerations / Testing Metadata Deployments**, L28186–28262 — the asynchronous write path, the namespace-qualified full name, the "create and update but not delete" restriction, the asynchronous-job accounting, and the guide's own `TestingDeployCallbackContext` pattern that `RetryPolicyDeployerTest` copies. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — Execution Governors and Limits, footnote 1**, L19614–19619 — "This limit doesn't apply to custom metadata types. In a single Apex transaction, custom metadata records can have unlimited SOQL queries." The claim that the SOQL path is free rests on exactly this sentence. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — Isolation of Test Data from Organization Data / Custom Settings / TestVisible Annotation**, L6290–6296, L13515–13526, L40700–40740 — why tests see custom metadata but not custom settings data, and the `@TestVisible` contract behind the injection seam in `references/code-examples.md` § 4. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Metadata API Developer Guide — Custom Metadata Types (CustomObject) and CustomMetadata**, L41296–41760 and L43406–43420 — the `visibility` enum, the per-record `protected` flag, the Special Access Rules that forbid DML, `fieldManageability`, the declarative sample definitions the XML in `references/code-examples.md` §§ 1–2 is shaped from, the `xsi:type` table, and the "an omitted field is not a cleared field" rule (Gotcha 8). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Object Reference for the Salesforce Platform — `Custom Metadata Type__mdt`**, L5661–5760 — the supported calls (`describeSObjects, describeLayout, query, retrieve` and nothing else), and the `DeveloperName` / `QualifiedApiName` / `isProtected` field semantics behind the "never assign DeveloperName in a test" rule. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Salesforce App Limits Cheat Sheet**, L120–137 and L760–764 — checked for a custom metadata storage or record-count limit; it carries the same "unlimited SOQL queries on custom metadata" footnote and a 10 MB *zip file* limit for Metadata API deployments, and no `DeployContainer` cap. This is the negative source behind the UNVERIFIED marker in `references/llm-anti-patterns.md` Anti-Pattern 6. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- **Salesforce Well-Architected — Overview** — the Reliability and Operational Excellence framing for "configuration is part of the release, not part of the data". https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

Line numbers refer to the plain-text extraction of the Summer '26 (v62 / API 66–67) PDFs
listed above; quotes are verbatim from those files.
