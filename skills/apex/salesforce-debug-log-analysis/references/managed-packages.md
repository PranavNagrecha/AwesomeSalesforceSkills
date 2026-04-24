# Managed Packages: Extended Catalog

When you see `ENTERING_MANAGED_PKG|<namespace>` in a log, the namespace tells you which ISV package is running. You cannot see inside managed package code (by design), so you infer behavior from the surrounding events: what SOQL it runs, what DML it produces, what fields it writes, what errors it catches.

This reference covers 50+ packages grouped by function.

## Data quality and duplicate management

### TracRTC (Traction Complete / Validity Realtime Clean)
Namespace: `TracRTC`

Function: realtime merge and cleanup of duplicate Contacts and Leads. More aggressive than Salesforce Duplicate Rules.

Signatures:
- SOQL on `TracRTC__Flow__c`, `TracRTC__Flow_Step__c`, `TracRTC__Response_Settings__c`, `TracRTC__ReRun_Complete_Criteria__c`, `TracRTC__Trigger_Handler__c`
- `Op:Merge|Type:Contact|Rows:1` at line 286 of the managed class (stable line number)
- Fields written: `TracRTC__Realtime_Clean_Processed__c`, `TracRTC__Realtime_Clean_Failed__c`, `TracRTC__Realtime_Clean_Error_Message__c`, `TracRTC__Date_of_Last_Completion__c`, `TracRTC__Original_Completion_Date__c`, `TracRTC__Time_of_Last_Auto_Merge__c`

Gotchas:
- Respects `TracRTC__Disable_Complete__c = true` to skip a record. Use to stop retry loops.
- Error messages are sanitized. Raw Salesforce error has more detail.
- Retries every 10 to 60 seconds on failed merges until disabled or succeeds.
- `LAM_5` in error = "List Auto Merge" step 5, internal label.

### Cloudingo
Namespace: `cldg`, `cldghub`

Function: dedup and merge at scale, realtime and batch.

Signatures: SOQL on `cldg__*` custom objects, agent user with View All Data.

### DupeCatcher
Namespace: `dupcatcher` or `DemandTools`

Function: dedup prevention and cleanup. DemandTools is the heavier cousin.

### RingLead / DemandCloud
Namespace: `rlmkto`, `rlctc`, `rlmr`

Function: data orchestration, dedup, enrichment.

### Data.com Clean (legacy)
Namespace: `DatacomClean`

Function: contact/account enrichment. Mostly retired.

## Rollups and field calculation

### Declarative Lookup Rollup Summaries (DLRS)
Namespace: `dlrs` (open-source, by Andy Fawcett)

Function: rollup summaries without requiring master-detail relationships.

Signatures:
- Triggers: `dlrs_<Object>Trigger on <Object> trigger event BeforeUpdate/AfterUpdate`
- Entry point Apex class: `dlrs.RollupService.triggerHandler()`
- SOQL on `dlrs__LookupRollupSummary2__mdt`, `dlrs__LookupRollupCalculateJob__c`

Gotchas:
- Fires in BOTH before and after update. One DML = two DLRS passes on the parent.
- Heavy orgs have dozens of rollups; SOQL count can explode.
- When child criteria change frequently, parent rollup flip-flops.

### Native Roll-Up Summary
Not managed. Master-detail only. Recalculated by the platform. No log event for the calculation; values appear in before/after record dumps.

## Marketing automation

### Pardot (Salesforce Marketing Cloud Account Engagement)
Namespace: `pi`

Function: B2B marketing automation, scoring, journeys.

Signatures:
- SOQL on `pi__*` objects: `pi__Tracker_Domain__c`, `pi__Campaign__c`
- Fields on Lead/Contact: `pi__score__c`, `pi__grade__c`, `pi__Pardot_Last_Scored_At__c`, `pi__conversion_date__c`
- Integration user ownership.

### Marketo Sales Insight
Namespace: `mkto_si`

Function: display Marketo scoring in SF, without writing.

