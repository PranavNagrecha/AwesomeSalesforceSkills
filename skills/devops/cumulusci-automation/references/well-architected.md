# Well-Architected Notes — CumulusCI Automation

## Relevant Pillars

- **Operational Excellence** — CumulusCI is a direct enabler of operational excellence in Salesforce development. The `cumulusci.yml` authoring model enforces that all environment setup, deployment, and testing steps are version-controlled, repeatable, and self-documenting. Standard flows provide baseline procedures that teams can extend rather than build from scratch, reducing operational drift between team members.

- **Reliability** — Flow composition with ordered, numbered steps creates deterministic execution: the same flow produces the same result regardless of who runs it or when. The `when:` condition system prevents tasks from running in invalid contexts. JWT-based authentication removes fragile refresh-token dependencies from CI pipelines.

- **Security** — JWT authentication with a Connected App and certificate eliminates the need for stored user credentials or SFDX auth URLs in CI secrets. The private key is the only credential required, and it authorizes only the operations permitted by the Connected App. Limiting the Connected App's OAuth scopes to the minimum needed for CI reduces blast radius if the key is compromised.

- **Scalability** — CumulusCI's cross-project `sources:` system allows large organizations to centralize shared automation (common configuration flows, shared datasets, org setup patterns) in a single repo and consume them across dozens of projects. This scales governance of automation standards without requiring every team to maintain redundant logic.

- **Performance** — Flow composition allows expensive steps (package install, large dataset load) to be conditionally included or excluded via `when:` guards, keeping developer-facing flows fast while CI flows run the full suite. Caching the CumulusCI home directory in CI pipelines avoids repeated source downloads and keychain initialization.

## Architectural Tradeoffs

**Standard flows vs. custom flows from scratch:** Extending standard flows keeps the project on CumulusCI's upgrade path; custom flows from scratch own all maintenance burden. Prefer extension unless the standard flow's assumptions are fundamentally incompatible with the project (rare).

**Inline `when:` conditions vs. separate task variants:** Using `when:` in flow steps keeps the flow definition concise but makes behavior harder to reason about. Separate named task variants in the `tasks:` block are more explicit and testable. Use `when:` for genuinely conditional logic (e.g., "only run if package is installed"); use named variants for consistently different option sets.

**Cross-project sources with `release: latest` vs. pinned tags:** `release: latest` always pulls the newest automation code, which is convenient but introduces silent behavior changes when the source repo releases a new version. Pinning to a tag makes builds reproducible and introduces changes deliberately. Production CI pipelines should always pin; developer convenience flows may use `latest`.

## Anti-Patterns

1. **Maintaining a full custom flow copy instead of extending the standard** — Teams sometimes copy the entire `dev_org` flow definition into `cumulusci.yml` to avoid having to understand step numbering. This means they never benefit from CumulusCI upgrades to the standard flow, and the custom copy drifts. Extend the standard flow with fractional step numbers instead.

2. **Using SFDX auth URLs as CI secrets for production orgs** — Auth URLs embed refresh tokens tied to a user session. They expire, cannot be scoped to CI-only operations, and if leaked provide persistent access until revoked. JWT with a Connected App scoped to `api` and `web` is the correct long-term authentication pattern for CI pipelines.

3. **Omitting `cci flow info` validation after editing** — Because CumulusCI merges standard and project flows at runtime, it is not possible to see the effective step order from `cumulusci.yml` alone. Skipping `cci flow info` validation means step collisions and accidental step replacements are discovered only when the flow fails at runtime.

## Official Sources Used

- CumulusCI Documentation — Key Concepts — https://cumulusci.readthedocs.io/en/stable/concepts.html
- CumulusCI Documentation — Configuring Tasks and Flows — https://cumulusci.readthedocs.io/en/stable/config.html
- CumulusCI Documentation — Standard Flows Reference — https://cumulusci.readthedocs.io/en/stable/flows.html
- CumulusCI Documentation — Robot Framework Integration — https://cumulusci.readthedocs.io/en/stable/robot.html
- CumulusCI Documentation — Cross-Project Sources — https://cumulusci.readthedocs.io/en/stable/sources.html
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce CLI Reference — sf org login jwt — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_org_commands_unified.htm
