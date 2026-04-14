# Examples — Embedded Analytics Architecture

## Example 1: Record-Context Account Dashboard with Silently-Broken Filter

**Context:** A developer embeds a CRM Analytics dashboard on the Account record page. The dashboard should filter automatically to show only data for the current Account.

**Problem:** The developer uses the legacy Aura `wave:waveDashboard` `filter` attribute syntax in the LWC `wave-wave-dashboard` component. The component renders the dashboard successfully but no filter is applied — the dashboard shows all data for all accounts instead of the current record.

**Solution:**
Use the LWC `state` attribute with the correct Filter and Selection Syntax JSON:

```html
<!-- Correct LWC approach — uses state attribute, NOT filter attribute -->
<c-wave-dashboard
  dashboard-dev-name={dashboardDevName}
  record-id={recordId}
  state={dashboardState}
  height="500">
</c-wave-dashboard>
```

```javascript
// In the LWC component JS
get dashboardState() {
  return JSON.stringify({
    filters: [{
      field: "Opportunity.AccountId",
      operator: "in",
      value: [this.recordId]
    }]
  });
}
```

**Why it works:** The `state` attribute on the LWC component takes the complete Filter and Selection Syntax JSON. The `filter` attribute (legacy Aura-style) is silently ignored by the LWC component.

---

## Example 2: Dynamic dashboardDevName Resolution Across Environments

**Context:** An architect designs an embedded analytics solution where different user profiles see different dashboards (Sales Rep dashboard vs VP Rollup dashboard). The solution must work across sandbox and production.

**Problem:** Hard-coding `dashboardDevName="SalesRepDashboard_v3"` works in sandbox but breaks in production where the dashboard was renamed to `SalesRepDashboard_FY26`. The page renders nothing with no error.

**Solution:**
Store dashboard dev names in a Custom Metadata Type and resolve at runtime:

```apex
// CustomMetadata: Analytics_Dashboard_Config__mdt
// Fields: Profile_Name__c (text), Dashboard_Dev_Name__c (text)
public with sharing class AnalyticsDashboardController {
    @AuraEnabled(cacheable=true)
    public static String getDashboardDevName(String profileName) {
        Analytics_Dashboard_Config__mdt config = [
            SELECT Dashboard_Dev_Name__c
            FROM Analytics_Dashboard_Config__mdt
            WHERE Profile_Name__c = :profileName
            LIMIT 1
        ];
        return config?.Dashboard_Dev_Name__c;
    }
}
```

```javascript
// In the LWC component — call Apex on connectedCallback
connectedCallback() {
  getDashboardDevName({ profileName: this.userProfile })
    .then(devName => { this.dashboardDevName = devName; });
}
```

**Why it works:** Dashboard dev names stored in Custom Metadata are environment-independent and can be set differently per org. No hard-coded values in component markup.

---

## Anti-Pattern: Using `filter` Attribute on LWC Component

**What practitioners do:** Copy Aura `wave:waveDashboard` documentation examples that use the `filter` attribute and apply them to the LWC `wave-wave-dashboard` component.

**What goes wrong:** The LWC component silently ignores the `filter` attribute. The dashboard renders without any filter applied. No error appears in browser console or Salesforce debug logs. The practitioner assumes there is a dashboard configuration problem or a permissions issue and spends hours debugging the wrong thing.

**Correct approach:** Use the `state` attribute with Filter and Selection Syntax JSON for the LWC `wave-wave-dashboard` component. Reserve the `filter` attribute for the legacy Aura `wave:waveDashboard` component used only in Visualforce contexts.