Signatures:
- Fields on Lead/Contact: `mkto_si__Mkto_Lead_Score__c`, `mkto_si__Priority__c`, `mkto_si__Relative_Score_Value__c`, `mkto_si__Sales_Insight__c`
- Formula fields contain image URLs pointing to `s3.amazonaws.com/marketo-sales-insight/`.

### Marketo Sync
Namespace: `mkto` (separate from mkto_si)

Function: actual sync between Marketo and SF.

Signatures:
- Integration user `Marketo` running a scheduled sync.
- DML on Leads/Contacts updating `mkto__Inferred_Company__c`, `mkto__Lead_Source_Most_Recent__c`, etc.

### HubSpot
Namespace: `hs_sales`, `hs2` (depending on version)

Function: HubSpot CRM sync.

### Eloqua
Namespace: `Eloqua`

Function: Oracle Marketing Cloud sync.

## Email and deliverability

### Validity Verify (formerly BriteVerify)
Namespace: `Validity_Verify`

Function: email verification.

Signatures:
- Fields: `Validity_Verify__Checked__c`, `Validity_Verify__Status__c`, `Validity_Verify__Timestamp__c`
- Only writes to three fields. Narrow footprint.

### Return Path / 250ok
Namespace varies. Look for `returnpath` or `validity`.

## Document generation and e-signature

### DocuSign for Salesforce
Namespace: `dsfs`

Function: e-signature.

Signatures:
- SOQL on `dsfs__DocuSign_Status__c`, `dsfs__DocuSign_Recipient_Status__c`
- Apex class: `dsfs.DocuSign_API.sendNow()`

### DocuSign CLM (formerly SpringCM)
Namespace: `SpringCM`

### Conga Composer
Namespace varies; often `APXTConga4` (Conga4) or `Conga`

Function: document generation.

Signatures:
- Fields contain URL parameters with `solmgr=1`, `csvisible=1`, `qmode=congasign`, `emailfromid=`
- Apex classes invoke Conga APIs.

### Conga Sign
Namespace: `congasign`

### PandaDoc
Namespace: `pd_connect` or `PandaDoc`

### Adobe Sign (formerly EchoSign)
Namespace: `echosign_dev1`

Signatures: SOQL on `echosign_dev1__SIGN_Agreement__c`.

### FormAssembly
Namespace: `formassembly`

### FormStack
Namespace: `formstack_ent`

## Scheduling

### SUMO Scheduler (FastSlow)
Namespace: `sumoapp`

Function: appointment scheduling.

Signatures: `sumoapp__IsGhost__c`, `sumoapp__CreatedBySumo__c`, `sumoapp__TextOptIn__c`, URLs containing `excelsior.my.site.com/s/onlinescheduler`.

### Calendly
Namespace: `calendly` or connected via integration user.

### Time Trade
Namespace: `ttsf`

## SMS and messaging

### SMS-Magic Interact
Namespace: `smagicinteract`

Function: SMS integration.

Signatures:
- Fields: `smagicinteract__SMSOptOut__c`, `smagicinteract__IncomingMessage_Unread__c`
- Custom objects for messaging history.

### Twilio (various packages)
Namespace varies (`twilio`, `twilio_sms`).

### Salesforce Messaging for In-App and Web
Native, no namespace.

## Higher education

### Education Data Architecture (EDA)
Namespace: `hed` (Salesforce, free)

Function: data model for higher ed. Extends Contact, Account, etc.

Signatures:
- Many `hed__*` fields on Contact, Account, Lead.
- Apex triggers `hed.*` dispatched via custom metadata.
- Household management creates `hed__Household__c` records.

Gotchas: Contact triggers can update Account (household) records, cascading surprise updates.

### Traction Rec
Namespace: `traa`

Function: higher-ed recruiting and application lifecycle on top of EDA.

Signatures:
- Opportunity is the Application object.
- `traa_Applicant__c` lookup on Opportunity points to Contact.
- Custom metadata: `traa_Status_Processor_Rule__mdt`, `traa_Opportunity_Stage__mdt`, `traa_Opportunity_Enrollment_Record_Types__mdt`.

