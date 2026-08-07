# LLM Anti-Patterns — Apex Encoding And Crypto

Common mistakes AI coding assistants make when generating or reviewing Apex code that signs, verifies, hashes, encrypts, or encodes payloads.

## Anti-Pattern 1: Hardcoding The HMAC Secret As A String Literal

**What the LLM generates:**

```apex
public static Boolean verify(Blob body, String receivedSig) {
    String secret = 'whsec_testsecret1234567890';   // <- literal
    Blob mac = Crypto.generateMac('hmacSHA256', body, Blob.valueOf(secret));
    return EncodingUtil.convertToHex(mac) == receivedSig;
}
```

**Why it happens:** Tutorials and vendor quickstarts show the secret inline for brevity. LLMs mirror that pattern and skip the managed-storage step.

**Correct pattern:** Store the secret in a Named Credential, External Credential, or protected Custom Metadata record and read it at call time:

```apex
String secret = WebhookConfig__mdt.getInstance('Live').Secret__c; // protected CMT
Blob mac = Crypto.generateMac('hmacSHA256', body, Blob.valueOf(secret));
```

**Detection hint:** `Crypto.generateMac(...)` or `Crypto.encrypt(...)` on the same line or within 3 lines of a string literal that looks like a secret (contains "secret", "key", "token", or 16+ opaque characters).

---

## Anti-Pattern 2: Using Standard Base64 Everywhere, Including JWT Segments

**What the LLM generates:**

```apex
String segment = EncodingUtil.base64Encode(Blob.valueOf(JSON.serialize(claims)));
String jwt = header + '.' + segment + '.' + sig;
```

**Why it happens:** Apex exposes `base64Encode` but no `base64UrlEncode`. LLMs miss that JWTs require URL-safe base64 and ship the standard form.

**Correct pattern:** Transform the base64 output to base64url (RFC 4648 §5):

```apex
String segment = EncodingUtil.base64Encode(Blob.valueOf(JSON.serialize(claims)))
    .replace('+', '-').replace('/', '_').replace('=', '');
```

**Detection hint:** `EncodingUtil.base64Encode` used in a JWT-like concatenation (`'.' + ... + '.'`) without a subsequent `.replace('+', '-')` call.

---

## Anti-Pattern 3: Comparing MACs With `==` Without Constant-Time Protection

**What the LLM generates:**

```apex
Blob mac = Crypto.generateMac('hmacSHA256', body, Blob.valueOf(secret));
if (EncodingUtil.convertToHex(mac) == receivedSig) {
    // accept
}
```

**Why it happens:** LLMs treat signature comparison as ordinary string equality. The timing-oracle risk is subtle and rarely called out in tutorials.

**Correct pattern:** Hash both sides, then compare — or XOR byte-by-byte:

```apex
Blob digestA = Crypto.generateDigest('SHA-256', Blob.valueOf(computedHex));
Blob digestB = Crypto.generateDigest('SHA-256', Blob.valueOf(receivedSig));
if (EncodingUtil.convertToHex(digestA) == EncodingUtil.convertToHex(digestB)) { ... }
```

**Detection hint:** A MAC or signature comparison (`convertToHex(...)` or `base64Encode(...)` on one side of `==`) that is not wrapped in a helper with "constant", "timing", or "safe" in the name, and no SHA-256 re-hash of both values before the compare.

---

## Anti-Pattern 4: Using `Crypto.sign` With A Hardcoded Private Key Blob

**What the LLM generates:**

```apex
String pkPem = '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANB...\n-----END PRIVATE KEY-----';
Blob pk = EncodingUtil.base64Decode(pkPem.replace('-----BEGIN PRIVATE KEY-----','')
    .replace('-----END PRIVATE KEY-----','').replace('\n',''));
Blob sig = Crypto.sign('RSA-SHA256', Blob.valueOf(input), pk);
```

**Why it happens:** LLMs mimic Node/Python examples that read a key from disk. In Apex, the equivalent secure form is an entirely different API.

**Correct pattern:** Import the key into Setup → Certificate and Key Management and use `Crypto.signWithCertificate`:

```apex
Blob sig = Crypto.signWithCertificate('RSA-SHA256', Blob.valueOf(input), 'Partner_Cert');
```

**Detection hint:** `Crypto.sign(` with an algorithm starting `RSA-` or `ECDSA-` where the private-key argument is anything other than a cert DeveloperName. Flag any `-----BEGIN PRIVATE KEY-----` literal in Apex.

---

## Anti-Pattern 5: Calling `Blob.toString()` On A Cryptographic Blob

**What the LLM generates:**

