---
name: apex-encoding-and-crypto
description: "Use when Apex must sign, verify, encrypt, hash, encode, or decode payloads — including HMAC for webhook signatures, RSA/ECDSA signing for JWT bearer flows, AES for stored secrets, base64/hex/URL encoding, and digest comparisons for integration integrity. Triggers: 'Crypto.sign', 'Crypto.generateMac', 'EncodingUtil.base64Encode', 'JWT signing in Apex', 'verify webhook signature'. NOT for where the signing key or API secret is stored — use apex/apex-secrets-and-protected-cmdt. NOT for setting up Named Credentials or OAuth flows end-to-end — use apex/apex-named-credentials-patterns. NOT for SOQL injection defense — use apex/soql-security."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - apex-encoding-and-crypto
  - hmac
  - jwt-signing
  - base64
  - encoding-util
  - crypto-class
triggers:
  - "how do I verify an HMAC-SHA256 webhook signature in Apex"
  - "signing a JWT assertion for OAuth 2.0 JWT bearer flow from Apex"
  - "AES encrypt a secret before storing it in a custom field"
  - "EncodingUtil base64 vs urlEncode vs hex decision"
  - "compare two digests without a timing leak in Apex"
inputs:
  - "the payload type (bytes, string, record field) and desired algorithm"
  - "whether the key material lives in Named Credential, Protected Custom Metadata, or Certificate"
  - "the downstream consumer's expected encoding (base64, base64url, hex)"
outputs:
  - "a code path using Crypto / EncodingUtil with the right algorithm, key source, and encoding"
  - "review findings for weak algorithms, non-constant-time comparisons, or hardcoded keys"
  - "a test plan that pins known-answer vectors for the chosen algorithm"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Encoding And Crypto

Use this skill when Apex code must sign, verify, hash, encrypt, or encode bytes — for integration signatures, JWT assertions, webhook verification, token obfuscation, or payload normalization. The purpose is to pick the right algorithm, pull key material from a managed source, and encode the output in the exact form the downstream consumer expects.

---

## Before Starting

Gather this context before writing any `Crypto` or `EncodingUtil` call:

- What is the **algorithm** the other side actually uses? HMAC-SHA256, RSA-SHA256, AES-256-CBC, and SHA-512 all need different `Crypto` method names and payload shapes. An HMAC is not a digest; a digest is not a signature.
- Where is the **key material**? A hardcoded `'my-secret'` literal in Apex fails every security review. Key material should come from a Named Credential (for HMAC shared secrets), a protected Custom Metadata record, or a Certificate stored in Setup (for RSA/ECDSA private keys signed via `Crypto.signWithCertificate`).
- What **encoding** does the consumer want? Base64 and base64url differ in three characters. Hex is lowercase by default. URL-form-encoded bodies need `EncodingUtil.urlEncode(value, 'UTF-8')`, not bare concatenation.
- Do you need a **constant-time comparison**? String equality (`==`) short-circuits and leaks bytes to an attacker timing the response. Use `Crypto.getRandomInteger` plus byte-wise loop, or compare full SHA-256 digests of both values instead of the raw HMACs.

---

## Core Concepts

### `Crypto` Does Symmetric And Asymmetric Work — With Different Methods

`Crypto.generateDigest(algorithmName, input)` produces a plain hash (MD5, SHA1, SHA-256, SHA-512). Hashes are not signatures — anyone can recompute them. Use them for integrity checks on non-adversarial payloads (deduplication, cache keys, file fingerprints).

`Crypto.generateMac(algorithmName, input, privateKey)` produces an HMAC keyed by a shared secret. The Apex Crypto reference documents exactly four valid values, spelled with a lowercase `hmac` prefix:

| Documented value | Use |
|---|---|
| `hmacMD5` | Legacy interop only — broken for security purposes |
| `hmacSHA1` | Legacy interop only |
| `hmacSHA256` | Default choice for new work |
| `hmacSHA512` | When the counterparty specifies it |

**There is no `hmacSHA384`.** SHA-384 exists in the Crypto class only for *asymmetric signatures* (`RSA-SHA384`, `ECDSA-SHA384` via `sign` / `signWithCertificate`), never for MACs, and `generateDigest` has no SHA-384 either (it offers `MD5`, `SHA1`, `SHA-256`, `SHA-512`, `SHA3-256`, `SHA3-384`, `SHA3-512`). If a counterparty genuinely requires HMAC-SHA-384: renegotiate to `hmacSHA256`/`hmacSHA512`, or move the MAC step outside Apex (middleware, an external service behind a Named Credential). Do **not** substitute a different algorithm and hope — the MAC will simply not verify. Do not reach for `SHA3-384` as a stand-in: that is an unkeyed digest, not an HMAC.

