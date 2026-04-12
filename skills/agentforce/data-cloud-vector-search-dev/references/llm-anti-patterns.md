# LLM Anti-Patterns — Data Cloud Vector Search Dev

Common mistakes AI coding assistants make when generating or advising on Data Cloud vector search development. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Chunk Size as a Free Numeric Parameter in Easy Setup

**What the LLM generates:** "In the Data Cloud vector search Easy Setup UI, set the chunk size to 256 tokens and the overlap to 32 tokens for better precision."

**Why it happens:** LLMs trained on generic vector database documentation (Pinecone, Weaviate, pgvector) know that chunk size is typically a numeric field in the index creation UI. They apply this general knowledge to Easy Setup without knowing that Salesforce Easy Setup does not expose chunk parameters — the platform selects them automatically.

**Correct pattern:**

```
Easy Setup does not expose chunk size or chunking strategy parameters.
These are automatically chosen by the platform and cannot be modified
after index creation.

To control chunk size and strategy:
1. Use Advanced Setup when creating the index.
2. Select the chunking strategy: Fixed-size, Paragraph, or Sentence.
3. For Fixed-size, specify chunk size (tokens) and overlap (tokens).

If an Easy Setup index already exists, delete it and rebuild with
Advanced Setup to gain chunking control.
```

**Detection hint:** Any recommendation to "set chunk size" or "configure chunk overlap" that does not explicitly mention Advanced Setup should be flagged. Easy Setup provides no such controls.

---

## Anti-Pattern 2: Using the Standard CRM OAuth Token for the Data Cloud Query API

**What the LLM generates:**

```javascript
// Incorrect: reusing a CRM Connected App token for Data Cloud API
const token = await getCrmOAuthToken(clientId, clientSecret); // /services/oauth2/token
const results = await fetch(`${instanceUrl}/api/v1/vector-search/${indexName}/query`, {
  headers: { Authorization: `Bearer ${token}` },
  // ... will always return 401
});
```

**Why it happens:** LLMs generalize from the Salesforce CRM REST API pattern where a single OAuth token obtained from `/services/oauth2/token` authenticates all CRM API calls. They are not trained on the Data Cloud authentication documentation that describes the separate `/services/a360/token` endpoint and the `cdpapi` scope requirement.

**Correct pattern:**

```javascript
// Correct: use the Data Cloud token endpoint with cdpapi-scoped Connected App
const dcTokenResponse = await fetch(`${crmInstanceUrl}/services/a360/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: DATA_CLOUD_CLIENT_ID,   // Data Cloud Connected App, NOT CRM app
    client_secret: DATA_CLOUD_CLIENT_SECRET,
  }),
});
const { access_token, instance_url: dcInstanceUrl } = await dcTokenResponse.json();
// dcInstanceUrl is the Data Cloud tenant URL — use it for all subsequent DC API calls
```

**Detection hint:** Any code that calls `/services/oauth2/token` and then uses the resulting token to call a `/api/v1/vector-search/` endpoint is wrong. Data Cloud tokens must come from `/services/a360/token`.

---

## Anti-Pattern 3: Assuming All Salesforce APIs Share the Same instance_url

**What the LLM generates:**

```javascript
// Incorrect: using CRM instance_url as the base for Data Cloud API calls
const { access_token, instance_url } = await getDataCloudToken(); 
// instance_url here is the DC tenant URL (e.g., https://abc123.c360a.salesforce.com)
// but LLM uses the CRM instance_url instead:
const response = await fetch(`${CRM_INSTANCE_URL}/api/v1/vector-search/...`, { ... });
```

**Why it happens:** LLMs see `instance_url` in Salesforce token responses and assume it always refers to the main org URL. The Data Cloud token endpoint returns an `instance_url` that points to the Data Cloud tenant infrastructure (`*.c360a.salesforce.com`), which is a different hostname from the CRM instance URL. Using the CRM URL as the base for Data Cloud API calls produces 404 or 401 errors.

**Correct pattern:**

```javascript
// Correct: extract instance_url from the DATA CLOUD token response
const dcTokenResponse = await fetch(`${CRM_ORG_URL}/services/a360/token`, { ... });
const { access_token, instance_url: DC_INSTANCE_URL } = await dcTokenResponse.json();

