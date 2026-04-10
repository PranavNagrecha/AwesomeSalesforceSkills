# Examples — Marketing Cloud Custom Activities

## Example 1: Custom Activity That Writes to an External CRM

**Context:** A retailer wants Journey Builder to post a "Journey Entered" event to their Salesforce Sales Cloud org whenever a contact enters a re-engagement journey. The external write happens asynchronously; Journey Builder should not wait for Salesforce to confirm.

**Problem:** A developer implements the execute endpoint synchronously — it calls the Salesforce REST API inline, waits for the response, then returns 200. During peak load, Salesforce API response times spike beyond 30 seconds. Journey Builder times out, marks contacts as errored, and the entire journey activation fails for thousands of contacts.

**Solution:**

config.json (relevant excerpt):
```json
{
  "workflowApiVersion": "1.1",
  "metaData": {
    "icon": "images/activity-icon.png",
    "category": "message"
  },
  "configurationArguments": {
    "save": { "url": "https://myapp.example.com/jtb/save" },
    "publish": { "url": "https://myapp.example.com/jtb/publish" },
    "validate": { "url": "https://myapp.example.com/jtb/validate" }
  },
  "userInterfaces": {
    "configModal": {
      "url": "https://myapp.example.com/jtb/config.html",
      "height": 200,
      "width": 400
    }
  },
  "endpoints": {
    "execute": { "url": "https://myapp.example.com/jtb/execute", "timeout": 30000 }
  }
}
```

Execute endpoint (Node.js pseudocode):
```javascript
app.post('/jtb/execute', verifyJwt, async (req, res) => {
  const { inArguments, keyValue, definitionInstanceId } = req.body;

  // Enqueue the work — do NOT await the Salesforce API call
  await queue.push({
    contactKey: keyValue,
    journeyId: definitionInstanceId,
    payload: inArguments
  });

  // Return 200 immediately — Journey Builder advances the contact
  res.status(200).json({ status: 'queued' });
});

// Background worker processes the queue and calls Salesforce REST API
```

**Why it works:** The execute endpoint returns HTTP 200 within milliseconds by only enqueuing the work. Journey Builder advances the contact. The background worker calls Salesforce asynchronously without any timeout pressure. If the Salesforce API call fails, the worker can retry independently without impacting the journey.

---

## Example 2: Custom Split Activity Routing by Loyalty Tier

**Context:** A travel company wants to route journey contacts to different branches based on their real-time loyalty tier fetched from an external loyalty platform API. Loyalty data is updated in real time and is not pre-loaded into Marketing Cloud Data Extensions.

**Problem:** A Decision Split activity requires the loyalty tier field to already be in a sendable Data Extension at journey entry time. Because the loyalty platform updates in real time (and sometimes after the contact enters the journey), pre-loaded DE data is stale. Contacts are routed to the wrong branch.

**Solution:**

config.json outcomes definition:
```json
{
  "metaData": {
    "icon": "images/loyalty-icon.png",
    "category": "flow",
    "outcomes": [
      { "key": "platinum",  "label": "Platinum Member" },
      { "key": "gold",      "label": "Gold Member" },
      { "key": "standard",  "label": "Standard Member" },
      { "key": "unknown",   "label": "Tier Unknown" }
    ]
  }
}
```

Execute endpoint with branchResult:
```javascript
app.post('/loyalty/execute', verifyJwt, async (req, res) => {
  const { inArguments } = req.body;
  const loyaltyMemberId = inArguments[0]?.loyaltyMemberId;

  let tier = 'unknown';
  try {
    const loyaltyResponse = await loyaltyApi.getTier(loyaltyMemberId);
    // loyaltyApi must respond quickly; apply a short internal timeout
    tier = loyaltyResponse.tier || 'unknown';
  } catch (err) {
    // On any error, route to 'unknown' branch rather than failing the contact
    tier = 'unknown';
  }

  // branchResult key must exactly match a key declared in metaData.outcomes
  res.status(200).json({ branchResult: tier });
});
```

customActivity.js (Postmonger initialization):
```javascript
var connection = new Postmonger.Session();

connection.on('ready', function() {
  // Only safe to call trigger methods after 'ready' fires
  connection.trigger('requestSchema');
});

connection.on('requestedSchema', function(schema) {
  // Populate field pickers in the UI using schema.schema
  renderFieldPicker(schema.schema);
});

connection.on('updatedActivity', function(activity) {
  // Journey Builder calls this when the practitioner saves
  // Persist the selected loyaltyMemberId field mapping
  currentActivity = activity;
});

// Signal Journey Builder that the UI has loaded — must be last
connection.trigger('ready');
```

**Why it works:** Outcomes defined in config.json are the only valid branch keys. The execute endpoint always returns one of those keys (with `unknown` as the safe fallback), so contacts always have a branch to follow and never error out due to an unrecognized key. The loyalty API is called inside the execute handler with a fallback — the contact is never stranded.

---

## Anti-Pattern: Triggering requestSchema Before ready

**What practitioners do:** To initialize the UI quickly, developers call `connection.trigger('requestSchema')` at the top of customActivity.js, before registering the `ready` listener or before Journey Builder has fired the `ready` event.

**What goes wrong:** Postmonger's cross-frame messaging session is not initialized until Journey Builder sends the `ready` event. Calling `trigger('requestSchema')` before `ready` fires sends the message into an uninitialized channel — it is silently dropped. The `requestedSchema` callback never fires, the schema is never populated, and any field mapping UI in the activity remains empty. The bug is invisible in browser console logs because Postmonger does not throw errors for dropped triggers.

**Correct approach:** Register all event listeners first, then call `connection.trigger('ready')` to begin the handshake. Wait for Journey Builder to fire the `ready` event, then call `connection.trigger('requestSchema')` inside the `ready` handler.
