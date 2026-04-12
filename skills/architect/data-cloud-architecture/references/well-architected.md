# Well-Architected Notes — Data Cloud Architecture

## Relevant Pillars

- **Trust & Reliability** — Identity resolution correctness is a trust problem: a Unified Individual that incorrectly merges two distinct people (false positive) or fails to merge the same person across sources (false negative) produces unreliable personalization and segmentation outcomes. Reconciliation rule design directly determines whether the golden profile is trustworthy. Data quality gates before identity resolution runs protect the reliability of downstream activation.

- **Adaptability** — The data lakehouse layer design (DSO → DLO → DMO) separates raw ingestion from harmonization, which allows new sources to be onboarded without disrupting existing identity clusters. Adding a new source only requires mapping its DLO to the existing canonical DMOs — it does not require re-architecting the identity resolution ruleset. This composable design is the core adaptability property of the architecture.

- **Performance** — Calculated Insight batch lag and Streaming Insight near-real-time processing are directly performance concerns for activation use cases. Choosing the wrong insight type for a time-sensitive segment causes the activation to underperform relative to its intent. Activation target pre-flight eliminates unnecessary re-activation retries, which add latency to go-live.

## Architectural Tradeoffs

### Precision vs Recall in Match Rules

Higher-precision match rules (exact email match) minimize false identity merges but miss individuals who appear in some sources without an email address. Lower-precision rules (fuzzy name, compound name+address) increase recall but introduce false merges. The tradeoff must be calibrated per deployment:

- **B2C consumer retail:** High record volume, high email capture rate → anchor on exact email, accept lower recall for email-less records rather than introduce false merges.
- **B2B:** Multiple contacts at the same company share similar names and addresses → be conservative with compound match rules; prefer loyalty or account IDs as secondary identifiers.
- **Loyalty-first retail:** Loyalty ID is a high-precision identifier and should be the primary match anchor even over email, since customers may share household email addresses.

### Batch Calculated Insights vs Streaming Insights

Calculated Insights are operationally simpler and cover a wider range of aggregate calculations, but they introduce lag. Streaming Insights are near-real-time but more complex to configure and have a smaller supported calculation surface. The tradeoff is: operational simplicity + batch lag vs. operational complexity + near-real-time freshness. Choose based on the activation use case's time-sensitivity requirement, not based on what is easier to build.

### File-Based vs Platform-Native Activation

File-based activation (SFTP, S3) is more flexible and works with any downstream system, but introduces an additional file processing step that the receiving system must handle. Platform-native activation (Marketing Cloud, CRM Core) is tighter and removes the intermediate step, but requires the receiving platform to be correctly configured to consume the segment data. For Salesforce-to-Salesforce activation, platform-native is preferred; for third-party systems, file-based is often the only option.

## Anti-Patterns

1. **Mapping email to Individual DMO instead of ContactPointEmail DMO** — The `Individual` DMO is a profile container, not a link entity. Identity resolution operates on ContactPointEmail, ContactPointPhone, and PartyIdentification. Mapping email to `Individual.email` bypasses the resolution engine entirely. This is the single most common architecture error in Data Cloud implementations and is completely silent — ingestion succeeds, but the person never appears in a Unified Individual.

2. **Deferring activation target authentication to go-live day** — Activation target authentication requires platform-side configuration (OAuth consent flows, API key validation, SFTP write permission verification). These steps require access to external systems that may have approval workflows or change management requirements. Treating them as a day-of task creates a failure point that cannot be resolved quickly under go-live pressure. Activation target setup should be a prerequisite to segment build, not a step after it.

3. **Using Calculated Insights as real-time segment filters without documenting lag** — A segment filtered on a CI attribute with a 4-hour batch schedule will silently deliver stale audience data. If the activation channel is a paid ad platform, this translates directly to wasted spend on stale audiences. Every Calculated Insight used in a production segment should have its refresh schedule explicitly documented and communicated to the campaign owner.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Data 360 Architecture — Salesforce Architects — https://architect.salesforce.com/
- Data Cloud Architecture Strategy — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud.htm
- Activation Targets in Data Cloud — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.c360_a_activation_targets.htm
- Building a Complete View with Data Cloud and Identity Resolution — Salesforce Developers Blog — https://developer.salesforce.com/blogs/
