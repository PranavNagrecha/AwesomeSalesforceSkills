# Examples: Apex Wrapper Class Patterns

## Example 1: Accounts with an open-opportunity count, sortable two ways

**Context:** A component shows Accounts with the number of open Opportunities on each, sortable by name or by count.

**Design:** A top-level `AccountRow` wrapper (the LWC guide does not support inner classes as parameters or return values), a separate `with sharing` controller with the static `@AuraEnabled` method, and null-safe comparators. The full deployable set (wrapper, comparators, controller, test class, component, and package.xml) is in `code-examples.md`.

---

## Example 2: Same-namespace Apex REST request wrapper

**Context:** An `@RestResource` endpoint accepts a JSON body.

```apex
@RestResource(urlMapping='/accountRequests/*')
global with sharing class AccountRequestResource {

    global class AccountRequest {
        global String name;
        global String industry;
    }

    @HttpPost
    global static Id create() {
        AccountRequest body = (AccountRequest) JSON.deserialize(
            RestContext.request.requestBody.toString(), AccountRequest.class);
        Account acct = new Account(Name = body.name, Industry = body.industry);
        insert as user acct;
        return acct.Id;
    }
}
```

**Why it works:** The class is deserialized by code in its own namespace, and since API 49.0 the default `@JsonAccess` for both directions is `sameNamespace`, so no annotation is needed. Add `@JsonAccess` with the narrowest value only if code in another namespace or package must serialize or deserialize `AccountRequest`. UNVERIFIED (2026-10-03): whether `global` is required on the inner request class for an `@RestResource` in an org without a namespace; `global` is shown because the outer resource class is `global`.

---

## Anti-Pattern: Missing @AuraEnabled on wrapper properties

**What practitioners do:** Annotate the Apex method with `@AuraEnabled` but not the wrapper's properties.

**What goes wrong:** Only annotated public instance properties are serialized, so the component reads `undefined`.

**Correct approach:** Annotate each property the template reads, and add getters and setters to properties the component sends back.
