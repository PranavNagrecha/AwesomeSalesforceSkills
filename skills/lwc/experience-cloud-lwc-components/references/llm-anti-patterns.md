# LLM Anti-Patterns — Experience Cloud LWC Components

Common mistakes AI coding assistants make when generating or advising on Experience Cloud LWC components. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Missing `with sharing` on Guest-Accessible Apex

**What the LLM generates:** An Apex class without an explicit sharing declaration (or with `without sharing`) called from a guest-accessible Experience Cloud component:

```apex
public class ProductController {
    @AuraEnabled(cacheable=true)
    public static List<Product2> getProducts() {
        return [SELECT Id, Name FROM Product2 WHERE IsActive = TRUE];
    }
}
```

**Why it happens:** Training data contains many Apex classes written for internal users where sharing is not specified. LLMs pattern-match to this common shape. The class compiles and runs, so the LLM never sees an error signal from the context.

**Correct pattern:**

```apex
public with sharing class ProductController {
    @AuraEnabled(cacheable=true)
    public static List<Product2> getProducts() {
        return [SELECT Id, Name FROM Product2 WHERE IsActive = TRUE WITH USER_MODE];
    }
}
```

**Detection hint:** Scan generated Apex for `@AuraEnabled` methods in classes that lack `with sharing` keyword. Any class callable from an Experience Cloud component without `with sharing` is a finding.

---

## Anti-Pattern 2: Not Exposing Component with `lightningCommunity__Default` Target

**What the LLM generates:** A JS-meta.xml that only declares internal targets, then instructs the user to deploy and use the component in Experience Builder:

```xml
<LightningComponentBundle>
    <apiVersion>61.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__AppPage</target>
    </targets>
</LightningComponentBundle>
```

**Why it happens:** The LLM defaults to the most common LWC scaffolding pattern (internal App Page) and does not adjust for the Experience Cloud deployment context unless explicitly prompted.

**Correct pattern:**

```xml
<LightningComponentBundle>
    <apiVersion>61.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Default</target>
    </targets>
</LightningComponentBundle>
```

**Detection hint:** Check for `lightningCommunity__Default` or `lightningCommunity__Page` in the `<targets>` block of any JS-meta.xml generated for an Experience Cloud component. Internal targets alone are never sufficient for Experience Builder exposure.

---

## Anti-Pattern 3: Using Aura Navigation Events or `comm__loginPage` in LWR Context

**What the LLM generates:** Navigation code that mixes Aura event syntax or Aura-only page reference types into an LWR LWC component:

```js
// Wrong: Aura event syntax in LWC
this.dispatchEvent(new CustomEvent('force:navigateToURL', {
    detail: { url: '/login' }
}));
```

or:

```js
// Wrong: using NavigationMixin but with incorrect page reference for LWR
this[NavigationMixin.Navigate]({
    type: 'comm__loginPage',  // may not resolve correctly in all LWR runtimes
    attributes: {}
});
```

**Why it happens:** LLMs are trained on large volumes of Aura community documentation and legacy LWC samples that predate LWR. Navigation in Aura communities used different event channels and page reference type names. The LLM conflates these patterns.

**Correct pattern:**

```js
import { NavigationMixin } from 'lightning/navigation';

// For LWR — use standard page reference types
this[NavigationMixin.Navigate]({
    type: 'standard__namedPage',
    attributes: { pageName: 'Login' }
});
```

**Detection hint:** Flag any generated component that uses `force:navigate*` event dispatches, `comm__loginPage` references (verify against the target runtime), or direct URL manipulation instead of `NavigationMixin`.

---

## Anti-Pattern 4: Importing Community Context Modules Without Restricting the Target

**What the LLM generates:** A component that imports `@salesforce/community/Id` or `@salesforce/user/isGuest` while also declaring internal Lightning targets in JS-meta.xml:

```xml
<targets>
    <target>lightning__AppPage</target>
    <target>lightningCommunity__Default</target>
</targets>
```

```js
import communityId from '@salesforce/community/Id'; // will fail on App Page
```

**Why it happens:** The LLM tries to make the component "reusable everywhere" without understanding the module resolution constraints. It does not model the platform runtime difference between internal Lightning and Experience Builder.

**Correct pattern:** Either restrict JS-meta.xml to only `lightningCommunity__*` targets when community imports are used, or remove community imports and use a wrapper pattern:

```js
// Base component — no community imports, receives communityId via @api
// Experience Cloud wrapper — imports @salesforce/community/Id, passes down via @api
```

**Detection hint:** Flag any component that imports `@salesforce/community/*` or `@salesforce/user/isGuest` AND also declares `lightning__AppPage`, `lightning__RecordPage`, or `lightning__HomePage` in its JS-meta.xml targets.

---

## Anti-Pattern 5: Omitting `@AuraEnabled` Guest User Profile Grant Instruction

**What the LLM generates:** Code that declares and calls an `@AuraEnabled` Apex method correctly, but deployment instructions that stop at "deploy the Apex class" without mentioning the Guest User profile access grant:

```
Step 1: Create ProductController.cls with @AuraEnabled methods
Step 2: Deploy to org
Step 3: Add component to Experience Builder page
// Done — no mention of profile access grant
```

**Why it happens:** The LLM understands `@AuraEnabled` as the complete access mechanism for Lightning components (which it is for internal users). The Guest User profile grant requirement is a secondary deployment step that is not expressed in code, so LLMs consistently omit it.

**Correct pattern:** Deployment instructions must include an explicit step:

```
After deploying ProductController.cls:
- For guest access: Setup > Experience Cloud Sites > [Site] > Workspaces >
  Administration > Guest User Profile > Apex Class Access > Add ProductController
- For portal user access: Setup > Profiles > [Portal Profile] > Apex Class Access >
  Add ProductController (or grant via Permission Set)
```

**Detection hint:** Any generated deployment guide for an Experience Cloud component that calls Apex but omits "Guest User Profile > Apex Class Access" (or equivalent permission set grant step) is missing a required step. Flag it before the guide is used.

---

## Anti-Pattern 6: Hard-Coding Site Path Instead of Using `basePath`

**What the LLM generates:** URL construction that embeds the site path prefix as a literal string:

```js
get productUrl() {
    return `/customerportal/product/${this.productId}`;
}
```

**Why it happens:** LLMs pattern-match to simple string interpolation. The `basePath` module import is an Experience Cloud-specific convention that is underrepresented in training data relative to plain string manipulation.

**Correct pattern:**

```js
import basePath from '@salesforce/community/basePath';

get productUrl() {
    return `${basePath}/product/${this.productId}`;
}
```

**Detection hint:** Search generated JS for string literals that start with `/` followed by a likely site name (`/portal`, `/community`, `/mysite`, etc.) inside URL-building methods. Any literal path prefix that is not `basePath` is a portability bug.
