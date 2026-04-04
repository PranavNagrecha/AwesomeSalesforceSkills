# Gotchas — Industries CPQ vs Salesforce CPQ

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Industries CPQ License Is Not Included in Sales Cloud or Service Cloud

**What happens:** An architect recommends Industries CPQ for an org that has Sales Cloud Enterprise and OmniStudio enabled. The implementation begins, and the team discovers that Industries CPQ catalog items, Calculation Procedures, and CPQ cart APIs are not accessible. The OmniStudio components (OmniScripts, DataRaptors, FlexCards) are there, but the CPQ-specific objects and APIs are missing.

**When it occurs:** When OmniStudio was licensed as a standalone add-on or via a non-Industries cloud. OmniStudio itself can be licensed separately from Industries clouds. Having OmniStudio does not mean having Industries CPQ. Industries CPQ is part of Communications Cloud, Energy and Utilities Cloud, Media Cloud, and related industry clouds. It is a separate license line item.

**How to avoid:** Before recommending Industries CPQ, confirm the org's Edition and licensed features in Setup > Company Information. Specifically, look for the `Industries CPQ` or the relevant Industry Cloud feature in the org's license list. Do not assume OmniStudio presence implies Industries CPQ access.

---

## Gotcha 2: Salesforce CPQ End-of-Sale Does Not Mean Immediate End-of-Life

**What happens:** A customer panics after reading the March 2025 end-of-sale announcement for Salesforce CPQ and initiates an emergency migration to Revenue Cloud, disrupting an otherwise stable quoting process. The rushed migration introduces data mapping errors in `SBQQ__QuoteLine__c` to `TransactionLineItem` and causes revenue recognition gaps.

**When it occurs:** When practitioners conflate "end-of-sale" (no new licenses sold) with "end-of-life" (product decommissioned). Salesforce CPQ entered end-of-sale in March 2025. Existing customers can still renew their subscriptions and receive support on a defined timeline. Salesforce has not announced a forced sunset date as of Spring '25.

**How to avoid:** Monitor Salesforce's official product lifecycle communications and the Revenue Cloud release notes for end-of-support date announcements. Plan the Revenue Cloud migration in a controlled timeline aligned to a natural business cycle (annual renewal, new fiscal year, major org change) rather than treating end-of-sale as an emergency trigger.

---

## Gotcha 3: Vlocity CPQ DataPacks Use a Namespace Prefix That Breaks on Native OmniStudio Orgs

**What happens:** A team exports DataPacks from a legacy Vlocity CPQ org using the Vlocity Build Tool (VBT) and attempts to deploy them to a new org running native OmniStudio. The deployment fails with schema errors or silent mismatches. OmniScript and FlexCard components that reference `%vlocity_namespace%` in their property sets do not resolve correctly on a native OmniStudio org.

**When it occurs:** Legacy Vlocity implementations (pre-Salesforce acquisition or early post-acquisition) used the `%vlocity_namespace%` token to handle managed-package namespace references. Native OmniStudio does not have a managed-package namespace. DataPacks containing this token require a find-and-replace namespace migration step before deployment to a native org.

**How to avoid:** Before migrating Vlocity CPQ DataPacks to a native OmniStudio org, run a namespace audit on all exported DataPacks. Replace `%vlocity_namespace%` tokens with the native OmniStudio namespace equivalent (typically `omnistudio` or empty string depending on component type). Follow Salesforce's official "Download and Migrate Industries CPQ DataPacks" guide (help.salesforce.com article id: `ind.comms_download_and_migrate_industries_cpq_datapacks_to_salesforce_org`).

---

## Gotcha 4: Industries CPQ Cart Objects Are Not Compatible with Salesforce CPQ Quote Objects

**What happens:** A team running both Industries CPQ and Salesforce CPQ in the same org attempts to build a unified quote report by querying both `SBQQ__Quote__c` and Industries CPQ order/cart objects in the same report. The report fails because these are separate, unrelated Salesforce objects. There is no standard join or relationship between them.

**When it occurs:** In coexistence architectures where both CPQ products serve different business units. Reporting, opportunity pipeline, and revenue forecasting all face this gap because each product stores quote data in different objects.

**How to avoid:** Design a unified CPQ summary object (custom object or external data strategy) at the start of a coexistence architecture. Both quoting flows write a normalized summary record that downstream reporting queries. Accept that native CPQ-to-Industries-CPQ joins are not possible within a single SOQL query.

---

## Gotcha 5: Revenue Cloud Is Not Feature-Complete Relative to Salesforce CPQ Managed Package (As of Spring '25)

**What happens:** A practitioner commits to a hard Revenue Cloud cutover date based on Salesforce's end-of-sale announcement. During gap analysis, they discover that specific Salesforce CPQ capabilities the org relies on — such as partner community quoting, certain legacy billing configurations, or specific Apex plugin hook points — are not yet available in Revenue Cloud.

**When it occurs:** Revenue Cloud (formerly RLM) was launched in March 2024 and is being actively developed. Feature parity with the mature Salesforce CPQ managed package is not complete as of Spring '25. Gaps vary by use case.

**How to avoid:** Before committing to a Revenue Cloud migration timeline, perform a formal feature parity assessment comparing the org's specific Salesforce CPQ feature usage against the current Revenue Cloud feature list in the release notes. Treat any feature listed as "Roadmap" or absent from Revenue Cloud documentation as a migration blocker until Salesforce confirms GA availability.
