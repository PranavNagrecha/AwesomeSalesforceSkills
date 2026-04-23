# Examples — Apex Encoding And Crypto

## Example 1: Verify A Stripe Webhook Signature

**Context:** A Salesforce org receives Stripe webhook events at a custom `@RestResource` endpoint. Stripe signs each webhook body with HMAC-SHA256 using a shared secret and sends a `Stripe-Signature` header in the form `t=1234567890,v1=abcdef...`.

**Problem:** Naive implementations either skip verification entirely (accepting forged events) or compare the computed MAC to the received one using `==`, which leaks bytes through timing.

**Solution:**

```apex
@RestResource(urlMapping='/stripe/events/*')
global with sharing class StripeEventResource {
    @HttpPost
    global static void post() {
        RestRequest req = RestContext.request;
        String header = req.headers.get('Stripe-Signature');
        if (String.isBlank(header)) {
            RestContext.response.statusCode = 400;
            return;
        }

        Map<String, String> parsed = parseHeader(header);
        String timestamp = parsed.get('t');
        String v1Signature = parsed.get('v1');
        if (String.isBlank(timestamp) || String.isBlank(v1Signature)) {
            RestContext.response.statusCode = 400;
            return;
        }

        // Reject events older than 5 minutes to defeat replay
        Long nowEpoch = Datetime.now().getTime() / 1000;
        if (Math.abs(nowEpoch - Long.valueOf(timestamp)) > 300) {
            RestContext.response.statusCode = 400;
            return;
        }

        String secret = StripeConfig__mdt.getInstance('Live').Webhook_Secret__c;
        String signedPayload = timestamp + '.' + req.requestBody.toString();
        Blob computed = Crypto.generateMac('HmacSHA256',
            Blob.valueOf(signedPayload), Blob.valueOf(secret));
        String computedHex = EncodingUtil.convertToHex(computed);

        if (!constantTimeEquals(computedHex, v1Signature)) {
            RestContext.response.statusCode = 401;
            return;
        }

        StripeEventDispatcher.dispatch(req.requestBody);
    }

    private static Map<String, String> parseHeader(String header) {
        Map<String, String> out = new Map<String, String>();
        for (String part : header.split(',')) {
            List<String> kv = part.split('=', 2);
            if (kv.size() == 2) out.put(kv[0], kv[1]);
        }
        return out;
    }

    private static Boolean constantTimeEquals(String a, String b) {
        if (a == null || b == null) return false;
        Blob da = Crypto.generateDigest('SHA-256', Blob.valueOf(a));
        Blob db = Crypto.generateDigest('SHA-256', Blob.valueOf(b));
        return EncodingUtil.convertToHex(da) == EncodingUtil.convertToHex(db);
    }
}
```

**Why it works:** The signed payload is reconstructed as Stripe defines it (timestamp `.` raw body). Timestamp drift check defeats replay attacks. The digest-of-digest comparison removes the timing-oracle risk from the last byte comparison.

---

## Example 2: Sign A JWT For Google Service Account OAuth

**Context:** A nightly Batch job exports Salesforce reporting data to a Google Cloud Storage bucket. The service account credential is a `.p12` imported into Setup → Certificate and Key Management as `GCS_Service_Account`.

**Problem:** Calling `Crypto.sign('RSA-SHA256', ..., privateKeyBlob)` requires exposing the private key inside Apex — neither the `.p12` bytes nor the decoded key belong in any runtime path. Additionally, the JWT must use base64url, not standard base64, or Google's token endpoint returns `invalid_grant`.

**Solution:**

