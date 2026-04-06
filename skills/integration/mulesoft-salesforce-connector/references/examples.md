# Examples — MuleSoft Salesforce Connector

## Example 1: Incremental Account Sync with Watermark and Bulk API

**Context:** A retail company syncs Account records nightly from Salesforce to an on-premise data warehouse. The volume is 50,000+ modified Accounts per day. The previous implementation used SOAP API with a `SELECT ... WHERE LastModifiedDate > :lastRun` query, but it was exhausting the daily API limit and timing out on large result sets.

**Problem:** Without watermark-based incremental sync using the correct API, the flow either re-processes the entire Account table (wasting Bulk API budget) or burns through the SOAP API daily limit within a few hours of a busy day.

**Solution:**

```xml
<!-- Mule 4 Flow: Incremental Account Sync -->
<flow name="account-incremental-sync">
  <scheduler>
    <scheduling-strategy>
      <cron expression="0 0 2 * * ?" timeZone="America/Chicago"/>
    </scheduling-strategy>
  </scheduler>

  <!-- Step 1: Read watermark from Object Store -->
  <os:retrieve key="account-sync-watermark" objectStore="watermarkStore"
               target="lastWatermark">
    <os:default-value>2000-01-01T00:00:00.000Z</os:default-value>
  </os:retrieve>

  <!-- Step 2: Query Salesforce via Bulk API -->
  <salesforce:query config-ref="Salesforce_Bulk_Config">
    <salesforce:salesforce-query>
      SELECT Id, Name, Industry, LastModifiedDate
      FROM Account
      WHERE LastModifiedDate > :lastWatermark
      ORDER BY LastModifiedDate ASC
    </salesforce:salesforce-query>
    <salesforce:parameters>
      <![CDATA[#[{ "lastWatermark": vars.lastWatermark }]]]>
    </salesforce:parameters>
  </salesforce:query>

  <!-- Step 3: Batch process with error isolation -->
  <batch:job jobName="account-sync-batch" maxFailedRecords="500">
    <batch:process-records>
      <batch:step name="transform-and-load">
        <!-- Transform to warehouse schema and insert -->
        <ee:transform><!-- DataWeave mapping --></ee:transform>
        <db:insert config-ref="Warehouse_DB"><!-- INSERT statement --></db:insert>
      </batch:step>
    </batch:process-records>
    <batch:on-complete>
      <!-- Step 4: Advance watermark only on acceptable success rate -->
      <choice>
        <when expression="#[payload.successfulRecords > 0 and
                           (payload.failedRecords / payload.totalRecords) &lt; 0.05]">
          <os:store key="account-sync-watermark" objectStore="watermarkStore">
            <os:value>#[payload.maxLastModifiedDate]</os:value>
          </os:store>
        </when>
        <otherwise>
          <logger level="ERROR"
                  message="Batch failure rate exceeded 5%. Watermark NOT advanced."/>
        </otherwise>
      </choice>
    </batch:on-complete>
  </batch:job>
</flow>
```

**Why it works:** Bulk API avoids the standard API limit and handles 50,000+ records efficiently via async job processing. The Object Store watermark ensures only modified records are queried. The watermark only advances when the failure rate is below 5%, preventing data loss on bad batches. Failed records remain in the next sync window for automatic retry.

---

## Example 2: Real-Time Order Event Processing via Replay Topic

**Context:** An e-commerce platform needs to process Salesforce Order platform events in near-real-time to trigger fulfillment workflows in an external OMS. Events must not be lost even if the Mule application restarts.

**Problem:** Without durable replay, a Mule application restart loses all events published during downtime. The default CometD subscription starts from the tip of the event stream, dropping anything published while the subscriber was offline.

**Solution:**

```xml
<!-- Mule 4 Flow: Durable Platform Event Subscriber -->
<flow name="order-event-subscriber">
  <!-- Subscribe with replay from last stored replay ID -->
  <salesforce:replay-topic config-ref="Salesforce_Streaming_Config"
                            topic="/event/Order_Event__e"
                            replayId="-1"
                            autoReplay="true"
                            objectStore-ref="replayIdStore"/>

  <!-- Process the event payload -->
  <ee:transform>
    <ee:message>
      <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
{
  orderId: payload.Order_Id__c,
  action: payload.Action__c,
  timestamp: payload.CreatedDate
}]]></ee:set-payload>
    </ee:message>
  </ee:transform>

  <!-- Forward to fulfillment system -->
  <http:request method="POST" url="${fulfillment.api.url}/orders"
                config-ref="Fulfillment_HTTP"/>

  <!-- Error handling: log and continue, do not lose replay position -->
  <error-handler>
    <on-error-continue type="HTTP:CONNECTIVITY">
      <logger level="ERROR"
              message="Fulfillment API unreachable. Event queued for retry."/>
      <jms:publish destination="order-event-dlq" config-ref="JMS_Config"/>
    </on-error-continue>
  </error-handler>
</flow>
```

**Why it works:** The `replay-topic` source with `autoReplay="true"` and an Object Store-backed replay ID store persists the last successfully processed replay ID. On restart, the connector resumes from the stored position rather than the stream tip. The 72-hour event retention window in Salesforce (for high-volume Platform Events) gives ample time for the subscriber to catch up after extended downtime.

---

## Anti-Pattern: Using Username-Password Auth in Production

**What practitioners do:** Configure the Salesforce Connector with `<salesforce:basic-connection username="..." password="..." securityToken="..."/>` for speed during development, then promote this configuration to production unchanged.

**What goes wrong:** When the integration user's password expires or is reset, the flow silently fails with `INVALID_LOGIN` until someone manually updates the Mule properties file and redeploys. If Salesforce enforces MFA on API-only users (which became default for many orgs), username-password auth stops working entirely with no clear error message. The security token also changes on every password reset, creating a double failure point.

**Correct approach:** Use OAuth 2.0 JWT Bearer authentication. The flow authenticates with a signed certificate rather than a password. Token refresh is automatic, MFA does not block server-to-server certificate-based auth, and credential rotation involves only certificate renewal on a predictable schedule.
