# Examples — Postman for Salesforce

## Example 1: JWT bearer collection-level pre-request script with cached token

**Context:** A platform team runs nightly Postman collection runs against three orgs (DevSandbox, UAT, Prod) to smoke-test 25 critical API workflows. Each run hits ~150 endpoints. Re-authenticating per request would burn the user's daily login budget by mid-morning.

**Problem:** A naive pre-request script that always calls `/services/oauth2/token` triples the request count *and* exhausts the 5,000-logins/day-per-user limit on the integration user before the day is out.

**Solution:**

```javascript
// Collection-level pre-request script.
// Reads cached accessToken + accessTokenExpiry; refreshes only when within 60s of expiry.

const cachedToken = pm.environment.get("accessToken");
const cachedExp = parseInt(pm.environment.get("accessTokenExpiry") || "0", 10);
if (cachedToken && Date.now() < cachedExp - 60000) {
  return; // still valid
}

const jsrsasignUrl = "https://kjur.github.io/jsrsasign/jsrsasign-all-min.js";
pm.sendRequest({ url: jsrsasignUrl, method: "GET" }, (err, res) => {
  if (err) { console.error("jsrsasign load failed", err); throw err; }
  eval(res.text());

  const header = { alg: "RS256", typ: "JWT" };
  const claim = {
    iss: pm.environment.get("clientId"),
    sub: pm.environment.get("username"),
    aud: pm.environment.get("loginUrl"),
    exp: Math.floor(Date.now() / 1000) + 180,
  };
  const privateKey = pm.environment.get("jwtPrivateKey").replace(/\\n/g, "\n");
  const jwt = KJUR.jws.JWS.sign("RS256", JSON.stringify(header), JSON.stringify(claim), privateKey);

  pm.sendRequest({
    url: `${pm.environment.get("loginUrl")}/services/oauth2/token`,
    method: "POST",
    header: { "Content-Type": "application/x-www-form-urlencoded" },
    body: { mode: "urlencoded", urlencoded: [
      { key: "grant_type", value: "urn:ietf:params:oauth:grant-type:jwt-bearer" },
      { key: "assertion", value: jwt },
    ]},
  }, (e, r) => {
    if (e) { console.error("token request failed", e); throw e; }
    if (r.code !== 200) { console.error("token error", r.text()); throw new Error(`token ${r.code}`); }
    const data = r.json();
    pm.environment.set("accessToken", data.access_token);
    pm.environment.set("instanceUrl", data.instance_url);
    pm.environment.set("accessTokenExpiry", String(Date.now() + 60 * 60 * 1000));
  });
});
```

**Why it works:** A 1h-cached token covers the typical 30–60-minute collection run with one token fetch per environment per run. The 60-second pre-expiry window prevents a token expiring mid-run. `jsrsasign` is loaded once per script execution; Postman's per-script sandbox makes caching the library across requests impractical, so the cost is paid only on refresh.

---

## Example 2: Bulk API 2.0 ingest job — five chained requests

**Context:** A data team needs to insert 50,000 contact records into a sandbox to repro a customer issue. The team uses Postman because the failure they're chasing is a malformed CSV that the Salesforce CLI's `sf data import bulk` swallows behind a generic error message.

**Problem:** A single Postman request can't represent a multi-step async job. The chain has to thread `jobId` and `contentUrl` between requests, then poll the job status until terminal.

**Solution:** Five requests in one collection folder, executed in order by the collection runner.

**Request 1 — Create job**
```
POST {{instanceUrl}}/services/data/{{apiVersion}}/jobs/ingest
Content-Type: application/json

{ "object": "Contact", "operation": "insert", "contentType": "CSV", "lineEnding": "LF" }
```
Tests:
```javascript
pm.test("job created", () => pm.expect(pm.response.code).to.eql(200));
const job = pm.response.json();
pm.collectionVariables.set("bulkJobId", job.id);
pm.collectionVariables.set("bulkContentUrl", job.contentUrl);
```

**Request 2 — Upload CSV**
```
PUT {{instanceUrl}}/{{bulkContentUrl}}
Content-Type: text/csv

LastName,Email
Doe,jane.doe@example.com
... (large CSV body)
```

