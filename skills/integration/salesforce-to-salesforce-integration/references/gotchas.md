# Gotchas — Salesforce-to-Salesforce Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Native S2S Cannot Be Deactivated Once Enabled

**What happens:** Once the Salesforce-to-Salesforce feature is enabled in an org (via Setup > Salesforce to Salesforce), it cannot be disabled. The PartnerNetworkConnection and PartnerNetworkRecordConnection objects remain in the org permanently. There is no "disable" toggle in Setup or via Metadata API. Enabling S2S is a permanent org configuration change.

**When it occurs:** When admins enable S2S for evaluation, proof-of-concept, or accidental click in Setup without understanding the irreversibility.

**How to avoid:** Never enable native S2S without explicit business sign-off that accepts the permanent nature of the feature. Use a developer edition org for evaluation. In production, prefer API-based sync which is fully reversible.

---

## Gotcha 2: Native S2S Consumes SOAP API Call Limits on Both Orgs Simultaneously

**What happens:** Each record share via native S2S counts as a SOAP API call against the daily limit of BOTH the publishing org AND the subscribing org. At high volumes, both orgs' daily API limits are depleted at twice the expected rate. When limits are exceeded, S2S shares fail silently — there is no user-facing error and no automatic retry.

**When it occurs:** When S2S is used at volumes above a few hundred records per day, or when both orgs already have API usage close to their daily limits.

**How to avoid:** Monitor SOAP API usage in both orgs after enabling S2S. For high-volume scenarios, replace S2S with REST API-based sync which uses the REST API limit (not SOAP) and provides explicit error handling.

---

## Gotcha 3: Salesforce Connect External Objects Have SOQL Limitations

**What happens:** External Objects created by Salesforce Connect Cross-Org adapter do not support the full SOQL feature set. Specifically: no OFFSET in queries, limited aggregate functions (COUNT works; SUM/AVG may not), and relationship queries across External Objects are limited. Apex that runs reports or complex queries against External Objects encounters runtime errors.

**When it occurs:** When developers query External Objects using standard Salesforce reporting patterns or SOQL features that work on native objects but are not supported for External Objects backed by OData/Salesforce Connect.

**How to avoid:** Document which SOQL features will be used against External Objects before designing Salesforce Connect as the cross-org access pattern. Test complex queries in a sandbox before committing to this pattern for use cases that need aggregate reporting.
