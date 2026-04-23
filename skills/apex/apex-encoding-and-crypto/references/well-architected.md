# Well-Architected Notes — Apex Encoding And Crypto

## Relevant Pillars

### Security

This skill lives at the Security boundary. Wrong algorithm choice, misplaced keys, or a non-constant-time comparison turns a compliant-looking code path into a cryptographic vulnerability.

Tag findings as Security when:
- algorithm is MD5/SHA-1 or `HmacMD5`/`HmacSHA1` in a security-relevant role
- key material is hardcoded in Apex or a Static Resource
- a MAC or signature comparison uses `==` on the raw value without a constant-time wrapper
- `Crypto.encrypt` is used with a fixed IV or a reused IV across calls
- `Math.random()` is used for a nonce, token, or PKCE verifier

### Reliability

Encoding bugs silently corrupt data. `Blob.toString()` on non-UTF-8 bytes, or base64-vs-base64url confusion, show up as opaque "invalid signature" failures that are expensive to reproduce.

Tag findings as Reliability when:
- a `Blob` carrying cryptographic output is coerced to `String` without base64/hex encoding
- a JWT segment uses standard base64 rather than base64url
- hex case assumptions differ between producer and consumer
- `EncodingUtil.urlEncode` is called twice on the same value

### Operational Excellence

Key rotation is the main operational concern here. A working signing path that hardcodes the key ID or certificate DeveloperName breaks silently at rotation time.

Tag findings as Operational Excellence when:
- cert or key IDs are string literals spread across multiple classes rather than resolved via a `SecretProvider` seam
- no test fixture exists to pin the algorithm's output against a known-answer vector (RFC 4231 for HMAC, RFC 7519 for JWT)

## Architectural Tradeoffs

- **`Crypto.sign` vs `Crypto.signWithCertificate`:** the raw-key form is more flexible (any PKCS#8 key) but exposes the key bytes to Apex memory. The certificate form keeps the key in the platform's secure store and is the correct default for long-lived service credentials.
- **`Crypto.encrypt` vs `Crypto.encryptWithManagedIV`:** managed IV is simpler and safer; the explicit form is only correct when protocol interop requires a caller-framed IV.
- **Shield Platform Encryption vs application-level AES:** Shield encrypts at the field-storage layer and is FIPS-validated; application-level AES is a crutch when Shield is not licensed and comes with the full responsibility of key management, IV management, and key rotation.
- **Constant-time compare via double-hash vs byte-XOR:** the double-hash approach is readable but costs two SHA-256 operations; the XOR approach is faster but harder to get right. For webhook paths the double-hash form is the right default.

## Anti-Patterns

1. **Hardcoded keys in Apex** — the single most common finding in any Apex crypto review.
2. **`Blob.toString()` on crypto output** — silent corruption that only manifests at decryption or verification time.
3. **Standard base64 in JWTs** — `invalid_grant` at 2 AM during a credential rotation.
4. **`==` on MACs or signatures** — timing oracle that looks correct in tests and fails in prod under adversarial conditions.

## Official Sources Used

- Apex Developer Guide — Crypto Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Crypto.htm
- Apex Developer Guide — EncodingUtil Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_EncodingUtil.htm
- Certificate And Key Management: https://help.salesforce.com/s/articleView?id=sf.security_keys_about.htm&type=5
- OAuth 2.0 JWT Bearer Flow: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5
- RFC 4231 (HMAC test vectors) and RFC 7519 (JWT) — for test pinning
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