**Request 3 — Mark complete**
```
PATCH {{instanceUrl}}/services/data/{{apiVersion}}/jobs/ingest/{{bulkJobId}}
Content-Type: application/json

{ "state": "UploadComplete" }
```

**Request 4 — Poll status (re-runs itself until terminal)**
```
GET {{instanceUrl}}/services/data/{{apiVersion}}/jobs/ingest/{{bulkJobId}}
```
Tests:
```javascript
const state = pm.response.json().state;
console.log("state:", state);
if (["JobComplete", "Failed", "Aborted"].includes(state)) {
  pm.collectionVariables.set("bulkTerminalState", state);
} else {
  postman.setNextRequest(pm.info.requestName); // re-run this request
}
```

**Request 5 — Pull failed rows for triage**
```
GET {{instanceUrl}}/services/data/{{apiVersion}}/jobs/ingest/{{bulkJobId}}/failedResults
```

**Why it works:** `pm.collectionVariables` survive across requests in the same run. `postman.setNextRequest(pm.info.requestName)` makes request 4 re-run itself until the job reaches a terminal state — no external poll loop needed. The failed-results endpoint returns each rejected row plus the per-row error, which is the visibility the team needed.

---

## Example 3: Composite REST graph for atomic Account+Contact+Opportunity insert

**Context:** A sales-ops engineer needs to insert a related triple (Account, Contact under it, Opportunity for it) and roll back all three if any fails — for example, if a validation rule rejects the Opportunity.

**Problem:** Three sequential POSTs threaded by collection variables work in the happy path but leave dangling Account+Contact records when the Opportunity fails. The triple is not atomic.

**Solution:** One request to `/composite/graph/`.

```
POST {{instanceUrl}}/services/data/{{apiVersion}}/composite/graph/
Content-Type: application/json

{
  "graphs": [{
    "graphId": "g1",
    "compositeRequest": [
      { "method": "POST", "url": "/services/data/{{apiVersion}}/sobjects/Account",
        "referenceId": "AccRef", "body": { "Name": "Acme Corp" } },
      { "method": "POST", "url": "/services/data/{{apiVersion}}/sobjects/Contact",
        "referenceId": "ConRef", "body": { "LastName": "Doe", "AccountId": "@{AccRef.id}" } },
      { "method": "POST", "url": "/services/data/{{apiVersion}}/sobjects/Opportunity",
        "referenceId": "OppRef",
        "body": { "Name": "Acme Q1 Renewal", "AccountId": "@{AccRef.id}",
                  "StageName": "Prospecting", "CloseDate": "2026-06-30" } }
    ]
  }]
}
```

Tests:
```javascript
const result = pm.response.json();
const graph = result.graphs[0];
pm.test("graph committed", () => pm.expect(graph.isSuccessful).to.be.true);
pm.collectionVariables.set("createdAccountId", graph.graphResponse.compositeResponse[0].body.id);
```

**Why it works:** The Composite Graph API guarantees all-or-nothing semantics across the sub-requests within a graph. `@{AccRef.id}` references the Id returned by the AccRef sub-request, threading parent IDs without round-trips. If the Opportunity fails, the Account and Contact never commit.

---

## Anti-Pattern: Hard-coded `instanceUrl` and `apiVersion` baked into every request

**What practitioners do:** Build the collection by copy-pasting `https://mycompany.my.salesforce.com/services/data/v55.0/sobjects/...` into each request's URL. Maybe even commit that to source control "for documentation."

**What goes wrong:** Three failure modes accumulate:

1. **Sandbox refresh changes the subdomain.** After the next refresh, every URL is broken. The team spends an afternoon search-replacing.
2. **API version stays at v55.0 long after Salesforce has shipped v59, v60, v61.** New endpoints and fields aren't accessible. When someone bumps one URL to v59, half the collection is on v55 and half on v59.
3. **Cross-org work means two parallel collections** — one per org — that drift independently. A bug fix in DevSandbox's collection never reaches Prod's.

**Correct approach:** Use environment variables. `{{instanceUrl}}` is set by the pre-request script after auth (the OAuth response carries the authoritative `instance_url`). `{{apiVersion}}` is a per-environment variable defaulted to a known-good version, bumped deliberately. Every request URL becomes `{{instanceUrl}}/services/data/{{apiVersion}}/...`. Switching orgs is a single dropdown change; bumping API versions is a single environment edit.
