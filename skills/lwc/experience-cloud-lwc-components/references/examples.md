# Examples — Experience Cloud LWC Components

## Example 1: Guest-Accessible Product Catalog Component

**Context:** A B2C portal built on LWR Experience Cloud. Anonymous (guest) visitors browse a product catalog; authenticated users also see a "Add to Cart" button. The component fetches product data via Apex.

**Problem:** Without explicit `with sharing` on the Apex class and a profile grant for the Guest User, the component either throws `System.NoAccessException` at runtime or silently returns records the guest user should not see.

**Solution — Apex class:**

```apex
public with sharing class ProductCatalogController {
    @AuraEnabled(cacheable=true)
    public static List<Product2> getActiveProducts() {
        return [
            SELECT Id, Name, Description, ProductCode
            FROM Product2
            WHERE IsActive = TRUE
            WITH USER_MODE
            LIMIT 200
        ];
    }
}
```

**Solution — LWC JS:**

```js
import { LightningElement, wire } from 'lwc';
import isGuest from '@salesforce/user/isGuest';
import basePath from '@salesforce/community/basePath';
import getActiveProducts from '@salesforce/apex/ProductCatalogController.getActiveProducts';

export default class ProductCatalog extends LightningElement {
    isGuest = isGuest;
    basePath = basePath;

    @wire(getActiveProducts)
    products;

    get productDetailBase() {
        // Construct site-relative URL using basePath — never hard-code the prefix
        return `${this.basePath}/product/`;
    }
}
```

**Solution — JS-meta.xml:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>61.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Default</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightningCommunity__Default">
            <property name="productsPerRow" type="Integer" default="3"
                      label="Products Per Row" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Post-deployment step:** In Setup > Experience Cloud Sites > [Site] > Workspaces > Administration, navigate to Guest User Profile. Under Apex Class Access, add `ProductCatalogController`. Without this step the `@AuraEnabled` call returns a 403 for unauthenticated users even though the class compiles cleanly.

**Why it works:** `with sharing` enforces OWD and sharing rules for whatever user context runs the query. `WITH USER_MODE` additionally enforces CRUD and FLS. The profile grant makes the `@AuraEnabled` method callable by the site's guest identity. `basePath` ensures the link prefix is always correct regardless of sandbox vs production site path.

---

## Example 2: Authenticated Portal User Profile Component Using Community Context

**Context:** A Customer Community Plus portal on LWR. After login, users land on a dashboard that shows their open cases and a link to their account detail page. The component must work across multiple sandboxes where the site path prefix differs.

**Problem:** Hard-coding the site path (e.g., `/customerportal/`) breaks when the component is deployed to a sandbox where the path is `/customerportal-dev/`. Constructing navigation URLs without `basePath` produces broken links.

**Solution — LWC JS:**

```js
import { LightningElement, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import communityId from '@salesforce/community/Id';
import basePath from '@salesforce/community/basePath';
import getOpenCases from '@salesforce/apex/PortalDashboardController.getOpenCases';

export default class PortalDashboard extends NavigationMixin(LightningElement) {
    communityId = communityId;

    @wire(getOpenCases, { communityId: '$communityId' })
    openCases;

    navigateToAccountPage() {
        this[NavigationMixin.Navigate]({
            type: 'standard__objectPage',
            attributes: {
                objectApiName: 'Account',
                actionName: 'list'
            }
        });
    }

    get caseListUrl() {
        // basePath is the portal path prefix, e.g. /portal or /customerportal-dev
        return `${basePath}/cases`;
    }
}
```

**Solution — Apex class:**

```apex
public with sharing class PortalDashboardController {
    @AuraEnabled(cacheable=true)
    public static List<Case> getOpenCases(String communityId) {
        return [
            SELECT Id, Subject, Status, CreatedDate
            FROM Case
            WHERE Status != 'Closed'
            AND ContactId = :UserInfo.getUserId() // adjust for contact lookup
            WITH USER_MODE
            ORDER BY CreatedDate DESC
            LIMIT 50
        ];
    }
}
```

**Post-deployment step:** Assign `PortalDashboardController` Apex class access to the Customer Community Plus User profile (or the Permission Set assigned to portal users). Guest users do not need access to this component because it only renders after authentication (`isGuest` would be `false`).

**Why it works:** Passing `communityId` to Apex enables server-side scoping when a single org hosts multiple communities. Using `basePath` for URL construction decouples the component from the site's path, making it deployable across environments without modification. `NavigationMixin` with `standard__objectPage` works in both LWR and Aura runtimes for standard object navigation.

---

## Anti-Pattern: Importing Community Context Modules in an Internal Component

**What practitioners do:** Add `@salesforce/community/Id` or `@salesforce/user/isGuest` imports to a component that is also exposed on internal Lightning pages (e.g., `lightning__AppPage` target) to reuse the same component in both contexts.

**What goes wrong:** When the component renders on an internal Lightning App Page or Record Page, the platform cannot resolve `@salesforce/community/*` or `@salesforce/user/isGuest` because these modules are scoped to Experience Builder. The component fails to load with a module resolution error for all users on that page, not just external ones.

**Correct approach:** Split the component into a context-agnostic base component (no community imports) and a thin Experience Cloud wrapper that imports the community modules and passes values down via `@api` properties. The base component is safely reusable in both internal and external contexts.
