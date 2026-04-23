# Apex Encoding And Crypto — Review Worksheet

## Task Context

| Item | Value |
|---|---|
| Purpose | Digest / MAC / Signature / Encryption / Encoding |
| Algorithm | `HmacSHA256` / `RSA-SHA256` / `AES256` / `SHA-256` / other |
| Consumer encoding expected | base64 / base64url / hex (case) / binary |
| Key / cert source | Named Credential / Certificate DeveloperName / Protected CMT / OTHER (flag) |
| Body source | `req.requestBody` / serialized JSON / concatenated string |
| Test vector pinned | Yes / No |

## Review Questions

- [ ] Is the algorithm name a string literal that exactly matches the consumer's spec?
- [ ] Does key material come from a managed store, not a literal?
- [ ] For signatures, is `Crypto.signWithCertificate` used over `Crypto.sign`?
- [ ] For encryption, is `encryptWithManagedIV` used over `encrypt`?
- [ ] Is any MAC / signature comparison wrapped in a constant-time helper?
- [ ] Are JWT segments base64url-encoded (replace `+`/`/`, strip `=`)?
- [ ] Is `Blob.toString()` used on any crypto output?
- [ ] Is `Math.random()` used anywhere security-relevant?

## Findings

| Severity | Finding | Remediation |
|---|---|---|
| | | |
| | | |

## Final Recommendation

Summarize the algorithm, key source, encoding, and test fixture for this code path.
