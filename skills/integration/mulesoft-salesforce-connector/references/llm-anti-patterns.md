# LLM Anti-Patterns — MuleSoft Salesforce Connector

Common mistakes AI coding assistants make when generating or advising on MuleSoft Salesforce Connector flows.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Mule 3 Watermark Syntax for Mule 4 Flows

**What the LLM generates:**

```xml
<poll frequency="60000">
  <watermark variable="lastTimestamp"
             default-expression="#[server.dateTime.format('yyyy-MM-dd\'T\'HH:mm:ss.SSS\'Z\'')]"
             update-expression="#[flowVars.maxDate]"/>
  <salesforce:query config-ref="Salesforce_Config">
    SELECT Id, Name FROM Account WHERE LastModifiedDate > #[flowVars.lastTimestamp]
  </salesforce:query>
</poll>
```

**Why it happens:** The Mule 3 watermark pattern is heavily represented in training data from blog posts, Stack Overflow answers, and MuleSoft documentation prior to 2018. LLMs default to it because it was the canonical pattern for years.

**Correct pattern:**

```xml
<!-- Mule 4: Use Object Store for watermark -->
<os:retrieve key="lastTimestamp" objectStore="watermarkStore" target="lastTimestamp">
  <os:default-value>2000-01-01T00:00:00.000Z</os:default-value>
</os:retrieve>
<salesforce:query config-ref="Salesforce_Config">
  <salesforce:salesforce-query>
    SELECT Id, Name FROM Account WHERE LastModifiedDate > :lastTimestamp
  </salesforce:salesforce-query>
  <salesforce:parameters>#[{ "lastTimestamp": vars.lastTimestamp }]</salesforce:parameters>
</salesforce:query>
```

**Detection hint:** Look for `<watermark`, `<poll>`, `flowVars.` or `server.dateTime` — all are Mule 3 constructs that do not exist in Mule 4.

---

## Anti-Pattern 2: Recommending Username-Password Auth as the Default

**What the LLM generates:**

```xml
<salesforce:sfdc-config name="Salesforce_Config">
  <salesforce:basic-connection
    username="${salesforce.username}"
    password="${salesforce.password}"
    securityToken="${salesforce.token}"/>
</salesforce:sfdc-config>
```

**Why it happens:** Username-password is the simplest auth configuration and appears in most getting-started tutorials and connector quickstart docs. LLMs optimize for the shortest working example.

**Correct pattern:**

```xml
<salesforce:sfdc-config name="Salesforce_Config">
  <salesforce:oauth-jwt-connection
    consumerKey="${salesforce.consumerKey}"
    keyStorePath="${salesforce.keystore.path}"
    storePassword="${salesforce.keystore.password}"
    principal="${salesforce.username}"
    audienceUrl="https://login.salesforce.com"/>
</salesforce:sfdc-config>
```

**Detection hint:** Presence of `basic-connection`, `password=`, or `securityToken=` in Salesforce connector configuration.

---

## Anti-Pattern 3: Using SOAP API Query for High-Volume Data Loads

**What the LLM generates:** A flow that uses the default `<salesforce:query>` operation (which maps to SOAP API) to extract 100,000+ records, with no mention of Bulk API or the `fetchSize` / API mode configuration.

**Why it happens:** The connector's `query` operation defaults to SOAP API. LLMs generate the simplest query call without considering volume. Training data rarely includes the `useBulkApi` configuration flag because most examples use small data sets.

**Correct pattern:**

```xml
<!-- Enable Bulk API in the connector global config -->
<salesforce:sfdc-config name="Salesforce_Bulk_Config">
  <salesforce:oauth-jwt-connection ... />
  <!-- Set queryType to BULK for high-volume queries -->
</salesforce:sfdc-config>

<!-- Or use the dedicated bulk operations -->
<salesforce:create-job config-ref="Salesforce_Bulk_Config" .../>
```

**Detection hint:** Any `<salesforce:query>` operating on an object expected to return > 10,000 records without Bulk API configuration. Check for absence of `bulk`, `createJob`, or `useBulkApi` in the flow XML.

---

## Anti-Pattern 4: Hardcoding Salesforce Instance URLs Instead of Using Login URL

**What the LLM generates:**

```xml
<salesforce:oauth-jwt-connection
  consumerKey="..."
  audienceUrl="https://mycompany.my.salesforce.com"
  tokenUrl="https://mycompany.my.salesforce.com/services/oauth2/token"/>
```

**Why it happens:** LLMs copy the instance-specific My Domain URL from example configurations. The connector's OAuth flow should use the generic login endpoint, which returns the correct instance URL after authentication.

**Correct pattern:**

```xml
<salesforce:oauth-jwt-connection
  consumerKey="..."
  audienceUrl="https://login.salesforce.com"
  <!-- For sandbox: audienceUrl="https://test.salesforce.com" -->
  />
```

**Detection hint:** `audienceUrl` or `tokenUrl` containing `.my.salesforce.com` or any org-specific subdomain. Should be `login.salesforce.com` or `test.salesforce.com`.

---

## Anti-Pattern 5: Advancing Watermark Unconditionally After Query

**What the LLM generates:**

```xml
<!-- Query Salesforce -->
<salesforce:query .../>
<!-- Immediately store new watermark -->
<os:store key="watermark" value="#[now()]"/>
<!-- Then process records -->
<foreach>
  <!-- processing logic -->
</foreach>
```

**Why it happens:** LLMs generate watermark storage immediately after the query because it follows a linear "read then bookmark" mental model. They do not account for processing failures that occur after the watermark is advanced.

**Correct pattern:**

```xml
<!-- Query Salesforce -->
<salesforce:query .../>
<!-- Process records FIRST -->
<batch:job maxFailedRecords="100">
  <batch:process-records><!-- processing --></batch:process-records>
  <batch:on-complete>
    <!-- Advance watermark ONLY after successful processing -->
    <choice>
      <when expression="#[payload.failedRecords == 0]">
        <os:store key="watermark" value="#[vars.maxLastModifiedDate]"/>
      </when>
    </choice>
  </batch:on-complete>
</batch:job>
```

**Detection hint:** `<os:store>` for watermark key appearing before `<batch:job>`, `<foreach>`, or any processing logic that operates on the queried records.

---

## Anti-Pattern 6: Omitting Error Handling for Streaming Subscriptions

**What the LLM generates:**

```xml
<flow name="event-listener">
  <salesforce:replay-topic topic="/event/My_Event__e"/>
  <logger message="#[payload]"/>
</flow>
```

**Why it happens:** LLMs generate minimal happy-path flows. Streaming subscriptions have unique failure modes (disconnection, replay ID expiration, channel deletion) that are not covered in basic examples.

**Correct pattern:**

```xml
<flow name="event-listener">
  <salesforce:replay-topic topic="/event/My_Event__e"
                            replayId="-1"
                            autoReplay="true"
                            objectStore-ref="replayStore"/>
  <!-- Processing logic -->
  <error-handler>
    <on-error-continue type="SALESFORCE:CONNECTIVITY">
      <logger level="WARN" message="Streaming connection lost. Auto-reconnect will retry."/>
    </on-error-continue>
    <on-error-continue type="SALESFORCE:INVALID_REPLAY_ID">
      <logger level="ERROR" message="Replay ID expired. Falling back to -1 (tip)."/>
      <os:remove key="My_Event__e" objectStore="replayStore"/>
    </on-error-continue>
  </error-handler>
</flow>
```

**Detection hint:** `<salesforce:replay-topic>` or `<salesforce:subscribe-topic>` without an `<error-handler>` block in the same flow.
