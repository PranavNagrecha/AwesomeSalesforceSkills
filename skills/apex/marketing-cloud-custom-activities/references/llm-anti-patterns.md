# LLM Anti-Patterns — Marketing Cloud Custom Activities

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud Custom Activities.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Serving config.json Over HTTP Instead of HTTPS

**What the LLM generates:** Config file endpoints, activity UI URLs, or execute endpoint URLs using `http://` scheme, especially in "getting started" or development examples:
```json
{
  "userInterfaces": {
    "configModal": { "url": "http://myapp.example.com/config.html" }
  },
  "endpoints": {
    "execute": { "url": "http://myapp.example.com/execute" }
  }
}
```

**Why it happens:** LLMs trained on general web development examples often use `http://` in development snippets without noting protocol requirements. Marketing Cloud's strict HTTPS requirement is a platform-specific constraint that generic training data underrepresents.

**Correct pattern:**
```json
{
  "userInterfaces": {
    "configModal": { "url": "https://myapp.example.com/config.html" }
  },
  "endpoints": {
    "execute": { "url": "https://myapp.example.com/execute" }
  }
}
```
All URLs in config.json must use HTTPS. Journey Builder will not load HTTP-only iframe URLs.

**Detection hint:** Scan config.json for any `"url": "http://` patterns. Flag as a hard error.

---

## Anti-Pattern 2: Calling Postmonger trigger Methods Before the ready Event

**What the LLM generates:** customActivity.js that calls `connection.trigger('requestSchema')` at the top level, before registering the `ready` listener:
```javascript
var connection = new Postmonger.Session();

// Wrong: called before ready fires
connection.trigger('requestSchema');

connection.on('ready', function() {
  // This runs too late
});
```

**Why it happens:** LLMs pattern-match on generic event emitter examples where order of initialization does not matter. The Postmonger cross-frame messaging protocol requires a specific handshake sequence that is not obvious from the library name alone.

**Correct pattern:**
```javascript
var connection = new Postmonger.Session();

// Register listeners first
connection.on('ready', function() {
  // Only call triggers after ready fires
  connection.trigger('requestSchema');
});

connection.on('requestedSchema', function(schema) {
  renderFieldPicker(schema.schema);
});

// Signal Journey Builder that the UI has loaded — must come after listener registration
connection.trigger('ready');
```

**Detection hint:** Look for `connection.trigger(` appearing before any `connection.on('ready'` registration in the same file.

---

## Anti-Pattern 3: Returning Non-200 HTTP Status From Execute Endpoint

**What the LLM generates:** Execute endpoints that return HTTP 202 for async acceptance, 201 for created resources, or 204 for no-content responses:
```javascript
// Wrong: 202 Accepted is a reasonable HTTP idiom but breaks Journey Builder
res.status(202).json({ message: 'Processing started' });

// Wrong: returning 204 after async enqueue
res.sendStatus(204);
```

**Why it happens:** LLMs draw on standard REST API design conventions where 202 is the correct code for "accepted for async processing" and 201 for "resource created." Journey Builder's requirement for exactly HTTP 200 deviates from standard REST semantics and is a platform-specific constraint.

**Correct pattern:**
```javascript
// Always return exactly 200 — Journey Builder advances the contact only on 200
res.status(200).json({ status: 'queued' });

// For custom splits, include branchResult in the 200 response
res.status(200).json({ branchResult: 'high_value' });
```

**Detection hint:** Search execute endpoint handler code for `res.status(2` followed by any digit other than `0` (i.e., `res.status(201`, `res.status(202`, `res.status(204`). Also flag `res.sendStatus(201)`, `res.sendStatus(202)`, `res.sendStatus(204)`.

---

## Anti-Pattern 4: Omitting JWT Verification on Execute Endpoint

**What the LLM generates:** Execute endpoint implementations that skip token verification, often with a comment like "add auth later" or that check only for the presence of a header without verifying its signature:
```javascript
app.post('/execute', async (req, res) => {
  // Skipped: JWT verification
  const { inArguments } = req.body;
  // Process directly...
  res.status(200).json({ status: 'ok' });
});
```

