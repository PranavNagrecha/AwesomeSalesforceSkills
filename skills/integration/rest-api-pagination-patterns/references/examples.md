# Examples — REST API Pagination Patterns

Two worked scenarios and one anti-pattern showing how to walk a
Salesforce REST query response correctly, when to tune the per-page
batch with `Sforce-Query-Options`, and why SOQL `OFFSET` is the
wrong primitive for production pagination beyond a handful of pages.
Examples use Salesforce REST API v60.0 endpoints; substitute the
version supported by your org's API enablement.

---

## Example 1: Walking `/services/data/v60.0/query` with `nextRecordsUrl` until exhausted

**Context:** A nightly export job reads every Opportunity created in
the last 90 days into a downstream data warehouse. Volume is around
85,000 rows — well past the default 2,000-record page boundary that
the REST query resource returns in a single response.

**Problem:** A caller that issues `/query?q=...` and processes only
the `records` array silently truncates at the first page. No 4xx,
no warning — just an apparent "the warehouse is missing rows" bug
discovered weeks later by a sales-ops analyst.

**Solution:** The first call returns a response shaped like:

```json
{
  "totalSize": 85217,
  "done": false,
  "nextRecordsUrl": "/services/data/v60.0/query/01g3X00000ABcDeQAA-2000",
  "records": [ /* up to batchSize records */ ]
}
```

Loop until `done == true`. The `nextRecordsUrl` value is a
server-managed query locator that already encodes the original
query, the cursor offset (the suffix after the dash, here `-2000`),
and the original `Sforce-Query-Options` batch size. Do NOT
re-construct the URL by hand and do NOT re-send the original SOQL
on follow-up calls.

**Curl walk:**

```bash
# Page 1 — initial query
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Sforce-Query-Options: batchSize=500" \
  "https://$INSTANCE.salesforce.com/services/data/v60.0/query/?q=SELECT+Id,Name,StageName,Amount,CreatedDate+FROM+Opportunity+WHERE+CreatedDate=LAST_N_DAYS:90+ORDER+BY+Id"

# Response body — abbreviated
# {
#   "totalSize": 85217,
#   "done": false,
#   "nextRecordsUrl": "/services/data/v60.0/query/01g3X00000ABcDeQAA-500",
#   "records": [ ...500 records... ]
# }

# Page 2 — follow nextRecordsUrl verbatim, prepend instance host
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://$INSTANCE.salesforce.com/services/data/v60.0/query/01g3X00000ABcDeQAA-500"

# Continue until response contains "done": true
```

**Apex callout (Queueable-chainable) skeleton:**

```apex
public class OppExportPager implements Queueable, Database.AllowsCallouts {
    String nextPath;            // null on first run; nextRecordsUrl on subsequent
    Integer pageCount;

    public OppExportPager(String nextPath, Integer pageCount) {
        this.nextPath = nextPath;
        this.pageCount = pageCount;
    }

    public void execute(QueueableContext qc) {
        HttpRequest req = new HttpRequest();
        String path = (nextPath != null)
            ? nextPath
            : '/services/data/v60.0/query/?q=' +
              EncodingUtil.urlEncode(
                'SELECT Id, Name, StageName, Amount FROM Opportunity ' +
                'WHERE CreatedDate = LAST_N_DAYS:90 ORDER BY Id', 'UTF-8');
        req.setEndpoint('callout:My_SF_Named_Cred' + path);
        req.setMethod('GET');
        req.setHeader('Sforce-Query-Options', 'batchSize=500');

        HttpResponse res = new Http().send(req);
        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());

        List<Object> records = (List<Object>) body.get('records');
        OppExportSink.persist(records);  // pushes to staging table

        Boolean done = (Boolean) body.get('done');
        String next = (String) body.get('nextRecordsUrl');

        // Safety cap — see llm-anti-patterns.md anti-pattern 1
        if (!done && pageCount < 1000 && !Test.isRunningTest()) {
            System.enqueueJob(new OppExportPager(next, pageCount + 1));
        }
    }
}
```

**Why it works:** The `done` flag is the authoritative termination
signal. `nextRecordsUrl` is opaque — the suffix after the locator id
(`-500`, `-1000`, ...) increments by the negotiated `batchSize`, so
the URL itself carries the page-boundary state. Chaining via
Queueable sidesteps the 100-callout-per-transaction governor; each
chained execution has its own callout budget.

---

## Example 2: Tuning per-page size with `Sforce-Query-Options: batchSize=N`

**Context:** Same Opportunity export. The integration runs over a
private VPN with high per-request latency (~600 ms round trip), and
the receiving warehouse has a memory ceiling of 50 MB per ingestion
buffer.

**Problem:** The default page size is 200 records (the REST API's
historical default per the SOAP-era `QueryOptions` semantics
inherited by REST). At default, exporting 85,000 records is
`ceil(85000 / 200) = 425` round trips. At 600 ms each, the pure
network cost alone is ~4 minutes — and every page consumes one
daily API call (see `gotchas.md` gotcha 4).

