# MuleSoft Salesforce Connector — Work Template

Use this template when configuring or reviewing a MuleSoft Salesforce integration.

## Scope

**Skill:** `mulesoft-salesforce-connector`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Salesforce org edition and API limits:** (e.g., Enterprise Edition, 100,000 daily API calls, Bulk API enabled)
- **Mule runtime version:** (e.g., Mule 4.4.x — confirm NOT Mule 3)
- **Integration pattern:** (request-reply / batch-bulk / event-driven / bidirectional sync)
- **Volume estimate:** (records per sync, peak concurrency, frequency)
- **Authentication method:** (JWT Bearer / Authorization Code / username-password — note: JWT Bearer recommended)

## API Selection

Based on context above, the recommended API is:

| Factor | Value | Selected API |
|---|---|---|
| Record volume per sync | ___ records | SOAP / REST Composite / Bulk API 2.0 |
| Latency requirement | real-time / near-real-time / scheduled | Streaming / REST / Bulk |
| Auth context | system-to-system / per-user | JWT Bearer / Authorization Code |

## Authentication Checklist

- [ ] Connected App created with "Enable OAuth Settings"
- [ ] Digital certificate uploaded (for JWT Bearer)
- [ ] Permitted Users set to "Admin approved users are pre-authorized"
- [ ] Integration user's profile added to Connected App's allowed profiles
- [ ] Consumer Key recorded in Mule secure properties
- [ ] Keystore file (JKS) deployed to Mule runtime classpath
- [ ] Test token exchange successful via cURL before Mule config

## Watermark Design (if incremental sync)

- **Watermark field:** `LastModifiedDate` / `SystemModstamp` / custom field: ___
- **Object Store key name:** ___
- **Default value (first run):** `2000-01-01T00:00:00.000Z`
- **Advancement condition:** Watermark advances only when: ___
- **Failure behavior:** On batch failure > ___% threshold, watermark is NOT advanced

## Batch Error Handling Design (if batch processing)

- **maxFailedRecords:** ___ (0 = abort on first failure; set to acceptable threshold)
- **Dead-letter destination:** (JMS queue / database table / Platform Event / log file)
- **Retry strategy for failed records:** (re-queue for next sync / manual review / immediate retry)

## Flow Skeleton

```xml
<flow name="___-sync-flow">
  <!-- Trigger: scheduler / HTTP listener / streaming source -->
  <scheduler>
    <scheduling-strategy>
      <cron expression="___" timeZone="___"/>
    </scheduling-strategy>
  </scheduler>

  <!-- Read watermark -->
  <os:retrieve key="___" objectStore="___" target="watermark">
    <os:default-value>___</os:default-value>
  </os:retrieve>

  <!-- Query Salesforce -->
  <salesforce:query config-ref="___">
    <salesforce:salesforce-query>
      SELECT ___ FROM ___ WHERE LastModifiedDate > :watermark
    </salesforce:salesforce-query>
    <salesforce:parameters>#[{ "watermark": vars.watermark }]</salesforce:parameters>
  </salesforce:query>

  <!-- Batch process -->
  <batch:job jobName="___" maxFailedRecords="___">
    <batch:process-records>
      <batch:step name="___">
        <!-- Transform and load -->
      </batch:step>
    </batch:process-records>
    <batch:on-complete>
      <!-- Advance watermark on success -->
    </batch:on-complete>
  </batch:job>

  <!-- Error handling -->
  <error-handler>
    <on-error-propagate type="SALESFORCE:CONNECTIVITY">
      <!-- Log and alert -->
    </on-error-propagate>
  </error-handler>
</flow>
```

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] Connected App uses JWT Bearer (not username-password) for server-to-server flows
- [ ] Connector global configuration specifies the correct API mode for the volume
- [ ] Watermark is stored in Object Store and only advanced after successful processing
- [ ] Batch scope has maxFailedRecords set with dead-letter logging
- [ ] API call budget verified: daily limit headroom confirmed
- [ ] Integration user has a dedicated profile with minimum required permissions
- [ ] Flow tested with partial-failure scenarios to confirm error isolation

## Notes

Record any deviations from the standard pattern and why.