```apex
public with sharing class GoogleOAuthClient {
    private static final String CERT_NAME = 'GCS_Service_Account';
    private static final String TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token';
    private static final String SCOPE = 'https://www.googleapis.com/auth/devstorage.read_write';

    public static String fetchAccessToken(String serviceAccountEmail) {
        String assertion = buildAssertion(serviceAccountEmail);

        HttpRequest req = new HttpRequest();
        req.setEndpoint(TOKEN_ENDPOINT);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/x-www-form-urlencoded');
        req.setBody('grant_type=' + EncodingUtil.urlEncode('urn:ietf:params:oauth:grant-type:jwt-bearer', 'UTF-8')
            + '&assertion=' + assertion);

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() != 200) {
            throw new CalloutException('Token fetch failed: ' + res.getBody());
        }
        return (String) ((Map<String, Object>) JSON.deserializeUntyped(res.getBody())).get('access_token');
    }

    private static String buildAssertion(String serviceAccountEmail) {
        Map<String, String> header = new Map<String, String>{ 'alg' => 'RS256', 'typ' => 'JWT' };
        Long nowEpoch = Datetime.now().getTime() / 1000;
        Map<String, Object> claims = new Map<String, Object>{
            'iss' => serviceAccountEmail,
            'scope' => SCOPE,
            'aud' => TOKEN_ENDPOINT,
            'exp' => nowEpoch + 180,
            'iat' => nowEpoch
        };
        String signingInput = base64Url(Blob.valueOf(JSON.serialize(header)))
            + '.' + base64Url(Blob.valueOf(JSON.serialize(claims)));
        Blob signature = Crypto.signWithCertificate('RSA-SHA256',
            Blob.valueOf(signingInput), CERT_NAME);
        return signingInput + '.' + base64Url(signature);
    }

    private static String base64Url(Blob input) {
        return EncodingUtil.base64Encode(input)
            .replace('+', '-').replace('/', '_').replace('=', '');
    }
}
```

**Why it works:** `Crypto.signWithCertificate` uses the platform-managed private key — Apex never loads the `.p12` bytes. The base64url transformation (replace `+`/`/`, strip `=`) is applied to every JWT segment. Clock skew is bounded by `exp = iat + 180` per Google's documentation.

---

## Example 3: Safely Encrypt An Integration Token Before Storing It

**Context:** An ISV app stores a customer's third-party API token on a custom field and needs the plaintext to make outbound callouts. Shield Platform Encryption is not in this org's edition.

**Problem:** Storing the plaintext exposes it in reports, List Views, and debug logs. Rolling your own AES usually produces IV reuse or missing authentication.

**Solution:**

```apex
public with sharing class PartnerTokenVault {
    private static Blob cachedKey;

    private static Blob key() {
        if (cachedKey == null) {
            PartnerSecrets__mdt rec = PartnerSecrets__mdt.getInstance('ActiveKey');
            cachedKey = EncodingUtil.base64Decode(rec.AES256_Key_Base64__c);
        }
        return cachedKey;
    }

    public static String encryptForStorage(String plaintext) {
        if (plaintext == null) return null;
        Blob cipher = Crypto.encryptWithManagedIV('AES256', key(), Blob.valueOf(plaintext));
        return EncodingUtil.base64Encode(cipher);
    }

    public static String decryptForUse(String cipherB64) {
        if (String.isBlank(cipherB64)) return null;
        Blob cipher = EncodingUtil.base64Decode(cipherB64);
        return Crypto.decryptWithManagedIV('AES256', key(), cipher).toString();
    }
}
```

**Why it works:** Each call gets a fresh IV from the platform, removing the most common homegrown AES bug. The key is held in a Protected Custom Metadata record that only the managing package can read. The plaintext is base64-encoded only at the storage boundary so the `Blob` never leaks as corrupted `String` anywhere in the call chain.

---

## Anti-Pattern: Comparing HMACs With `==` Or `String.equals`

**What practitioners do:**

```apex
Blob mac = Crypto.generateMac('HmacSHA256', body, Blob.valueOf(secret));
if (EncodingUtil.convertToHex(mac) == providedSignature) { /* accept */ }
```

**What goes wrong:** String comparison short-circuits at the first mismatched byte. An attacker can repeatedly POST with varying signatures and measure the response-time difference to reveal signature bytes one at a time. This is a known-practical attack; real webhook handlers have been compromised this way.

**Correct approach:** Hash both sides (e.g. SHA-256) and compare the digests, or XOR every byte and test equality of the accumulated result. The comparison should always touch all bytes regardless of where the mismatch lies.

---

## Anti-Pattern: Using `Blob.toString()` On A Ciphertext

**What practitioners do:**

```apex
Blob cipher = Crypto.encryptWithManagedIV('AES256', key, Blob.valueOf(plaintext));
String stored = cipher.toString();  // corrupted — not UTF-8
CustomObj__c.Token__c = stored;
```

**What goes wrong:** `Blob.toString()` interprets the bytes as UTF-8. Random AES ciphertext bytes almost never form a valid UTF-8 sequence, so the returned string is corrupted; the reverse `Blob.valueOf(stored)` returns different bytes, and decryption fails with an opaque error.

**Correct approach:** Encode ciphertext with `EncodingUtil.base64Encode` for storage. Ciphertext bytes should only touch a `String` via a binary-safe encoding step.