**Why it happens:** LLMs prioritize demonstrating the core logic (processing contact data, returning branchResult) and treat authentication as boilerplate to be added later. In tutorial-style generation, auth is often omitted to keep examples short.

**Correct pattern:**
```javascript
const jwt = require('jsonwebtoken');

function verifyJwt(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing token' });
  }
  const token = authHeader.split(' ')[1];
  try {
    // Use the Installed Package secret as the signing key
    jwt.verify(token, process.env.MC_APP_SIGNATURE);
    next();
  } catch (err) {
    return res.status(403).json({ error: 'Invalid token' });
  }
}

app.post('/execute', verifyJwt, async (req, res) => {
  const { inArguments } = req.body;
  // Safe to process — caller is verified
  res.status(200).json({ status: 'ok' });
});
```

**Detection hint:** Search execute route handler for absence of JWT verification middleware or `jwt.verify(` call. Flag any execute handler that processes `req.body` without a prior auth check.

---

## Anti-Pattern 5: Missing or Incorrect branchResult Key for Custom Splits

**What the LLM generates:** Custom split execute endpoints that return a human-readable label instead of the outcome key, return an unrelated field name, or omit the branchResult field entirely:
```javascript
// Wrong: returning the label instead of the key
res.status(200).json({ outcome: 'Gold Member' });

// Wrong: wrong field name
res.status(200).json({ branch: 'gold' });

// Wrong: omitting branchResult entirely
res.status(200).json({ tier: 'gold', processed: true });
```

**Why it happens:** LLMs infer field names from context and may use `outcome`, `branch`, `result`, or the label value rather than the exact field name `branchResult` with the exact key string. The exact contract (`branchResult` containing the exact key from config.json outcomes) is not self-evident from general API design training.

**Correct pattern:**
```javascript
// config.json declares: { "key": "gold", "label": "Gold Member" }
// Execute endpoint must return the key, not the label, in the field named branchResult
res.status(200).json({ branchResult: 'gold' });
```

**Detection hint:** In custom split execute handlers, check that the response JSON object uses exactly `branchResult` as the field name and that the value is one of the string keys (not labels) declared in config.json `metaData.outcomes`. Flag `outcome`, `branch`, `result`, `splitResult`, or any label value ("Gold Member", "Platinum Member") appearing as a response field or value.

---

## Anti-Pattern 6: Synchronous Blocking Operations in Execute Handler

**What the LLM generates:** Execute handlers that await slow external API calls synchronously before returning:
```javascript
app.post('/execute', verifyJwt, async (req, res) => {
  // Wrong: awaiting a potentially slow external call
  const apiResult = await externalCrmApi.updateContact(req.body.inArguments);
  const loyaltyTier = await loyaltyPlatform.getTier(req.body.keyValue);
  // If either call takes >30s, Journey Builder times out and errors the contact
  res.status(200).json({ branchResult: loyaltyTier });
});
```

**Why it happens:** LLMs default to the simplest linear async/await pattern. The Journey Builder 30-second timeout constraint and its "no retry on timeout" behavior are platform-specific knowledge not present in generic web API training data.

**Correct pattern:**
```javascript
app.post('/execute', verifyJwt, async (req, res) => {
  // Enqueue the work — do not await the slow external call
  await workQueue.push({
    contactKey: req.body.keyValue,
    arguments: req.body.inArguments
  });
  // Return immediately — background worker handles the rest
  res.status(200).json({ status: 'queued' });
});
```
For custom splits requiring real-time routing: apply a strict internal timeout (e.g., 5 seconds) on downstream calls and return a safe fallback branchResult on timeout rather than letting the Journey Builder timeout fire.

**Detection hint:** In execute handlers, flag any `await` call to an external service (HTTP client, database, Salesforce API) that is not wrapped in a short timeout or not preceded by an immediate `res.status(200)` response.