`algorithmName` is a plain `String` checked at run time, not by the compiler, so a misspelled or unsupported name ships clean and fails in production. Use the documented spelling verbatim. HMACs are the right tool for webhook verification and request signing against a shared secret (Stripe, Slack, Twilio, GitHub all use HMAC-SHA256).

`Crypto.sign(algorithmName, input, privateKey)` produces an asymmetric signature using a raw private key blob. `Crypto.signWithCertificate(algorithmName, input, certDevName)` uses a certificate stored in Setup → Certificate and Key Management — this is the right pattern for OAuth 2.0 JWT bearer flow because the private key stays in the platform-managed certificate store and never appears as a literal in Apex.

`Crypto.encrypt` / `Crypto.decrypt` perform AES encryption with `AES128`, `AES192`, or `AES256` in CBC mode with an explicit IV. `Crypto.encryptWithManagedIV` / `decryptWithManagedIV` let the platform generate and prepend the IV. Salesforce Shield Platform Encryption is a separate, superior capability for encrypting standard field storage — use it when the requirement is "the admin should never see this field" rather than wrapping `Crypto.encrypt` around every DML.

### `EncodingUtil` Is For Bytes-To-Text And Text-To-Text

`EncodingUtil.base64Encode(Blob)` / `EncodingUtil.base64Decode(String)` convert between bytes and standard base64. There is **no** `base64UrlEncode` method — if the consumer wants base64url (JWT headers, WebPush), post-process: replace `+` with `-`, `/` with `_`, and strip `=` padding.

`EncodingUtil.convertToHex(Blob)` returns lowercase hex. Downstream consumers that want uppercase must `.toUpperCase()` the result. `EncodingUtil.convertFromHex(String)` is the reverse.

`EncodingUtil.urlEncode(value, charset)` produces percent-encoded text. Always pass `'UTF-8'` — the other supported charsets are present for legacy and expose locale-dependent bugs.

`Blob.toString(encoding)` and `Blob.valueOf(string)` round-trip between `Blob` and `String`, but only for encodings the string actually represents. `Blob.toString('UTF-8')` on an arbitrary AES ciphertext will corrupt it — always keep ciphertexts as `Blob` and only encode at the boundary.

### Key Material Belongs In Managed Storage, Not Apex

A hardcoded secret is the most common finding in security reviews of crypto code. Three correct alternatives, by use case:

- **Certificate** (Setup → Certificate and Key Management) — for RSA/ECDSA private keys used by `Crypto.signWithCertificate`. The key is never readable from Apex.
- **Named Credential (Custom Header or External Credential)** — for shared secrets used in HMAC. The secret is scoped to a principal and rotatable without code change.
- **Protected Custom Metadata Type** — for configuration-style secrets (signing key IDs, issuer strings, algorithm names). Mark the CMT `Protected` so only code in the managing package can read it.

### Constant-Time Comparison Matters For Verification

When your code compares a received signature to a recomputed one, `a == b` may short-circuit at the first differing byte, giving an attacker a measurable timing oracle. Salesforce doesn't expose a native constant-time compare, but two safe patterns exist: (1) SHA-256 both values and compare the digests — the comparison is now over fixed-length opaque bytes, which is effectively constant-time for short inputs; or (2) XOR all bytes and test equality at the end. For most webhook verification paths, pattern (1) is simpler and readable.

---

## Common Patterns

### HMAC-SHA256 Webhook Verification With Constant-Time Compare

**When to use:** An external vendor POSTs a webhook with a signature header (`X-Signature`, `Stripe-Signature`, etc.) computed as `HMAC-SHA256(secret, body)`. The Apex REST endpoint must reject forged payloads.

**How it works:**

```apex
@RestResource(urlMapping='/webhook/vendor/*')
global with sharing class VendorWebhookResource {
    @HttpPost
    global static void handle() {
        RestRequest req = RestContext.request;
        String signatureHeader = req.headers.get('X-Signature');
        Blob rawBody = req.requestBody;
        String secret = WebhookSecretProvider.current(); // Named Credential or protected CMT

        if (String.isBlank(signatureHeader) || String.isBlank(secret)) {
            RestContext.response.statusCode = 401;
            return;
        }

        Blob computedMac = Crypto.generateMac('hmacSHA256', rawBody, Blob.valueOf(secret));
        String computedHex = EncodingUtil.convertToHex(computedMac);

        if (!constantTimeEquals(computedHex, signatureHeader.toLowerCase())) {
            RestContext.response.statusCode = 401;
            return;
        }

        WebhookDispatcher.dispatch(rawBody);
    }

    private static Boolean constantTimeEquals(String a, String b) {
        Blob digestA = Crypto.generateDigest('SHA-256', Blob.valueOf(a));
        Blob digestB = Crypto.generateDigest('SHA-256', Blob.valueOf(b));
        return EncodingUtil.convertToHex(digestA) == EncodingUtil.convertToHex(digestB);
    }
}
```

