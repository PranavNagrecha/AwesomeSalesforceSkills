# Gotchas — Embedded Analytics Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `filter` Attribute on LWC Component Is Silently Ignored

**What happens:** The LWC `wave-wave-dashboard` component does not have a `filter` attribute. If a developer adds a `filter` attribute binding (copied from Aura documentation), the component ignores it silently — no error in the browser console, no error in Salesforce debug logs. The dashboard renders correctly but with no filter applied, showing all data instead of the filtered view.

**When it occurs:** When developers copy examples from Aura `wave:waveDashboard` documentation and apply them to the LWC component. Also occurs when AI-generated code applies the wrong attribute.

**How to avoid:** For the LWC `wave-wave-dashboard` component, always use the `state` attribute with Filter and Selection Syntax JSON. For Visualforce/Aura contexts, use `wave:waveDashboard` with the `filter` attribute. These are two different components with different APIs.

---

## Gotcha 2: Hard-Coded `dashboardDevName` Breaks on Rename or Cross-Env Promotion

**What happens:** A component with hard-coded `dashboardDevName="AccountSummaryDashboard"` silently renders nothing (or shows an error) if the dashboard is renamed, if a different dashboard developer name is used in a different environment, or if the dashboard is deactivated. No helpful error message is shown to the user.

**When it occurs:** Any time a dashboardDevName is hard-coded in component markup, wired directly in a template, or stored in a configuration file that is not environment-aware.

**How to avoid:** Store dashboard developer names in a Custom Metadata Type or Custom Setting with an Apex controller to retrieve them at runtime. Pass the retrieved value to the component attribute. This makes the configuration environment-specific and survives renames.

---

## Gotcha 3: `record-id` Binding Passes the Record ID — The Dashboard Must Use It

**What happens:** Adding `record-id={recordId}` to the LWC `wave-wave-dashboard` component passes the current Lightning record ID to the dashboard. However, if the dashboard itself does not have a binding that uses the record ID as a filter parameter, the record ID is silently ignored. The dashboard shows all data regardless of which record is open.

**When it occurs:** When the architect assumes `record-id` auto-filters the dashboard. It does not — it passes the context; the dashboard must be configured to consume that context via a binding that references the passed record ID.

**How to avoid:** Confirm that the CRM Analytics dashboard has a binding configured in Dashboard Designer that uses the passed record ID as a filter. Test by navigating to two different records and confirming the dashboard content changes.
