# Gotchas — Apex Encoding And Crypto

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `EncodingUtil.base64Encode` Always Uses Standard Base64

**What happens:** A JWT assertion signed in Apex is rejected by every OAuth server with `invalid_grant`, even though the signing flow is correct end-to-end.

**When it occurs:** JWT headers, claim sets, and signatures must use URL-safe base64 (base64url, RFC 4648 §5). `EncodingUtil.base64Encode` emits standard base64 with `+`, `/`, and `=` characters that JWT servers reject.

**How to avoid:** After every `base64Encode` on a JWT segment, run `.replace('+', '-').replace('/', '_').replace('=', '')`. The same rule applies to PKCE verifiers, WebPush VAPID claims, and any other RFC 7515/7518 payload.

---

## `Crypto.signWithCertificate` Needs The Cert In Setup, Not A Static Resource

**What happens:** A developer uploads a `.p12` or `.pem` file as a Static Resource, reads it as a `Blob`, and tries to call `Crypto.sign('RSA-SHA256', input, p12Blob)`. UNVERIFIED (2026-10-20): that the call throws or produces an unverifiable signature.

**When it occurs:** `Crypto.sign` takes a private key that "must be decoded using the EncodingUtil base64Decode method, and should be in RSA's PKCS #8 (1.2) Private-Key Information Syntax Standard form", at most 4 KB, with the PEM BEGIN/END lines removed (apexref 262 L204008-204009, L204030-204031). Meanwhile `Crypto.signWithCertificate` takes a certificate DeveloperName (L204053-204059); UNVERIFIED (2026-10-20): that the certificate must live in Setup → Certificate and Key Management.

**How to avoid:** Import the certificate into Setup → Certificate and Key Management and reference it by DeveloperName through `Crypto.signWithCertificate`. This also keeps the private key out of Apex memory entirely.

---

## `Blob.toString()` Is A Cast, Not An Encoding

**What happens:** AES ciphertext or HMAC output is converted to a string with `Blob.toString()` for storage. Round-trip decryption or verification fails. Decryption errors surface as `System.SecurityException` (apexref 262 L203193-203198); the earlier `CryptoException` is not a documented type — CONTRADICTED.

**When it occurs:** `Blob.toString()` takes no argument and "casts the Blob into a String" (apexref 262 L201256-201257). UNVERIFIED (2026-10-20): that the cast is UTF-8 and that the replacement character silently loses information.

**How to avoid:** Always encode cryptographic bytes with `EncodingUtil.base64Encode` or `EncodingUtil.convertToHex` before coercing to `String`. Only call `Blob.toString()` when the blob is known to contain text (e.g. a decrypted plaintext you originally built from `Blob.valueOf(someString)`); there is no encoding argument.

---

## `Crypto.encrypt` Requires A Caller-Provided IV — And IV Reuse Is Catastrophic

**What happens:** A team uses `Crypto.encrypt('AES256', key, iv, plaintext)` with a hardcoded IV (often all zeros). UNVERIFIED (2026-10-20): that under CBC a fixed IV makes identical plaintexts produce identical ciphertexts — the guide states the IV requirements (any 16-byte value, apexref 262 L203560-203562) and the padding-oracle caution for CBC (L203203-203220), not this leak.

**When it occurs:** Any time a developer copies a "how to encrypt in Apex" snippet from a blog that uses a literal 16-byte `Blob.valueOf('0123456789abcdef')` IV.

**How to avoid:** Prefer `Crypto.encryptWithManagedIV`, which prepends a platform-generated random IV to the ciphertext. If you need an explicit IV for protocol interop, supply a fresh 16-byte value per call (`Crypto.generateAesKey(128)` returns a 128-bit key, apexref 262 L203751-203765) and store it alongside the ciphertext — never reuse. For GCM, supply no IV: any non-null IV results in an error (L203562).

---

## `Crypto.generateDigest('SHA1', ...)` Is Not A Security Control

**What happens:** A team uses SHA-1 or MD5 as a "password hash" or "HMAC" in Apex and fails a pen test. Note the documented digest spellings are `MD5`, `SHA1`, `SHA-256`, `SHA-512` and the SHA3 variants (apexref 262 L203811-203817) — `SHA1` has no hyphen.

**When it occurs:** Legacy code; or a developer conflating hash (integrity) with MAC (authenticated integrity) with signature (authenticated non-repudiation).

**How to avoid:** SHA-256 or stronger for digests. `hmacSHA256` or stronger for MACs. `RSA-SHA256` or `ECDSA-SHA256` for signatures. Reserve MD5/SHA-1 for non-security fingerprints (deduplication, cache keys) and comment why.

---

## `EncodingUtil.urlEncode` Double-Encodes If You Encode Twice

**What happens:** A value containing `%20` gets re-encoded to `%2520` and the downstream API rejects it as invalid. This follows from `urlEncode` treating all characters outside A-Z, a-z, 0-9 and `. - * _` as unsafe and encoding them (apexref 262 L214361-214365).

**When it occurs:** A developer calls `EncodingUtil.urlEncode` both in a helper function and again at the point of URL assembly.

**How to avoid:** Encode exactly once, at the latest possible point (when assembling the URL or form body). Read every helper you call to confirm it doesn't already encode.

---

## Hex Case From `EncodingUtil.convertToHex` Is Not Documented

**What happens:** A service that expects uppercase-hex HMAC signatures (some legacy SOAP partners) receives lowercase hex and returns `400 Invalid Signature`. UNVERIFIED (2026-10-20): that `convertToHex` emits lowercase — apexref 262 L214291-214292 does not say; test against a known-good sample.

**When it occurs:** The Apex side generates the MAC correctly but serialization differs in case.

**How to avoid:** Call `.toUpperCase()` on the hex string if the consumer requires uppercase. Always confirm case expectations against a known-good sample signature before declaring the integration complete.

---

## `Blob.valueOf(String)` Encoding Is Not Documented; Other Character Sets Need Explicit Conversion

UNVERIFIED (2026-10-20): that `Blob.valueOf(String)` is UTF-8 — apexref 262 L201258-201259 says only that it "casts the specified String to a Blob".

**What happens:** A MAC computed in Apex doesn't match one computed by a partner running ISO-8859-1 or UTF-16. The partner's body bytes differ for any non-ASCII character.

**When it occurs:** Integrations with older systems (particularly Japanese, German, or cyrillic text) that use non-UTF-8 character encodings.

**How to avoid:** Document the expected byte encoding explicitly. If the partner uses a non-UTF-8 encoding, warn the user that Apex cannot produce those bytes without workarounds (e.g. pre-encoded bodies passed as `Blob` rather than `String`).

---

## `Crypto.getRandomInteger` And `Math.random()` Are Different Qualities

**What happens:** A developer uses `Math.random()` to generate a nonce, session token, or PKCE verifier. A security review flags it as a predictable source.

**When it occurs:** `Math.random()` returns a pseudo-random `Double` (UNVERIFIED (2026-10-20): that it carries no guarantee of cryptographic quality — the corpus documents only that `Crypto.getRandomInteger` and `getRandomLong` call `java.security.SecureRandom`, apexref 262 L203920, L203957).

**How to avoid:** Use `Crypto.getRandomInteger()` or `Crypto.getRandomLong()` for anything security-sensitive. For longer random bytes, generate an AES key via `Crypto.generateAesKey(256)` and slice it (UNVERIFIED (2026-10-20): that the source is cryptographically strong).
