# Webhook Inbound Patterns — Implementation Template

## Webhook Configuration

**Sender system:** ___
**Authentication model:**
- [ ] HMAC shared secret (requires Salesforce Site)
- [ ] OAuth Client Credentials
- [ ] API Key (treat as unauthenticated — add IP allowlist in addition)

**HTTP Method:** POST / GET (circle one — almost always POST)

**Payload format:** JSON / XML / Form-encoded

**Sender timeout:** ___ seconds

## Endpoint Design

**Apex class name:** `___WebhookHandler`

**@RestResource URL mapping:** `/webhook/___`

**Public URL (if Salesforce Site):**
`https://<site-domain>.my.salesforce-sites.com/services/apexrest/webhook/___`

**Org URL (if OAuth):**
`https://<org-domain>/services/apexrest/webhook/___`

## HMAC Verification

- **Header containing signature:** `X-<Sender>-Signature` or `___`
- **Signature format:** `sha256=<hex>` or `___`
- **Shared secret storage:** Custom Metadata type `___`, record DeveloperName `___`
- [ ] Verify over `req.requestBody.toString()` (raw, before JSON parse)
- [ ] Constant-time comparison (`.equals()` — not `==`)

## Idempotency Design

- **Event ID field in payload:** `event.id` / `delivery_id` / `___`
- **Custom object for dedup:** `Webhook_Event__c`
- **External ID field:** `Event_Id__c`
- [ ] Upsert on External ID before processing — skip if `!result.isCreated()`

## Processing Mode

- [ ] Synchronous (processing completes in <3 seconds with no callouts)
- [ ] Async via Queueable (processing > 3 seconds or involves callouts)

**Queueable class name (if async):** `___EventProcessor`

## Salesforce Site Setup (if unauthenticated)

- [ ] Site created at Setup > Sites
- [ ] Site domain configured: `___`
- [ ] Apex class added to Guest User Profile > Apex Class Access
- [ ] Site is Active

## Testing Checklist

- [ ] Valid HMAC signature test: curl with correct signature → returns 200
- [ ] Invalid HMAC signature test: curl with wrong signature → returns 401
- [ ] Duplicate delivery test: same event ID sent twice → second delivery processed without creating duplicate records
- [ ] Timeout test: if async, confirm response returns before Queueable finishes
