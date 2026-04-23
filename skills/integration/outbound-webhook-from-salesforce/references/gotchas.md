# Outbound Webhook — Gotchas

## 1. Callouts Are Not Allowed After DML In A Transaction

Move callouts async (Queueable / @future with callout=true) or pattern
Platform Event → trigger → Queueable.

## 2. Flow HTTP Callout Has No Built-In Retry

Fault path catches errors but there is no retry primitive. Write your own
via Delivery custom object + scheduled Apex.

## 3. Named Credential External Credential For Secrets

Custom Metadata storing the secret in plaintext is a compliance risk. Use
External Credential with OAuth/Custom headers.

## 4. Signed Payload Order Matters

Consumer must compute HMAC over the EXACT byte sequence your producer
signed. Document canonical form and test round-trip.

## 5. 24h Callout Timeout Is Not The Only Limit

Per-callout timeout is 120s max; daily callout allocation is bounded;
max request/response size limits exist.

## 6. Retry-After Header Is Not A Suggestion

For 429 responses, honor Retry-After; backoff bursts will cause more 429s
and amplify the outage.

## 7. IP Allowlisting On The Receiver

Salesforce egress IPs vary; provide receivers with the published IP
ranges, or use a static-IP gateway like MuleSoft / private connect.