**Solution:** Send the `Sforce-Query-Options` request header on
the *first* call to set the per-page batch size. The negotiated
size sticks for every `nextRecordsUrl` follow-up tied to that
locator — you do NOT re-send the header on follow-ups.

```bash
# Tune to 2000 (the documented maximum)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Sforce-Query-Options: batchSize=2000" \
  "https://$INSTANCE.salesforce.com/services/data/v60.0/query/?q=SELECT+Id,Name+FROM+Opportunity"
```

Salesforce treats `batchSize` as advisory — the platform may return
fewer records than requested when row payload weight (CLOB fields,
nested relationships, large rich-text) pushes the response above
internal serialization thresholds. The accepted range is **200
(minimum) to 2000 (maximum)**; values outside the range are
clamped, not errored.

**Tradeoffs:**

| batchSize | Round trips for 85K rows | Per-request payload | Failure cost |
|-----------|--------------------------|---------------------|--------------|
| 200 (default) | 425 | small (~200 KB JSON) | low — retry one page |
| 500 | 170 | ~500 KB | low |
| 1000 | 85 | ~1 MB | medium |
| 2000 (max) | 43 | ~2-4 MB | high — losing a page redoes 2000 rows; warehouse buffer near 50 MB ceiling |

**Why it works:** Smaller batches mean more round trips and more
daily API calls but smaller per-request memory and faster recovery
on a single-page failure. Larger batches reduce round trips and
API-call consumption but raise per-request memory pressure on both
sides and amplify the cost of a retried page. The sweet spot for
most warehouse-egress jobs is 500-1000; reserve 2000 for low-field
projections on stable schemas.

---

## Anti-Pattern: Paginating with SOQL `OFFSET`

**What practitioners do:**

```apex
// Page through Opportunities 200 at a time using OFFSET
for (Integer page = 0; page < 100; page++) {
    List<Opportunity> chunk = [
        SELECT Id, Name, StageName, Amount
        FROM Opportunity
        WHERE CreatedDate = LAST_N_DAYS:90
        ORDER BY CreatedDate DESC
        LIMIT 200
        OFFSET :(page * 200)
    ];
    if (chunk.isEmpty()) break;
    process(chunk);
}
```

The REST equivalent — same shape, same failure:

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://$INSTANCE.salesforce.com/services/data/v60.0/query/?q=SELECT+Id+FROM+Opportunity+ORDER+BY+CreatedDate+LIMIT+200+OFFSET+2200"
# Response:
# [{
#   "message": "OFFSET 2200 is outside of the valid range.",
#   "errorCode": "NUMBER_OUTSIDE_VALID_RANGE"
# }]
```

**What goes wrong:** Two distinct failures, both production-impacting.

1. **The hard cap at OFFSET 2000.** SOQL caps the OFFSET clause at
   2,000 rows total. Any query that includes `OFFSET 2001` or higher
   throws `NUMBER_OUTSIDE_VALID_RANGE`. The loop above succeeds for
   the first 11 iterations (offsets 0, 200, 400, ..., 2000) then
   throws on iteration 12 (`OFFSET 2200`). For an 85K-row export
   the pattern reads at most 2,200 records before exception — the
   remaining 82,800 are silently lost if the exception is swallowed.
2. **Drift on concurrent writes.** Even within the 0-2000 valid
   range, a record inserted between page 1 and page 2 shifts every
   subsequent row index by one. The record that *was* at offset 200
   moves to offset 201; the page-2 caller now reads offset 200-399,
   which begins with the record that was previously at offset 199
   — a duplicate. Deletes cause the symmetric miss.

**Correct approach:** Use one of three Salesforce-supported
pagination primitives, picked by total volume:

1. **`nextRecordsUrl` cursor walk** (Example 1 above) — for any
   query returning more than 2,000 rows and where a single
   transaction or chained Queueable can carry the cursor. Cursor
   expires after ~15 minutes; restart on expiry.
2. **Keyset pagination on `Id`** — for resumable, restart-tolerant
   walks where the 15-minute cursor TTL is too tight, or where the
   pagination state must survive across days or workflows:

   ```apex
   Id lastId = '000000000000000';   // sentinel — every real Id sorts after this
   for (Integer page = 0; page < 10000; page++) {
       List<Opportunity> chunk = [
           SELECT Id, Name
           FROM Opportunity
           WHERE Id > :lastId
           ORDER BY Id
           LIMIT 200
       ];
       if (chunk.isEmpty()) break;
       process(chunk);
       lastId = chunk[chunk.size() - 1].Id;
   }
   ```

   `Id` is a guaranteed-unique, monotonically-comparable key with no
   2000-row cap. Persist `lastId` to a Custom Setting or platform
   cache for cross-transaction resumability.
3. **Bulk API 2.0 query job** — for one-shot extracts of millions
   of rows. Uses `Sforce-Locator` response header instead of
   `nextRecordsUrl`; see `well-architected.md` for the tradeoff
   matrix and `gotchas.md` gotcha 3 for the API surface difference.
