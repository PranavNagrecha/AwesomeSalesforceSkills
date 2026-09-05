# Well-Architected Notes - Static Resources In LWC

## Relevant Pillars

### Performance

Static resources affect page weight and initialization time directly. Controlled loading,
smaller payloads, and avoiding duplicate initialization keep components responsive. The
platform gives you two hard numbers to design against: 5 MB per resource and 250 MB per
org.

### Operational Excellence

Versioned resource names, documented internal paths, and consistent loading patterns make
upgrades and rollback safe. Asset sprawl and ad hoc naming do the opposite.

### Security

`cacheControl` is an access decision, not a caching tweak. `Public` makes the bytes
readable by unauthenticated internet traffic once cached; `Private` keeps them behind
authentication in a per-user session cache. Library choice is the second security surface:
under Lightning Locker a library that creates globals, calls `eval()`, or scans the whole
document is blocked outright.

## Architectural Tradeoffs

- **Library convenience vs platform fit:** a third-party dependency can accelerate
  delivery, but it adds security and lifecycle review cost, and Salesforce provides no
  support for third-party JavaScript libraries.
- **Single-file uploads vs zipped packages:** separate resources are simple at first, while
  zipped packs scale better for coordinated assets — at the cost of an internal path
  contract every consumer now depends on.
- **Overwrite-in-place vs versioned names:** overwriting is convenient short term, but
  versioned names give clearer rollback and deployment behavior.
- **`loadStyle` reach vs containment:** in synthetic shadow a stylesheet loaded this way is
  global by design. That is exactly right for a library's own stylesheet and exactly wrong
  for component styling.
- **Static resource vs content asset:** content assets (`@salesforce/contentAssetUrl`) come
  from Salesforce Files and are the Experience Builder path for editable imagery; static
  resources are the developer-owned, deployable path for code and fixed assets.

## Anti-Patterns

1. **Remote CDN loading in LWC** - the deployment model escapes Salesforce asset governance,
   and the platform blocks it regardless of Trusted URLs.
2. **Repeated script loads per rerender** - library initialization multiplies with every
   component update.
3. **Undocumented zip path contracts** - resource consumers break on package refresh
   because internal file paths changed silently.
4. **`Public` by default** - chosen for load time, it publishes the bytes to
   unauthenticated traffic.
5. **Zipping the ESM build** - it deploys cleanly and then defines nothing, because
   `loadScript` does not support ES modules.

## Official Sources Used

- Lightning Web Components Developer Guide, **Static Resources** (`create-resources`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-resources.html — supports
  the `@salesforce/resourceUrl` import, the namespace prefix for packaged resources, the
  resource-name character rules, archive path concatenation, `{property}` template syntax,
  the flat `staticresources` directory, and the 5 MB / 250 MB limits (L3640-L3668).
- Lightning Web Components Developer Guide, **Use Third-Party JavaScript Libraries**
  (`js-third-party-library`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html —
  supports the static-resource-as-CSP-requirement claim, `loadScript`/`loadStyle` in
  `renderedCallback()` on first render, `Promise.all` aggregation with `then`/`catch`,
  `lwc:dom="manual"` on an empty native element, styling not applying to appended elements,
  and using `this.template` rather than `document` (L2655-L2744).
- Lightning Web Components Developer Guide, **renderedCallback()**
  (`create-lifecycle-hooks-rendered`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-rendered.html
  — supports the one-time-guard gotcha and the "rendered many times" behaviour (L4136).
- Lightning Web Components Developer Guide, **Locker-Compliant JavaScript Libraries**
  (`js-third-party-guidance`) and **LWS-Compliant JavaScript Libraries**
  (`js-third-party-strict-mode`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-guidance.html —
  support the trust-escalation gotcha: globals under strict mode, `eval()`/`new
  Function()`/`<script>` as CSP violations, blocked broad DOM scans, and libraries that set
  `"use strict"` needing changes under LWS (L2761-L2782).
- Lightning Web Components Developer Guide, **Use Third-Party Web Components in LWC**
  (`create-use-third-party-components`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-use-third-party-components.html
  — supports the "`loadScript` doesn't currently support ECMAScript Modules" gotcha and
  restates the 5 MB / 250 MB limits (L4190, L4207).
- Lightning Web Components Developer Guide, **Synthetic Shadow DOM** (`create-dom-synthetic`)
  and **Introduction** (`get-started`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-dom-synthetic.html —
  support the "`loadStyle` CSS is global in synthetic shadow" gotcha and the specificity
  order component CSS > `@import` > `loadStyle` (L127, L3165-L3171).
- Lightning Web Components Developer Guide, **Light DOM** (`create-light-dom`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom.html — supports
  the claim that scoped styles do not apply inside `lwc:dom="manual"` (L3483).
- Lightning Web Components Developer Guide, **Content Asset Files**
  (`create-content-assets`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-content-assets.html —
  supports the static resource vs content asset tradeoff, `@salesforce/contentAssetUrl`,
  and the `pathinarchive` parameter (L3674-L3688).
- Lightning Web Components Developer Guide, **Write Jest Tests**
  (`unit-testing-using-jest-create-tests`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html
  — supports the test file's structure, the `afterEach` jsdom reset, the `.forceignore`
  requirement, and the documented `moduleNameMapper` mock list that does **not** include
  `platformResourceLoader` (L12326-L12453).
- Metadata API Developer Guide, **StaticResource** —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports
  the required `cacheControl` (`Private`/`Public`) and `contentType` fields, the
  `.resource` / `resource-meta.xml` file suffixes, the sample definition the XML in
  `code-examples.md` is shaped from, wildcard support in `package.xml`, and the org-local
  statement (api_meta.txt L130902-L130965).
- Metadata API Developer Guide, **LightningComponentBundle** — same PDF — supports
  `apiVersion`, `isExposed`, `masterLabel`, `description`, and `targets` in the component's
  `js-meta.xml` (api_meta.txt L84011-L84053).
- Object Reference, **StaticResource** standard object —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf —
  supports the SOQL verification step: `query()` is a supported call, and `Name`,
  `ContentType`, `CacheControl`, `BodyLength`, and `Description` are queryable, with the
  authoritative wording for what each `CacheControl` value exposes
  (object_reference.txt L273887-L273953).