**Why not the alternative:** Direct `==` between `computedHex` and `signatureHeader` short-circuits on the first differing byte. Re-hashing both sides makes the comparison opaque to timing attackers. `rawBody` must come from `req.requestBody`, not from a re-serialized JSON — any whitespace change invalidates the MAC.

### JWT Assertion Signing For OAuth 2.0 JWT Bearer Flow

**When to use:** Apex needs to obtain an OAuth 2.0 access token from a partner that supports the JWT bearer flow (Google, Salesforce-to-Salesforce, any RFC 7523 server). A Certificate stored in Setup holds the RSA private key.

**How it works:**

```apex
public with sharing class JwtAssertionBuilder {
    private static final String CERT_NAME = 'Partner_Signing_Cert';

    public static String build(String issuer, String audience, String subject) {
        Map<String, String> header = new Map<String, String>{ 'alg' => 'RS256', 'typ' => 'JWT' };
        Map<String, Object> claims = new Map<String, Object>{
            'iss' => issuer,
            'sub' => subject,
            'aud' => audience,
            'exp' => (Datetime.now().addMinutes(3).getTime() / 1000),
            'iat' => (Datetime.now().getTime() / 1000)
        };
        String headerB64Url = base64Url(Blob.valueOf(JSON.serialize(header)));
        String claimsB64Url = base64Url(Blob.valueOf(JSON.serialize(claims)));
        String signingInput = headerB64Url + '.' + claimsB64Url;

        Blob signature = Crypto.signWithCertificate('RSA-SHA256', Blob.valueOf(signingInput), CERT_NAME);
        return signingInput + '.' + base64Url(signature);
    }

    private static String base64Url(Blob input) {
        return EncodingUtil.base64Encode(input)
            .replace('+', '-').replace('/', '_').replace('=', '');
    }
}
```

**Why not the alternative:** `Crypto.sign('RSA-SHA256', ..., privateKeyBlob)` is the lower-level form and requires the private key to be loaded into the Apex transaction — a cardinal sin. `signWithCertificate` keeps the private key in the certificate store. Missing the base64url transformation produces a token the server rejects with `invalid_grant`.

### Encrypting A Field-Level Secret With Platform-Managed IV

**When to use:** The org stores an external integration token on a custom field but must not display the plaintext in a report or debug log. Shield Platform Encryption is not licensed in this org.

**How it works:**

```apex
public with sharing class IntegrationTokenVault {
    private static Blob key {
        get { return EncodingUtil.base64Decode(IntegrationSecret__mdt.getInstance('ActiveKey').Key_Base64__c); }
    }

    public static String encrypt(String plaintext) {
        Blob cipher = Crypto.encryptWithManagedIV('AES256', key, Blob.valueOf(plaintext));
        return EncodingUtil.base64Encode(cipher);
    }

    public static String decrypt(String cipherB64) {
        Blob cipher = EncodingUtil.base64Decode(cipherB64);
        return Crypto.decryptWithManagedIV('AES256', key, cipher).toString();
    }
}
```

**Why not the alternative:** `Crypto.encrypt` forces the caller to generate and persist an IV — a common source of IV reuse bugs. `encryptWithManagedIV` prepends a fresh 16-byte IV to the ciphertext so the only thing you store is a single opaque base64 blob. Shield Platform Encryption is still the preferred answer when it is licensed — it encrypts the physical field storage transparently with FIPS-validated keys.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Verify a webhook signed by an external service | `Crypto.generateMac('hmacSHA256', ...)` + constant-time compare | Matches the vendor's signing method exactly |
| Sign a JWT assertion for OAuth JWT bearer flow | `Crypto.signWithCertificate('RSA-SHA256', ..., certName)` | Keeps the private key in the certificate store |
| Hash a record for deduplication or cache keys | `Crypto.generateDigest('SHA-256', ...)` | Not a security control — just a deterministic fingerprint |
| Encrypt a custom-field secret without Shield | `Crypto.encryptWithManagedIV('AES256', ...)` | Platform generates a fresh IV per call |
| Encode bytes for a JSON payload | `EncodingUtil.base64Encode` | Standard base64 with padding |
| Encode a token for a URL segment or JWT header | base64 then replace `+→-`, `/→_`, strip `=` | No native base64url method |
| Obscure a short ID for non-security reasons | `Crypto.generateDigest('SHA1', ...)` — documented spelling has no hyphen, unlike `SHA-256` | Not acceptable for HMACs or signatures |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Identify the **purpose** — signature, MAC, digest, encryption, or encoding — and the exact algorithm the other system uses.
2. Locate the **key material** in a Named Credential, Certificate, or protected Custom Metadata record; refuse to proceed if the key is a string literal in Apex.
3. Write the transformation in the order the consumer expects: bytes → algorithm → encoding. Never collapse two boundaries (e.g. `Blob.valueOf(hmac.toString())` corrupts the MAC).
4. For verification paths, wrap the equality check in a constant-time comparison (digest both sides, or XOR loop).
5. Pin the behavior with a test that feeds a known input and asserts a known output (RFC 4231 HMAC test vectors are public and stable).