### Salesforce for Higher Education (SFHE) / Target X
Namespace: `sfhe`, `targetx`

### Liaison TX (TargetX Recruitment Suite)
Namespace: `targetx_eventsb`, `targetx_mark`, `targetx_srmb`

## Nonprofit

### Nonprofit Success Pack (NPSP)
Namespace: `npe01`, `npo02`, `npsp`

Function: nonprofit data model, donations, households.

Signatures: many `npsp__*` and `npe01__*` fields.

### Engagement Plan / Volunteer for Salesforce
Namespaces: `npe03`, `V4S`.

## Financial services

### Financial Services Cloud
Namespace: `FinServ`

Function: wealth management, insurance, banking data model.

Signatures:
- `FinServ__*` fields and objects: `FinServ__FinancialAccount__c`, `FinServ__Household__c`.
- Custom triggers on `FinServ__FinancialAccount__c`.

### nCino (commercial lending)
Namespace: `ncino` (plus add-ons like `ncp`)

Function: banking and lending.

Signatures: `ncino__*` fields, LLC (Loan Life Cycle) objects.

### FinancialForce (now Certinia)
Namespace: `c2g` (accounting), `ffintranet`, `pse` (services), `ffscpq`

### Rootstock ERP
Namespace: `rstk`

### FinancialForce HCM (now HCM)
Namespace: `fHCM2`

## Sales and CPQ

### Salesforce CPQ (Steelbrick)
Namespace: `SBQQ`

Function: Configure-Price-Quote.

Signatures:
- `SBQQ__Quote__c`, `SBQQ__QuoteLine__c`, `SBQQ__Subscription__c`
- Apex class `SBQQ.QuoteCalculator`
- Calculation service triggers update Quote totals, pricing, MDQ, discounts.

Gotchas: CPQ does heavy computation on Quote Line edit. Save time can be long. Calculator errors appear as `SBQQ__SBAA__Approval__c` related.

### Salesforce Billing
Namespace: `blng`

Function: subscription billing on top of CPQ.

### Apttus CPQ / Contract Management (now Conga CPQ)
Namespace: `Apttus_Config2`, `Apttus`, `Apttus_CMConfig`

### Vlocity / Salesforce Industries (OmniStudio)
Namespaces: `vlocity_cmt` (Communications), `vlocity_ins` (Insurance), `vlocity_ps` (Public Sector), `vlocity_u` (Utilities), `vlocity_h` (Health)

Function: industry CPQ, product catalog, OmniScripts, FlexCards.

Signatures:
- OmniScript invocations: `CODE_UNIT_STARTED|[EventService.....apex]|vlocity_cmt.OmniScript.<method>`
- Data Raptors: `vlocity_cmt.DRRunnerImpl.run`
- Many custom objects: `vlocity_cmt__PriceList__c`, `vlocity_cmt__Promotion__c`, `vlocity_cmt__Catalog__c`

Gotchas: OmniStudio can be extremely SOQL-heavy. One step can do dozens of queries.

### Xactly Incent / Connect
Namespace: `xactly`

Function: commission management.

## Service Cloud add-ons

### ServiceMax (field service)
Namespace: `SVMXC`

### Field Service Lightning (native)
Not a managed package per se, but uses `wkcc` namespace in some areas.

### Gainsight
Namespace: `gsfn` (NXT) or `CRM` (CS)

Function: customer success management.

## Analytics and AI

### Einstein / Tableau CRM (formerly Wave)
Namespace: `bi`, `wave`

Function: analytics dashboards.

### Einstein Discovery
Namespace: `einsteinDiscovery`

### Einstein Activity Capture
Integration, not a package per se. Emails/events synced.

### Einstein Bots
Namespace: `einsteinbots`

## DevOps

### Copado
Namespace: `copado`

Function: CI/CD, release management.

Signatures: `copado__User_Story__c`, `copado__Promotion__c`, `copado__Deployment__c`.

### Gearset
Not a managed package; SaaS with integration user.