// Use DC_INSTANCE_URL (e.g., https://abc123.c360a.salesforce.com) for all DC API calls
const searchUrl = `${DC_INSTANCE_URL}/api/v1/vector-search/${indexName}/query`;
```

**Detection hint:** Look for code that extracts `instance_url` from a Data Cloud token response but then uses a hardcoded CRM domain or a separately obtained `instance_url` for the API call. The Data Cloud `instance_url` must come from the Data Cloud token response, not the CRM token response.

---

## Anti-Pattern 4: Claiming the Einstein Trust Layer Does Not Apply to Retrieved Chunks

**What the LLM generates:** "Retrieved chunks are injected directly into the prompt without modification — the Trust Layer only applies to the final LLM response."

**Why it happens:** LLMs generalize from generic RAG documentation where the retriever returns chunks as-is to the prompt. They are not aware that Salesforce's Einstein Trust Layer processes the entire prompt payload — including grounding chunks — before it reaches the LLM. Data masking is applied to retrieved chunks that contain PII-classified fields.

**Correct pattern:**

```
The Einstein Trust Layer processes the full prompt payload, including
grounding chunks, before the payload reaches the LLM.

At inference time:
1. Chunks are retrieved from the vector index via the Grounding configuration.
2. The Trust Layer applies data masking rules to any PII-classified fields
   present in the retrieved chunk content.
3. Masked chunks (with placeholder tokens replacing sensitive values) are
   injected into the prompt.
4. Zero data retention is enforced at the LLM provider.

Developers must classify sensitive DMO fields in the Data Cloud field
taxonomy before indexing if they want to control what masking applies
at retrieval time.
```

**Detection hint:** Any claim that Trust Layer policies "only apply after" retrieval or "only to LLM outputs" is incorrect. Masking is applied to chunk content before the LLM sees it.

---

## Anti-Pattern 5: Recommending Increasing top-K to Fix Poor Retrieval Precision

**What the LLM generates:** "If the agent is returning off-topic answers, increase topK from 5 to 10 to give the LLM more context to work with."

**Why it happens:** LLMs associate "more retrieved content = better coverage" and conflate retrieval recall problems (the right chunk is not in the result set) with retrieval precision problems (the wrong chunks are at the top of the result set). Increasing top-K can improve recall but does not improve precision. If precision is poor because the index was built with Easy Setup using overly large auto-selected chunks, adding more imprecise chunks actively degrades agent response quality.

**Correct pattern:**

```
Before adjusting topK, diagnose the retrieval failure mode:

1. Open Agent Preview and submit a failing query.
2. Check the Grounding tab — inspect the specific chunks returned.

If chunks are topically correct but too broad (contain multiple topics):
  → Problem is chunk granularity (chunking strategy or size)
  → Fix: rebuild the index with Advanced Setup using smaller chunks
  → Do NOT increase topK

If the correct chunk exists in the DMO but is absent from results:
  → Problem is recall (the right chunk scored below topK threshold)
  → Fix: investigate embedding quality and filter expressions
  → Increasing topK may help as a temporary measure

If topK is already high (>7) and precision is still poor:
  → Adding more low-precision chunks consumes token budget
  → Consider reducing topK and improving chunking strategy instead
```

**Detection hint:** A recommendation to "increase topK" as the primary fix for poor agent responses — without first diagnosing whether the issue is precision vs recall — is an anti-pattern. topK adjustment is a tuning lever, not a diagnostic tool.

---

## Anti-Pattern 6: Packaging a Vector Search Index Without Including It in a Data Kit

**What the LLM generates:** "Deploy the vector search index configuration using a standard SFDX metadata deployment — package the index XML file in the force-app directory."

**Why it happens:** LLMs default to standard Salesforce DX deployment patterns for all metadata types. Vector search index configuration in Data Cloud is deployed via Data Kits, which are a separate packaging mechanism from standard SFDX metadata deployment. Attempting to deploy vector index config as standard SFDX metadata will either fail silently or be ignored.

**Correct pattern:**

```
Data Cloud vector search index configuration is a Data Kit component.
It cannot be deployed via standard SFDX metadata deployment (force-app).

To package for scratch org or ISV distribution:
1. In Data Cloud Setup, navigate to Data Kits.
2. Create or edit the Data Kit for this package.
3. Add components: the vector search index, the source DMO definition,
   and the Data Stream configuration.
4. Export the Data Kit and include it in the package.
5. Validate in a scratch org by importing the Data Kit and confirming
   the index is created and Active.
```

**Detection hint:** Any instruction to place vector search index configuration files in `force-app/main/default/` or deploy using `sf project deploy start` without a Data Kit wrapper should be flagged as incorrect for Data Cloud vector search configuration.
