# LLM Anti-Patterns — CSP and Trusted URLs

Mistakes AI assistants reliably make when asked to fix "Refused to load ... Content
Security Policy" in a Salesforce org.

## Anti-Pattern 1: Recommending a `script-src` Checkbox That Does Not Exist

**What the LLM generates:** "Add a Trusted URL for `https://cdn.example.com` and
select the `script-src` directive so the library can load."

**Why it happens:** `script-src` is the directive named in the browser error, and
the model assumes the Trusted URL UI mirrors the CSP specification one-to-one.

**Correct pattern:**

```
CspTrustedSite exposes exactly six directive fields:

  isApplicableToConnectSrc   isApplicableToFontSrc
  isApplicableToFrameSrc     isApplicableToImgSrc
  isApplicableToMediaSrc     isApplicableToStyleSrc

There is NO script-src option. Lightning fixes script-src at 'self'.

For third-party JavaScript, the answer is a STATIC RESOURCE:

  import { loadScript } from 'lightning/platformResourceLoader';
  import CHART_JS from '@salesforce/resourceUrl/chartJs';
  ...
  loadScript(this, CHART_JS).then(() => this.init());

The library is then served from the org's own origin, satisfying
script-src 'self'. This also pins the version.
```

**Detection hint:** the string `script-src` appearing as a Trusted URL directive to
select, or any `<isApplicableToScriptSrc>` element in generated metadata.

---

## Anti-Pattern 2: Ticking Every Directive "To Be Safe"

**What the LLM generates:** a `CspTrustedSite` with all six `isApplicableTo*`
fields set to `true`, or the instruction "select all the directives so it
definitely works."

**Why it happens:** The model cannot observe which directive actually blocked the
request, and over-granting makes the immediate symptom disappear.

**Correct pattern:**

```
The browser tells you the directive. Read it, then tick exactly one:

  "Refused to connect to"                -> connect-src
  "Refused to frame" / "to display ... in a frame" -> frame-src
  "Refused to load the image"            -> img-src
  "Refused to load the font"             -> font-src
  "Refused to load the stylesheet"       -> style-src
  "Refused to load media"                -> media-src

Write every field explicitly - true AND false - because the default for unset
fields is version-dependent:
  API <= 49.0     all isApplicable fields default to TRUE
  API 50.0-58.0   isApplicableToImgSrc is set to true
  API >= 59.0     at least one isApplicable/canAccess must be true, or the
                  deploy is rejected

An over-granted entry is indistinguishable from a correct one at review time,
so the reviewer cannot catch what you cannot justify.
```

**Detection hint:** a generated `CspTrustedSite` where more than two
`isApplicableTo*` fields are `true` with no stated reason, or where some fields are
omitted entirely.

---

## Anti-Pattern 3: Ignoring Context

**What the LLM generates:** a Trusted URL with no `<context>` element, or with
`LEX` regardless of where the component runs.

**Why it happens:** Context has a default, so omitting it produces valid metadata.
"Lightning" in the question maps to `LEX` even when the surface is an Experience
Cloud site — which is also Lightning technology.

**Correct pattern:**

```
context scopes the ENTIRE record:

  LEX          Lightning Experience pages only
  Communities  Experience Builder sites only
  VisualForce  custom Visualforce pages only (and only if the page's
               cspHeader attribute is true)
  All          all supported context types

A URL trusted in LEX is NOT trusted in an Experience Builder site.

Always ask which surfaces the component runs on before generating the record.
If the answer is "both," emit two records or use All with the reason in
description - All is a wider grant, not a shortcut.
```

**Detection hint:** a generated `CspTrustedSite` with no `<context>` element, or an
answer that never asks where the component runs.

---

## Anti-Pattern 4: Suggesting Relaxed CSP

**What the LLM generates:** "If the widget still doesn't work, set the Experience
Cloud site's Security Level to Relaxed CSP."

**Why it happens:** It is a real setting that makes the symptom disappear, and it
appears in forum answers as the fast fix.

**Correct pattern:**

```
Relaxed CSP is site-wide and permanent in practice. It relaxes script-src for
every component on every page of the site, including components a future admin
drags on. Worse, it destroys the record of WHICH origin the site needed, so
nobody can safely tighten it again.

The correct escalation is:
  1. read the console message
  2. identify the directive
  3. add ONE Trusted URL for ONE origin with THAT ONE directive, in the
     Communities context
  4. repeat for each additional origin the vendor uses

If a vendor genuinely requires inline script execution, that is a security
review with a named risk owner - never a build-time workaround, and never
something to suggest unprompted.
```

**Detection hint:** the phrase "Relaxed CSP" anywhere in a troubleshooting answer.

---

