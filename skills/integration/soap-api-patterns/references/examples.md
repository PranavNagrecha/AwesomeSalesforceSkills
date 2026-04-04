# Examples — SOAP API Patterns

## Example 1: .NET Integration Using the Enterprise WSDL

**Context:** A manufacturing company has a legacy .NET ERP integration that pushes Account and Order records into Salesforce on a nightly batch. The org has custom fields on Account. The team wants to authenticate safely and upsert records with an external ID.

**Problem:** The team originally used a hardcoded `na1` login endpoint and embedded the password and security token in `app.config`. When the org moved to a Hyperforce instance, all API calls failed because the hardcoded `na1` URL was unreachable. Additionally, after a schema change (new custom field on Account), the upsert silently stopped populating the new field because the WSDL was not regenerated.

**Solution:**

```csharp
// Step 1: Authenticate using the standard login endpoint — capture serverUrl
SforceService binding = new SforceService();
binding.Url = "https://login.salesforce.com/services/Soap/c/63.0";

LoginResult loginResult = binding.login(
    Environment.GetEnvironmentVariable("SF_USERNAME"),
    Environment.GetEnvironmentVariable("SF_PASSWORD_WITH_TOKEN")
);

// Step 2: Switch ALL subsequent calls to the instance-specific serverUrl
binding.Url = loginResult.serverUrl;
binding.SessionHeaderValue = new SessionHeader { sessionId = loginResult.sessionId };

// Step 3: Upsert Accounts using an External ID field (ERP_Account_ID__c)
Account[] accountsToUpsert = BuildAccountsFromERP();
UpsertResult[] results = binding.upsert("ERP_Account_ID__c", accountsToUpsert);

// Step 4: Inspect per-record results — partial success is normal
foreach (UpsertResult result in results)
{
    if (!result.success)
    {
        foreach (Error error in result.errors)
        {
            Log.Error($"{error.statusCode}: {error.message} (fields: {string.Join(", ", error.fields)})");
        }
    }
}
```

**Why it works:** Using environment variables avoids embedding credentials in config. Switching to `serverUrl` after `login()` ensures the integration works on any Salesforce instance. Inspecting each `UpsertResult` catches record-level validation failures that would otherwise be silently ignored.

**Re-generation reminder:** Whenever the org admin adds or changes a custom field on Account (or any other object used by this integration), the developer must re-download the enterprise WSDL from Setup > API > Generate Enterprise WSDL and regenerate the C# proxy classes. Missing this step causes the new field to remain null even when the ERP sends a value.

---

## Example 2: Java ISV Integration Using the Partner WSDL

**Context:** An ISV is building a managed package that syncs opportunity data from customer Salesforce orgs back to the ISV's central data platform. The package must work against any customer's org — including orgs with different custom fields and API versions.

**Problem:** Using the enterprise WSDL would require the ISV to generate a separate WSDL stub set for every customer org and redistribute updated code when any customer's schema changes. This is not scalable for a multi-tenant product.

**Solution:**

```java
// Partner WSDL — generic, works with any org
ConnectorConfig partnerConfig = new ConnectorConfig();
partnerConfig.setAuthEndpoint("https://login.salesforce.com/services/Soap/u/63.0");
partnerConfig.setUsername(customerUsername);
partnerConfig.setPassword(customerPasswordWithToken);

PartnerConnection connection = Connector.newConnection(partnerConfig);
// partnerConfig.getServiceEndpoint() is now the customer-specific serverUrl

// Query Opportunities — fields resolved at runtime via generic sObject
QueryResult queryResult = connection.query(
    "SELECT Id, Name, Amount, CloseDate, StageName FROM Opportunity WHERE IsClosed = false"
);

while (!queryResult.isDone()) {
    processBatch(queryResult.getRecords());
    queryResult = connection.queryMore(queryResult.getQueryLocator());
}
processBatch(queryResult.getRecords());

// Helper: extract fields from generic sObject
private void processBatch(SObject[] records) {
    for (SObject record : records) {
        String id = record.getId();
        Object amount = record.getField("Amount");
        Object stageName = record.getField("StageName");
        syncToDataPlatform(id, amount, stageName);
    }
}
```

**Why it works:** The partner WSDL's generic `sObject` allows the integration to work with any org without regenerating stubs. The `query()` + `queryMore()` loop correctly handles pagination when `done` is `false`. Fields are accessed by name at runtime rather than by generated typed accessors.

**Trade-off:** Without compile-time type checking, field name typos cause runtime `null` values rather than compile errors. Unit tests should assert field presence and type before production deployment.

---

## Example 3: Metadata API Deploy via SOAP (Ant Migration Tool Pattern)

**Context:** A DevOps team needs to deploy metadata from a scratch org to a production org as part of a CI/CD pipeline. The Metadata API is exclusively SOAP-based; the login flow must authenticate first via the enterprise or partner WSDL.

**Problem:** The team tried to call the Metadata API endpoint directly without first calling `login()`. The Metadata API endpoint does not accept unauthenticated requests and has no independent login mechanism.

**Solution (Java with WSC):**

```java
// Step 1: Authenticate via enterprise WSDL to get sessionId + serverUrl
ConnectorConfig enterpriseConfig = new ConnectorConfig();
enterpriseConfig.setAuthEndpoint("https://login.salesforce.com/services/Soap/c/63.0");
enterpriseConfig.setUsername(System.getenv("SF_USERNAME"));
enterpriseConfig.setPassword(System.getenv("SF_PASSWORD_WITH_TOKEN"));

EnterpriseConnection enterpriseConnection = Connector.newConnection(enterpriseConfig);
String sessionId = enterpriseConfig.getSessionId();
String metadataServerUrl = enterpriseConfig.getServiceEndpoint()
    .replace("/services/Soap/c/", "/services/Soap/m/");

// Step 2: Initialize MetadataConnection using the session from Step 1
ConnectorConfig metadataConfig = new ConnectorConfig();
metadataConfig.setServiceEndpoint(metadataServerUrl);
metadataConfig.setSessionId(sessionId);

MetadataConnection metadataConnection = new MetadataConnection(metadataConfig);

// Step 3: Deploy a zip file of metadata
byte[] zipBytes = Files.readAllBytes(Paths.get("deploy.zip"));
DeployOptions options = new DeployOptions();
options.setRunAllTests(false);
options.setCheckOnly(false);

AsyncResult asyncResult = metadataConnection.deploy(zipBytes, options);
// Poll for completion...
```

**Why it works:** The Metadata API reuses the `sessionId` from the SOAP login. The Metadata API endpoint URL is derived by replacing `/Soap/c/` with `/Soap/m/` in the enterprise serverUrl. Passing the session ID via `ConnectorConfig.setSessionId()` is the correct injection point for WSC-based Metadata API clients.

---

## Anti-Pattern: Ignoring Per-Record `SaveResult` Errors

**What practitioners do:** Call `connection.create(records)` and only check whether the call itself threw a SOAP fault (exception). If no exception is thrown, assume all records succeeded.

**What goes wrong:** SOAP DML calls process all records in the batch even when some fail. A SOAP fault is only thrown for authentication failures, protocol errors, or system faults — not for record-level validation failures. Individual records with missing required fields, duplicate values, or validation rule violations fail silently if `SaveResult.isSuccess()` is not checked per record. Data is lost without any logged error.

**Correct approach:** Iterate over every `SaveResult` or `UpsertResult` in the response array and check `result.isSuccess()`. Log or queue-for-retry any record where `isSuccess()` is `false`, and inspect `result.getErrors()` for the `statusCode` and `message`.