---

## Review Checklist

- [ ] Algorithm name is copied verbatim from the Apex Crypto reference (`hmacSHA256` — not `HMAC-SHA-256`, not `SHA256-HMAC`) and matches the consumer's specification.
- [ ] No `hmacSHA384` anywhere — `generateMac` supports only `hmacMD5`, `hmacSHA1`, `hmacSHA256`, `hmacSHA512`.
- [ ] Key material is not a literal string in Apex; source is documented.
- [ ] Verification paths use a constant-time comparison, not `==` on raw MACs.
- [ ] Base64url transformation is applied for JWT segments (replace `+`, `/`, strip `=`).
- [ ] Ciphertexts and signatures stay as `Blob` until the last encoding step.
- [ ] `encryptWithManagedIV` is preferred over `encrypt` unless IV interop is required.
- [ ] Weak algorithms (`MD5`, `SHA1`, `hmacMD5`, `hmacSHA1`) are flagged and justified.
- [ ] Test class pins at least one known-answer vector for the algorithm in use.

---

## Salesforce-Specific Gotchas

1. **`Crypto.signWithCertificate` requires the cert in Setup, not a Static Resource** — loading a `.p12` file from a Static Resource and trying to sign with its bytes will fail. Import the key into Certificate and Key Management and reference it by DeveloperName.
2. **Base64url is not a built-in** — `EncodingUtil.base64Encode` always produces standard base64. Forgetting to translate `+`/`/` and strip `=` is the single most common JWT signing bug in Apex.
3. **`Blob.valueOf(String)` defaults to UTF-8, but `Blob.toString(Blob)` requires you to pass the encoding** — a MAC computed over UTF-8 body bytes will differ from one computed over a re-serialized JSON that normalized character escapes.
4. **`Crypto.generateAesKey` returns a fresh key per call, not a stable one** — developers use it to generate a key and then forget that the next transaction has no reference to that key. For persistent AES use, generate the key once externally and store it via protected CMT or Named Credential.
5. **`Crypto.getRandomInteger` is cryptographically secure; `Math.random()` is not** — use `Crypto.getRandomInteger` or `Crypto.getRandomLong` for nonces, session IDs, and PKCE verifiers. Never use `Math.random()` for anything security-relevant.
6. **The `encryptWithManagedIV` ciphertext prepends the IV as the first 16 bytes** — systems that expect an IV-separated structure will decode this incorrectly. Use `encrypt` with an explicit IV if you need interop with a spec that declares its own IV framing.
7. **`Crypto.sign` with `RSA` returns PKCS#1 v1.5 signatures, not PSS** — if the consumer expects PSS (`RSASSA-PSS`), there is no native Apex support; you must call an external signing service.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Crypto/encoding code path | Apex using `Crypto` / `EncodingUtil` with correct algorithm, key source, and encoding transform |
| Key-material sourcing plan | Named Credential, Certificate, or protected CMT setup steps with rotation guidance |
| Test fixture with known-answer vectors | `@IsTest` method pinning algorithm output to published test vectors |
| Review findings for weak algorithms or literals | List of `Crypto`/`EncodingUtil` calls with MD5, SHA1, literal keys, or non-constant-time compares |

---

## Related Skills

- `apex/apex-named-credentials-patterns` — use when the key or secret is delivered through a Named Credential or External Credential principal.
- `apex/apex-rest-services` — use when the crypto path is wrapped inside an inbound `@RestResource` webhook endpoint.
- `apex/callouts-and-http-integrations` — use when the crypto output is attached to an outbound HTTP request.
- `apex/custom-metadata-in-apex` — use when signing keys or secrets live in protected Custom Metadata.
- `security/shield-platform-encryption` — use when the requirement is to encrypt Salesforce-stored field data, not Apex payloads in transit.