```apex
Blob mac = Crypto.generateMac('hmacSHA256', body, Blob.valueOf(secret));
String macStr = mac.toString();  // corrupts non-UTF-8 bytes
CustomObj__c.Signature__c = macStr;
```

**Why it happens:** LLMs treat `Blob` → `String` as a generic toString, missing that `Blob.toString()` assumes UTF-8.

**Correct pattern:** Base64 or hex encode first:

```apex
String macStr = EncodingUtil.convertToHex(mac);   // or base64Encode(mac)
```

**Detection hint:** `.toString()` called on a `Blob` that came from `Crypto.*`. Also flag assignment of a `Crypto.*` return value to a `String` variable without an `EncodingUtil` call.

---

## Anti-Pattern 6: `Crypto.encrypt` With A Hardcoded Zero IV

**What the LLM generates:**

```apex
Blob iv = Blob.valueOf('0000000000000000');   // fixed 16-byte IV
Blob cipher = Crypto.encrypt('AES256', key, iv, Blob.valueOf(plaintext));
```

**Why it happens:** LLMs default to a constant IV to make the code "simple." CBC mode with a fixed IV leaks equality of plaintexts.

**Correct pattern:** Use `Crypto.encryptWithManagedIV`:

```apex
Blob cipher = Crypto.encryptWithManagedIV('AES256', key, Blob.valueOf(plaintext));
```

**Detection hint:** `Crypto.encrypt(` (without `WithManagedIV`) where the IV argument is a literal or a variable set once outside a loop.

---

## Anti-Pattern 7: Using MD5 Or SHA-1 For HMACs Or Signatures

**What the LLM generates:**

```apex
Blob mac = Crypto.generateMac('hmacMD5', body, Blob.valueOf(secret));
```

**Why it happens:** LLMs copy the first algorithm name from the docs list; `hmacMD5` and `hmacSHA1` are listed first alphabetically.

**Correct pattern:** `hmacSHA256` minimum for HMACs; `SHA-256` minimum for digests when the output has a security role.

**Detection hint:** `'hmacMD5'`, `'hmacSHA1'`, `'MD5'`, or `'SHA1'` / `'SHA-1'` passed to any `Crypto` method — match case-insensitively, since `HmacMD5` and `hmacMD5` both appear in the wild.

---

## Anti-Pattern 7b: Inventing `hmacSHA384` (Or Any Unsupported Algorithm Name)

**What the LLM generates:**

```apex
// compiles fine; throws at run time
Blob mac = Crypto.generateMac('hmacSHA384', body, Blob.valueOf(secret));
```

…or prose listing the supported set as "hmacSHA1, hmacSHA256, hmacSHA384, hmacSHA512, hmacMD5".

**Why it happens:** SHA-384 is a real SHA-2 member and a real HMAC in Java's JCE (`HmacSHA384`), in Python's `hmac`, and in OpenSSL. The model completes the 256/384/512 sequence by pattern rather than by reading Salesforce's list, and Salesforce's own `sign` / `signWithCertificate` *does* accept `RSA-SHA384` and `ECDSA-SHA384`, which reinforces the guess. Because `algorithmName` is a `String`, the compiler and the deploy both pass, so nothing contradicts the model.

**Correct pattern:** `Crypto.generateMac` accepts exactly `hmacMD5`, `hmacSHA1`, `hmacSHA256`, `hmacSHA512`. SHA-384 has no keyed-MAC form on the platform, and `generateDigest` has no SHA-384 either. When a counterparty mandates HMAC-SHA-384, renegotiate to SHA-256/SHA-512 or compute the MAC outside Apex; never silently substitute another algorithm, because the signature will not verify. `SHA3-384` is not a substitute — it is an unkeyed digest.

**Detection hint:** case-insensitive regex `Crypto\.generateMac\s*\(\s*['"]\s*hmac[- ]?sha[- ]?384` in any `.cls`/`.trigger`, and in prose any supported-algorithm list for `generateMac` whose cardinality is not exactly 4 or that contains the substring `384`.

---

## Anti-Pattern 8: Using `Math.random()` For Nonces Or Tokens

**What the LLM generates:**

```apex
String nonce = String.valueOf(Math.random()).substring(2);
```

**Why it happens:** LLMs default to `Math.random()` as the idiomatic "make a random thing" call. It is not cryptographically secure.

**Correct pattern:** `Crypto.getRandomInteger()`, `Crypto.getRandomLong()`, or a sliced `Crypto.generateAesKey(256)` for longer random bytes.

**Detection hint:** `Math.random()` used near any word suggesting security purpose: `nonce`, `token`, `session`, `verifier`, `csrf`, `otp`.