### Flosum
Namespace: `Flosum`

### AutoRABIT
Namespace: `autorabit`

## Backup / data management

### OwnBackup
Namespace: `ownbackup`

Function: backup and recovery.

### Salesforce Backup
Native.

### DataArchiva
Namespace: `Archivaor`

Function: data archiving.

## Integration platforms (iPaaS agents)

### MuleSoft
Not a managed package; integration via connected app. Look for `mulesoft` in integration user naming.

### Boomi
Not a managed package; integration via connected app. Look for `BOOMI_*__c` custom fields on objects and `boomi` in integration user naming.

### Jitterbit
Integration user naming `jitterbit`.

### Informatica Cloud
Namespace `infa` (agent) or integration-user based.

## Customer success / support

### Service Cloud Voice
Native (no namespace).

### NICE inContact CXone
Namespace: `NICEBLUE`

### Five9
Namespace: `five9`

### Genesys Cloud
Namespace: `purecloud`, `genesys`

## Healthcare

### Health Cloud
Namespace: `HealthCloudGA`

Function: patient management, care plans.

Signatures: `HealthCloudGA__*` fields; custom objects like `Care_Plan__c`.

### Veeva (life sciences)
Namespace: `Veeva`

Function: pharma-specific CRM.

## Media and communications

### Salesforce OMS (B2C Commerce integration)
Native for B2C sites.

### Retail Execution
Namespace: `retailExecution`

## How to identify an unknown package

1. Grep unique namespaces:
   ```bash
   grep -oE "ENTERING_MANAGED_PKG\|[A-Za-z_0-9]+" log.log | awk -F'|' '{print $2}' | sort -u
   ```

2. Look for custom fields with that prefix on the affected object:
   ```bash
   grep -oE "[A-Za-z_]+__[a-z]+__c" log.log | awk -F'__' '{print $1}' | sort -u
   ```

3. Search AppExchange for the namespace. Most packages list it.

4. Search Salesforce Help, Trailhead, and community answers for the namespace.

5. Inspect the custom metadata types the package uses:
   ```bash
   grep "SOQL_EXECUTE_BEGIN" log.log | grep -oE "[A-Za-z_]+__mdt" | sort -u
   ```
   Custom metadata types named with the package prefix give away the package.

## When the package is the culprit vs the victim

Packages are often the immediate actor but rarely the root cause. Common misdiagnoses:

- **DLRS flip-flop**: DLRS propagates flip-flops from child records. The fix is upstream (why are children flip-flopping?), not in DLRS.
- **TracRTC retries**: TracRTC retries because the merge fails due to permission misconfiguration. Fix the permission, retries stop.
- **CPQ slow save**: CPQ calculator does a lot by design. If it is too slow, the underlying config (too many product rules, too many price rules) is the problem, not CPQ itself.
- **Vlocity slow**: OmniStudio scripts can be inefficient by design. Profile the specific step.
- **Marketo Sync overwriting**: Marketo Sync writes fields it is configured to write. If a field is unexpectedly changing, someone configured Marketo to own that field.

Investigate what is causing the package to behave that way, not just the package itself.

## Managed package debugging techniques

1. **Disable and compare**: most packages have a "disable" toggle. Disable, repro, compare.
2. **Read the package docs**: every major ISV has documentation on their triggers, settings, and hooks.
3. **Check the package's custom objects and metadata**: their configuration often has answers.
4. **Contact the ISV support**: packages like CPQ, Vlocity, nCino have dedicated support; use it.
5. **Check the package's Trust site**: many ISVs have status pages and issue trackers.

## Governor limits per namespace

`LIMIT_USAGE_FOR_NS` events in the log show per-namespace usage. If one namespace is burning 90% of the SOQL budget, you know who to investigate.

```bash
grep "LIMIT_USAGE_FOR_NS" log.log | awk -F'|' '{print $3}' | sort -u
```

Each namespace gets its own governor limit pool in some dimensions. A managed package running 100 queries does not burn your 100-query limit for non-managed code.
