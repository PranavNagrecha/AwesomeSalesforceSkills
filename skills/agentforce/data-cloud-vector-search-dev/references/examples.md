# Examples — Data Cloud Vector Search Dev

## Example 1: Rebuilding an Easy Setup Index with Advanced Setup for Better Chunking Precision

**Context:** A developer built a Data Cloud vector search index using Easy Setup to ground a service Agentforce agent with product documentation. After go-live, the agent frequently returns chunks that contain the right topic but too much surrounding text, causing the LLM to miss the specific answer buried in a long chunk.

**Problem:** Easy Setup locked the chunk size at an automatically chosen value (typically 512–1024 tokens). The developer has no way to reduce chunk size or switch to paragraph-based chunking through the Easy Setup index — there is no edit control for these parameters.

**Solution:**

```
1. In Data Cloud Setup → Vector Search, identify the existing Easy Setup index.
   Note the source DMO name and text field (e.g., ProductDocs__dlm.Body__c).
   
2. Deactivate and delete the Easy Setup index.
   (This does not remove the source DMO or its data.)

3. Click "New Vector Search Index" and select "Advanced Setup".

4. Source configuration:
   - Object: ProductDocs__dlm
   - Field: Body__c

5. Chunking configuration:
   - Strategy: Fixed-size
   - Chunk size: 256 tokens
   - Chunk overlap: 32 tokens (12.5%)

6. Embedding model: Salesforce-managed (no additional config required)

7. Save and trigger initial index build.
   Monitor index Status in Setup until it reads "Active".

8. In Agentforce Setup → Agent Topic → Grounding, update the index reference
   to point to the new Advanced Setup index. Set topK = 5.

9. Test in Agent Preview with 5 representative queries.
   Confirm retrieved chunks in the Grounding tab are more focused.
```

**Why it works:** Smaller fixed-size chunks isolate individual concepts within the documentation, improving the cosine similarity score for narrow semantic queries. The embedding model has less noise to encode per chunk, resulting in more precise ANN retrieval at search time.

---

## Example 2: Calling the Data Cloud Vector Search Query API from an External Service

**Context:** A middleware integration layer (Node.js service) needs to retrieve semantically relevant product documentation chunks before calling a third-party LLM. The service cannot use Agentforce grounding because it routes through an external LLM, not an Agentforce agent.

**Problem:** The developer initially tried to reuse an existing Salesforce CRM Connected App OAuth token to call the Data Cloud Query API. The API returned a `401 Unauthorized` on every request. The standard CRM token is not valid for the Data Cloud API.

**Solution:**

```javascript
// Step 1: Obtain a Data Cloud access token
// Uses the Data Cloud Connected App — must have cdpapi scope
async function getDataCloudToken(clientId, clientSecret, instanceUrl) {
  const params = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: clientId,
    client_secret: clientSecret,
  });

  const response = await fetch(`${instanceUrl}/services/a360/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });

  if (!response.ok) {
    throw new Error(`Token request failed: ${response.status} ${await response.text()}`);
  }

  const data = await response.json();
  // data.instance_url is the Data Cloud tenant base URL (different from CRM instance_url)
  return { accessToken: data.access_token, dcInstanceUrl: data.instance_url };
}

// Step 2: Execute a vector search query
async function queryVectorIndex(dcInstanceUrl, accessToken, indexName, queryText, topK = 5) {
  const endpoint = `${dcInstanceUrl}/api/v1/vector-search/${indexName}/query`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: queryText,
      topK: topK,
    }),
  });

  if (!response.ok) {
    throw new Error(`Vector search failed: ${response.status} ${await response.text()}`);
  }

  return response.json(); // { results: [{ chunk: "...", score: 0.87, metadata: {...} }] }
}
```

**Why it works:** The Data Cloud token endpoint (`/services/a360/token`) authenticates against the Data Cloud tenant, producing a token scoped to Data Cloud APIs. The `dcInstanceUrl` in the token response is the Data Cloud tenant hostname, which differs from the CRM `instance_url`. Using the CRM instance URL for the Query API call will fail even with a valid Data Cloud token.

---

## Anti-Pattern: Adjusting Only top-K to Fix Poor Retrieval Quality

**What practitioners do:** After noticing that an Agentforce agent built with an Easy Setup vector index gives vague or off-topic answers, the developer navigates to the Grounding configuration and increases top-K from 5 to 10, expecting more retrieved chunks to improve coverage.

**What goes wrong:** Increasing top-K returns more chunks but does not fix the underlying chunk quality problem. If the index was built with Easy Setup using large auto-selected chunks, each chunk already contains multiple topics blended together. Increasing top-K just adds more blended, low-precision chunks to the prompt, consuming token budget without improving grounding accuracy. In some cases, the additional low-relevance chunks actively degrade the LLM response by introducing contradictory or irrelevant context.

**Correct approach:** Diagnose whether the issue is a retrieval quality problem (wrong chunks are being returned) or a top-K coverage problem (the right chunk exists but is not in the result set). Review the Grounding tab in Agent Preview to inspect which specific chunks are returned for a failing query. If the returned chunks are topically correct but too broad, the issue is chunking granularity — rebuild with Advanced Setup using smaller chunks. Only increase top-K if the correct chunk is absent from results entirely.
