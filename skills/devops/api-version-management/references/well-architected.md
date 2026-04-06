# Well-Architected Notes — API Version Management

## Relevant Pillars

- **Reliability** — API version consistency directly affects runtime behavior predictability. Components on different versions can exhibit subtly different behaviors for the same code, leading to intermittent failures that are difficult to diagnose. Keeping all components at a consistent, current version eliminates an entire class of "works on my machine" reliability issues.
- **Operational Excellence** — Version drift is technical debt that compounds over time. A disciplined version management practice, including CI gates and regular audits, reduces the operational burden of emergency upgrades when retirement deadlines arrive. Proactive version management converts a crisis (forced retirement upgrade) into routine maintenance.
- **Security** — Older API versions may lack security enhancements introduced in newer releases, such as stricter CRUD/FLS enforcement defaults, improved Content-Security-Policy headers, or enhanced guest user restrictions. Running components on the latest version ensures they inherit the platform's current security posture.

## Architectural Tradeoffs

**Consistency vs. Risk:** Upgrading all components to a single version maximizes consistency but increases the blast radius of any version-specific behavior change. Incremental tier-based upgrades reduce risk but temporarily increase the number of active versions in the codebase.

**Currency vs. Subscriber Compatibility:** Managed package ISVs must balance running on the latest version (for security and features) against supporting subscribers on older orgs. The `apiVersion` in a managed package determines the minimum subscriber org version required.

**Automation vs. Manual Review:** CI gates that auto-reject old versions prevent drift but can block legitimate work (e.g., a hotfix to a legacy component that cannot be safely upgraded yet). A threshold-based approach (reject below minimum, warn within tolerance) balances automation with flexibility.

## Anti-Patterns

1. **"Set and forget" sourceApiVersion** — Updating `sfdx-project.json` once and never auditing individual components. This creates a false sense of currency while actual runtime behavior stays on legacy versions. The fix is to pair every `sourceApiVersion` update with a full component audit.

2. **Big-bang version upgrades without test isolation** — Upgrading all 500 components from version 45.0 to 63.0 in a single commit. When tests fail, it is impossible to determine which version jump caused the regression. The fix is tier-based incremental upgrades with test checkpoints.

3. **Ignoring transport API versions in integrations** — Focusing only on metadata component versions while external integrations continue calling `/services/data/v28.0/`. When version 28.0 is retired, the integration breaks instantly. The fix is to include `ApiTotalUsage` event log analysis in every version audit.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce API End-of-Life Policy — https://help.salesforce.com/s/articleView?id=000381744&type=1
- Salesforce Developer Blog: API Retirement Tools (Oct 2024) — https://developer.salesforce.com/blogs
- LWC Component Versioning (Spring '25) — https://developer.salesforce.com/docs/platform/lwc/guide
