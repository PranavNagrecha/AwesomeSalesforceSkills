# Well-Architected Notes — API Version Management

## Relevant Pillars

- **Reliability** — API version consistency directly affects runtime behavior predictability. Components on different versions can exhibit subtly different behaviors for the same code, leading to intermittent failures that are difficult to diagnose. Keeping all components at a consistent, current version eliminates an entire class of "works on my machine" reliability issues.
- **Operational Excellence** — Version drift is technical debt that compounds over time. A disciplined version management practice, including CI gates and regular audits, reduces the operational burden of emergency upgrades when retirement deadlines arrive. Proactive version management converts a crisis (forced retirement upgrade) into routine maintenance.
- **Security** — Older API versions may lack security enhancements introduced in newer releases, such as stricter CRUD/FLS enforcement defaults, improved Content-Security-Policy headers, or enhanced guest user restrictions. Running components on the latest version ensures they inherit the platform's current security posture.

## Architectural Tradeoffs

**Consistency vs. Risk:** Upgrading all components to a single version maximizes consistency but increases the blast radius of any version-specific behavior change. Incremental tier-based upgrades reduce risk but temporarily increase the number of active versions in the codebase.

**Currency vs. Subscriber Compatibility:** Managed package ISVs must balance running on the latest version (for security and features) against supporting subscribers on older orgs. The `apiVersion` in a managed package determines the minimum subscriber org version required.

**Currency vs. Record Visibility (the 67.0 boundary):** Raising an Apex class to API version 67.0 or later tightens a platform default — a class with no sharing keyword moves from `without sharing` to `with sharing`. That is the safer posture, but it narrows what the code can see, and the classes most likely to have relied on the old default are the ones whose job is to see everything: roll-up helpers, sharing-recalculation utilities, low-privilege batch jobs. The resolution is not to hold the tier at 66.0. It is to make the intended mode explicit before the bump, which decouples currency from visibility instead of trading one against the other. See Gotcha 6 in `gotchas.md`.

**Automation vs. Manual Review:** CI gates that auto-reject old versions prevent drift but can block legitimate work (e.g., a hotfix to a legacy component that cannot be safely upgraded yet). A threshold-based approach (reject below minimum, warn within tolerance) balances automation with flexibility.

## Anti-Patterns

1. **"Set and forget" sourceApiVersion** — Updating `sfdx-project.json` once and never auditing individual components. This creates a false sense of currency while actual runtime behavior stays on legacy versions. The fix is to pair every `sourceApiVersion` update with a full component audit.

2. **Big-bang version upgrades without test isolation** — Upgrading all 500 components from version 45.0 to 63.0 in a single commit. When tests fail, it is impossible to determine which version jump caused the regression. The fix is tier-based incremental upgrades with test checkpoints.

3. **Ignoring transport API versions in integrations** — Focusing only on metadata component versions while external integrations continue calling `/services/data/v28.0/`. When version 28.0 is retired, the integration breaks instantly. The fix is to include `ApiTotalUsage` event log analysis in every version audit.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce KB 000389618 — "Salesforce Platform API Versions 21.0 through 30.0 Retirement" (deprecated Summer '22, retired Summer '25; REST 410 GONE / SOAP 500 UNSUPPORTED_API_VERSION / Bulk 400 InvalidVersion; verified 2026-08-01) — https://help.salesforce.com/s/articleView?id=000389618&language=en_US&type=1
- Salesforce API End-of-Life Policy — https://help.salesforce.com/s/articleView?id=000381744&type=1
- REST API End-of-Life Policy (REST API Developer Guide) — confirms 7.0–20.0 "retired and unavailable" as of Summer '22 and 21.0–30.0 as of Summer '25, a supported band of "Versions 31.0 through 67.0" with no deprecated-but-serving band beneath it, and that REST "returns the 410:GONE error code" (verified 2026-08-13) — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/api_rest_eol.htm
- SOAP API End-of-Life Policy (SOAP API Developer Guide) — confirms the same two retirement waves and the SOAP-side `500:UNSUPPORTED_API_VERSION` error code (verified 2026-08-13) — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/api_eol_soap.htm
- New Tools to Help Prepare for API Version Retirement (Salesforce Developer Blog, Oct 2024) — confirms the third protocol string, Bulk API "400: InvalidVersion" (verified 2026-08-13) — https://developer.salesforce.com/blogs/2024/10/new-tools-to-help-prepare-for-api-version-retirement
- Using the with sharing, without sharing, and inherited sharing Keywords (Apex Developer Guide) — confirms "In API version 67.0 and later, classes without an explicit sharing declaration run in with sharing mode", the inheritance-chain rule, and that "Apex triggers can't have an explicit sharing declaration" (verified 2026-08-13) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- LWC Component Versioning (Spring '25) — https://developer.salesforce.com/docs/platform/lwc/guide