## Anti-Pattern 5: Conflating Trusted URLs with Remote Site Settings

**What the LLM generates:** "Add the endpoint to Remote Site Settings so the LWC can
call it," or "add a Trusted URL so the Apex callout succeeds."

**Why it happens:** Both are "allow-list an external URL" screens in Setup. The
distinction is about *which process* makes the request, which the prompt often does
not state.

**Correct pattern:**

```
Ask where the request originates.

  Browser (LWC fetch, <img>, <iframe>, WebSocket)
      -> Trusted URL (CspTrustedSite). Enforced by the CSP header.
      -> Error: "Refused to connect to ... violates the following Content
         Security Policy directive"

  Server (Apex Http.send, Visualforce)
      -> Remote Site Setting, or better a Named Credential.
         Enforced by the Salesforce application server.
      -> Error: "Unauthorized endpoint, please check Setup->Security->Remote
         site settings"

A feature that does both needs BOTH, configured independently. Adding one does
not satisfy the other.
```

**Detection hint:** an answer that names only one of the two mechanisms for a
feature that clearly does both, or that quotes the wrong error text for the
mechanism it recommends.

---

## Anti-Pattern 6: Reaching for a Wildcard by Default

**What the LLM generates:** `<endpointUrl>*.vendor.com</endpointUrl>` for a single
known host, or `https://*` for "any external API."

**Why it happens:** Wildcards are supported, they make the immediate problem go
away, and they save the model from enumerating hosts it cannot look up.

**Correct pattern:**

```
Wildcards ARE supported - "To reduce repetition, you can use the wildcard
character * (asterisk). For example, *.example.com" - and are correct when a
CDN genuinely rotates hostnames.

They are wrong as a shortcut: *.vendor.com trusts every current AND FUTURE
subdomain, including any the vendor later delegates to a third party.

Default to the exact host. When a wildcard is genuinely needed, say so in the
description field so the next reviewer does not have to guess.

Also note the grammar: the value must include a domain name, may include a
port (https://example.com:8080), must begin with https:// for a third-party
API and wss:// for a WebSocket, and is a LITERAL - "To add an EndpointUrl
based on parameters, build the URL before you add it to this Metadata Type."
```

**Detection hint:** any `endpointUrl` containing `*` for a single named host, or any
value with a template placeholder such as `{env}` left unsubstituted — the latter is
a documented malformed-URL example and is silently excluded from the CSP header.

---

## Anti-Pattern 7: Fixing One Origin and Declaring Victory

**What the LLM generates:** the Trusted URL for the vendor's loader script host,
presented as the complete solution.

**Why it happens:** The prompt quotes one console error, so the model solves one
console error.

**Correct pattern:**

```
A third-party widget is almost never one origin. Enumerate before configuring:

  loader script host    (often needs script-src -> static resource instead)
  API host              connect-src
  challenge/redirect    frame-src        (payment 3-D Secure, SSO popups)
  asset CDN             img-src, font-src, style-src
  telemetry beacon      connect-src      (fires only on the unhappy path)

Read the vendor's own CSP documentation - most publish this list - and create
one Trusted URL per origin. Then test the WHOLE flow including failure and
challenge paths, because a 3-D Secure iframe or an error beacon fires only
there and will otherwise be found by a customer.
```

**Detection hint:** a single Trusted URL offered for a named third-party SDK, with
no mention of the vendor's other hosts.

---

## Anti-Pattern 8: Granting Camera or Microphone with a CSP Directive

**What the LLM generates:** "Add the video vendor to Trusted URLs with `frame-src`
and `media-src` so the camera works."

**Why it happens:** `media-src` sounds like it governs media devices. It governs
loading audio and video *resources*, which is a different thing.

**Correct pattern:**

```
Camera and microphone are governed by the Permissions-Policy header, not CSP,
and need a two-part configuration (both API 59.0 and later):

  1. Org level - SecuritySettings:
       <enablePermissionsPolicy>true</enablePermissionsPolicy>
       <grantCameraAccess>TrustedUrls</grantCameraAccess>
       <grantMicrophoneAccess>TrustedUrls</grantMicrophoneAccess>

  2. Per URL - CspTrustedSite:
       <canAccessCamera>true</canAccessCamera>
       <canAccessMicrophone>true</canAccessMicrophone>

The per-URL flags are INERT without step 1: "This field takes effect only when
the enablePermissionsPolicy field equals true and the grantCameraAccess field
equals TrustedUrls in the SecuritySettings metadata API type."

Deploy the org-level change first and separately - it changes header behaviour
for every page in the org.
```

**Detection hint:** `media-src` recommended for a camera or microphone
requirement, or `canAccessCamera` set with no accompanying `SecuritySettings`
change.
