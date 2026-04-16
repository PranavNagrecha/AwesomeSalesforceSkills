# Well-Architected Notes — Managed Package Development

## Relevant Pillars

### Operational Excellence

1GP managed package development is a highly constrained discipline. Many decisions (namespace, class names, included Flows) are irreversible after the first Released upload. Operational excellence requires treating pre-release reviews as schema-lock events and maintaining documented package component registries.

### Security

Packages installed in subscriber orgs run under the package's namespace with the subscriber org's governor limits. The PostInstall script runs as Automated Process user. ISVs must ensure PostInstall scripts do not store sensitive data, do not expose subscriber data to the ISV, and comply with the AppExchange security review requirements.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Operational Excellence | Pre-release review as schema-lock event; patch org registry documentation |
| Security | AppExchange Security Review compliance; PostInstall script runs as Automated Process user |
| Reliability | PostInstall governor limits apply in subscriber org; use Queueable for large installs |
| Performance | Push upgrade impact on subscriber orgs; schedule during low-traffic windows |

---

## Cross-Skill References

- `devops/second-generation-managed-packages` — For 2GP managed packages with CLI-driven workflow
- `devops/package-development-strategy` — For package type selection (1GP vs 2GP vs unlocked)
- `devops/cpq-deployment-patterns` — For deploying CPQ configuration alongside managed packages

---

## Official Sources Used

- First-Generation Managed Packaging Developer Guide v66.0 — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/sharing_apps.htm
- Run Apex on Package Install/Upgrade — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/apex_post_install_script.htm
- ISVforce Guide v66.0 — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/packaging_intro.htm
