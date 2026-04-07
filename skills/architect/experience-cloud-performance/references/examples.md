# Examples — Experience Cloud Performance

## Example 1: Eliminating Redundant Apex Wire Calls on a Customer Portal Dashboard

**Context:** A B2C customer portal built on the LWR Build Your Own template has a dashboard page with five custom LWC components: `c-account-summary`, `c-open-cases`, `c-recent-orders`, `c-loyalty-points`, and `c-contact-info`. Each component uses an independent `@wire` call to a separate Apex controller method. The product team reports that the dashboard takes 3–4 seconds to become fully interactive on average.

**Problem:** Five independent Apex wire calls fire at page load. Each carries its own HTTP round-trip to the Salesforce server. On a connection with 100ms latency, the five calls in parallel add at least 100–200ms of request overhead regardless of the actual server processing time. More critically, two of the five methods query the same Account record (once for summary fields, once for contact information). This doubles the SOQL cost and means the Account record is fetched twice from different callouts.

**Solution:**

Create a single Apex controller that returns a composite result:

```apex
public with sharing class CustomerDashboardController {

    public class DashboardData {
        @AuraEnabled public Account account;
        @AuraEnabled public List<Case> openCases;
        @AuraEnabled public List<Order> recentOrders;
        @AuraEnabled public Integer loyaltyPoints;
    }

    @AuraEnabled(cacheable=true)
    public static DashboardData getDashboardData() {
        DashboardData result = new DashboardData();

        result.account = [
            SELECT Id, Name, BillingCity, Phone, PersonEmail
            FROM Account
            WHERE Id = :UserInfo.getUserId()  // simplified; use actual relationship
            LIMIT 1
        ];

        result.openCases = [
            SELECT Id, Subject, Status, CreatedDate
            FROM Case
            WHERE AccountId = :result.account.Id AND IsClosed = false
            ORDER BY CreatedDate DESC LIMIT 5
        ];

        // ... additional queries
        result.loyaltyPoints = LoyaltyService.getPointsForAccount(result.account.Id);

        return result;
    }
}
```

Build a `c-dashboard-data-provider` LWC that calls this single wire and distributes the results to the five child components via `@api` properties. Each child component is simplified to display-only logic.

**Why it works:** One wire call replaces five. The single Apex method runs in one transaction, allowing the SOQL query for Account to be used for both the summary and contact sections without a second round-trip. The `cacheable=true` annotation on the method also allows the LWR wire service to serve a cached response on subsequent page loads within the same session, bypassing the server call entirely.

---

## Example 2: LWR Publish Timing Causes Support Escalation After Critical Fix

**Context:** An e-commerce LWR Experience Cloud site is showing an incorrect promotional banner (wrong discount percentage). The marketing team publishes a corrected version at 2:00 PM. At 2:03 PM, a customer calls support saying they still see the wrong banner.

**Problem:** The site runs on LWR with CDN enabled. The CDN caches the HTML document for 60 seconds. The customer who called at 2:03 PM opened the page at 2:01 PM, within the CDN TTL window. Their browser received the pre-publish HTML from the CDN edge node. After 60 seconds from the publish timestamp, new page loads will receive the updated HTML. Users with the old HTML open in their browser will continue to see the old version until they navigate away and reload.

**Solution:**

There is no Salesforce configuration to override the 60-second HTML CDN TTL — it is a platform-level behavior. The correct operational response is:

1. Establish a post-publish validation procedure: after publishing, wait at least 90 seconds (60s CDN TTL + 30s safety margin), then validate the live site in an incognito browser window.
2. For high-stakes content changes (pricing, legal copy), schedule publishes at low-traffic windows where the exposure window affects the fewest users.
3. Document in the operations runbook: "CDN HTML TTL is 60 seconds. After publishing, allow 60–90 seconds before declaring the publish complete and notifying stakeholders."

```text
Publish Checklist Addition:
- [ ] Site published in Experience Builder
- [ ] Wait 90 seconds
- [ ] Validate change in incognito window (confirms CDN has refreshed)
- [ ] Notify stakeholders
```

**Why it works:** The 60-second TTL is intentional — it protects origin servers from thundering herd effects when a popular page's HTML is regenerated. Communicating this behavior and building validation delays into the publish process eliminates surprise escalations and accurately sets stakeholder expectations.

---

## Anti-Pattern: Assuming Enabling CDN Will Reduce Apex Call Latency

**What practitioners do:** A team enables CDN on their LWR Experience Cloud site and expects the number of Apex wire calls visible in the browser's Network tab to decrease, or expects the latency of existing Apex calls to drop because "the CDN is now caching the data."

**What goes wrong:** CDN has no effect on Apex wire calls, `getRecord` requests, or any User Interface API calls. These are dynamic, user-scoped, and authenticated requests that must reach Salesforce origin servers. CDN only caches the static layer: HTML documents, generated JS/CSS bundles, static resources, and content assets. After enabling CDN, the browser Network tab will continue to show the same number of Apex calls with the same server-side latency.

**Correct approach:** Apex call latency reduction requires Apex-level optimization (consolidation, `cacheable=true` annotation, Salesforce Platform Cache for frequently-read data) and component architecture changes (deferred loading, data provider pattern). CDN is the correct tool for static asset delivery acceleration and is complementary to, not a substitute for, Apex optimization.
