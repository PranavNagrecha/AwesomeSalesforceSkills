# Gotchas — Apex Encoding And Crypto

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `EncodingUtil.base64Encode` Always Uses Standard Base64

**What happens:** A JWT assertion signed in Apex is rejected by every OAuth server with `invalid_grant`, even though the signing flow is correct end-to-end.

**When it occurs:** JWT headers, claim sets, and signatures must use URL-safe base64 (base64url, RFC 4648 §5). `EncodingUtil.base64Encode` emits standard base64 with `+`, `/`, and `=` characters that JWT servers reject.

**How to avoid:** After every `base64Encode` on a JWT segment, run `.replace('+', '-').replace('/', '_').replace('=', '')`. The same rule applies to PKCE verifiers, WebPush VAPID claims, and any other RFC 7515/7518 payload.

---

## `Crypto.signWithCertificate` Needs The Cert In Setup, Not A Static Resource

**What happens:** A developer uploads a `.p12` or `.pem` file as a Static Resource, reads it as a `Blob`, and tries to call `Crypto.sign('RSA-SHA256', input, p12Blob)`. The call throws or produces an unverifiable signature.

**When it occurs:** `Crypto.sign` with a raw private-key blob expects a DER-encoded PKCS#8 private key — not a `.p12` container, not a PEM-wrapped key. Meanwhile `Crypto.signWithCertificate` requires the certificate to live in Setup → Certificate and Key Management.

**How to avoid:** Import the certificate into Setup → Certificate and Key Management and reference it by DeveloperName through `Crypto.signWithCertificate`. This also keeps the private key out of Apex memory entirely.

---

## `Blob.toString()` Corrupts Non-UTF-8 Bytes

**What happens:** AES ciphertext or HMAC output is converted to a string with `Blob.toString()` for storage. Round-trip decryption or verification fails with a `CryptoException` or a mismatched MAC.

**When it occurs:** `Blob.toString()` (no argument) defaults to UTF-8. Random cryptographic bytes are almost never valid UTF-8, so the Unicode replacement character is substituted and information is lost silently.

**How to avoid:** Always encode cryptographic bytes with `EncodingUtil.base64Encode` or `EncodingUtil.convertToHex` before coercing to `String`. Only call `Blob.toString('UTF-8')` when the blob is known to contain UTF-8 text (e.g. a decrypted plaintext you originally built from `Blob.valueOf(someString)`).

---

## `Crypto.encrypt` Requires A Caller-Provided IV — And IV Reuse Is Catastrophic

**What happens:** A team uses `Crypto.encrypt('AES256', key, iv, plaintext)` with a hardcoded IV (often all zeros). Under CBC mode, identical plaintexts produce identical ciphertexts, leaking equality of record fields across the dataset.

**When it occurs:** Any time a developer copies a "how to encrypt in Apex" snippet from a blog that uses a literal 16-byte `Blob.valueOf('0123456789abcdef')` IV.

**How to avoid:** Prefer `Crypto.encryptWithManagedIV`, which prepends a platform-generated random IV to the ciphertext. If you need an explicit IV for protocol interop, generate it with `Crypto.generateAesKey(128)` (truncated to 16 bytes) per call and store it alongside the ciphertext — never reuse.

---

## `Crypto.generateDigest('SHA-1', ...)` Is Not A Security Control

**What happens:** A team uses SHA-1 or MD5 as a "password hash" or "HMAC" in Apex and fails a pen test.

**When it occurs:** Legacy code; or a developer conflating hash (integrity) with MAC (authenticated integrity) with signature (authenticated non-repudiation).

**How to avoid:** SHA-256 or stronger for digests. `HmacSHA256` or stronger for MACs. `RSA-SHA256` or `ECDSA-SHA256` for signatures. Reserve MD5/SHA-1 for non-security fingerprints (deduplication, cache keys) and comment why.

---

## `EncodingUtil.urlEncode` Double-Encodes If You Encode Twice

**What happens:** A value containing `%20` gets re-encoded to `%2520` and the downstream API rejects it as invalid.

**When it occurs:** A developer calls `EncodingUtil.urlEncode` both in a helper function and again at the point of URL assembly.

**How to avoid:** Encode exactly once, at the latest possible point (when assembling the URL or form body). Read every helper you call to confirm it doesn't already encode.

---

## Hex Output From `EncodingUtil.convertToHex` Is Lowercase

**What happens:** A service that expects uppercase-hex HMAC signatures (some legacy SOAP partners) receives lowercase hex and returns `400 Invalid Signature`.

**When it occurs:** The Apex side generates the MAC correctly but serialization differs in case.

**How to avoid:** Call `.toUpperCase()` on the hex string if the consumer requires uppercase. Always confirm case expectations against a known-good sample signature before declaring the integration complete.

---

## `Blob.valueOf(String)` Is UTF-8; Other Character Sets Need Explicit Conversion

**What happens:** A MAC computed in Apex doesn't match one computed by a partner running ISO-8859-1 or UTF-16. The partner's body bytes differ for any non-ASCII character.

**When it occurs:** Integrations with older systems (particularly Japanese, German, or cyrillic text) that use non-UTF-8 character encodings.

**How to avoid:** Document the expected byte encoding explicitly. If the partner uses a non-UTF-8 encoding, warn the user that Apex cannot produce those bytes without workarounds (e.g. pre-encoded bodies passed as `Blob` rather than `String`).

---

## `Crypto.getRandomInteger` And `Math.random()` Are Different Qualities

**What happens:** A developer uses `Math.random()` to generate a nonce, session token, or PKCE verifier. A security review flags it as a predictable source.

**When it occurs:** `Math.random()` returns a pseudo-random `Double` with no platform guarantee of cryptographic quality.

**How to avoid:** Use `Crypto.getRandomInteger()` or `Crypto.getRandomLong()` for anything security-sensitive. For longer random bytes, generate an AES key via `Crypto.generateAesKey(256)` and slice it — the underlying source is cryptographically strong.
