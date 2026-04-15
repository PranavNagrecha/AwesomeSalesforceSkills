# Gotchas — Industries Process Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Claims Management OmniScript Remote Actions Are Bound to the Framework — Cloning Breaks Them

**What happens:** A developer clones the prebuilt FNOL OmniScript from the managed-package namespace into the org namespace to make customizations. The clone appears visually identical. During testing, the Remote Action elements that call `InsProductService` methods and Claims Management API wrappers fail silently or throw "Action not found" errors. The Claim record is created but the ClaimParticipant, coverage validation, and financial setup steps do not execute.

**When it occurs:** On orgs using the managed-package Digital Insurance Platform (DIP) path, where the prebuilt OmniScript lives in the managed package namespace. Cloning creates an org-namespace copy but the Remote Action bindings in the original script point to managed-package Apex classes. After cloning, the Remote Action element names still appear in the designer but resolve against org-namespace classes that do not exist, so the actions are skipped without an activation-time error.

**How to avoid:** Before cloning any managed-package OmniScript, confirm whether the org is on the managed-package DIP path or the native-core path. On managed-package orgs, work within the managed package's OmniScript extension points (adding custom Steps or element groups that sit alongside, not replacing, managed steps). If a full clone is genuinely required, audit every Remote Action element and re-wire it to an org-namespace Apex class that replicates the managed-package class behavior. This is significant development work — escalate to the solution architect before committing to a clone-and-modify approach.

---

## Gotcha 2: Communications Cloud Decomposition Failure Is Silent — No Error Record, No Alert

**What happens:** An admin configures EPC Product Offerings for a new bundle but does not configure corresponding decomposition rules in Industries Order Management. Commercial orders are submitted and create Order and OrderItem records successfully. The order status shows "Processing". After an interval, the order status transitions to "Completed" — but no technical order records exist in the vlocity_cmt objects. Provisioning never fires. The issue is not discovered until a customer calls to report service is not working.

**When it occurs:** Any time a new EPC Product Offering is created without a corresponding decomposition rule in Industries Order Management. This is extremely common during catalog expansions because EPC configuration and decomposition rule configuration are done by different teams or in different sprint cycles.

**How to avoid:** Add a post-EPC-configuration checklist item: for every new Product Offering or bundle added to EPC, confirm a corresponding decomposition rule exists in Industries Order Management before the offering is activated in the catalog. After configuring rules, submit a test commercial order and verify the technical order record count matches the expected number of technical fulfillment actions. Do not rely on order status alone — always query the vlocity_cmt technical order objects directly.

---

## Gotcha 3: E&U Service Order CIS Callout Failure Looks Like Success in Sandbox

**What happens:** An E&U service order is tested in a full sandbox where the CIS integration is configured to accept all requests (via mock endpoint or sandbox CIS environment). The service order executes, the status transitions to "Completed", and the ServiceContract updates correctly. The process design is signed off. In production, the CIS callout uses the live CIS endpoint which has stricter validation. The callout fails for a percentage of service orders (wrong payload format, missing required CIS field, or authentication token issue). These production service orders stall at "In Progress" indefinitely, with no alert to operations staff.

**When it occurs:** When process design and testing are done only in sandbox environments with forgiving mock CIS endpoints. The validation gap between sandbox and production CIS API behavior is not discovered until production go-live.

**How to avoid:** Include a production CIS integration validation step in the process design sign-off criteria. For each service order type, test the CIS callout against a production-equivalent CIS endpoint (typically a CIS staging environment or a CIS UAT environment that mirrors production validation rules). Design the exception path before completing the happy path: define the service order status to use for CIS failures, the alerting mechanism (custom notification, Task creation, platform event), and the manual resolution procedure. Document the CIS error response structure so operations staff can interpret callout log entries.

---

## Gotcha 4: Insurance Claims Management Module License Is Separate from FSC Insurance License

**What happens:** A project team enables FSC Insurance and configures InsurancePolicy and Claim records. They attempt to configure the Claims Management OmniScript framework (FNOL intake, Adjuster's Workbench, financial processing) and find that the Claims Management-specific features are not available in the org — the Adjuster's Workbench component is missing, the Claims Management API endpoints return 403 errors, and the prebuilt OmniScripts do not exist in the org.

**When it occurs:** When the org has the FSC Insurance permission set license but not the separate Claims Management module license. Insurance for FSC and Claims Management are sold and provisioned as separate modules. The FSC Insurance license covers policy and coverage objects; the Claims Management module license covers the full claims lifecycle process framework, Adjuster's Workbench, and Claims API endpoints.

**How to avoid:** Before designing any insurance claims process, confirm that the Claims Management module license is provisioned — check Setup > Company Information > Permission Set Licenses for the Claims Management PSL. If it is absent, no claims process design work can proceed: the required platform components and APIs are unavailable. Engage Salesforce licensing to provision the Claims Management module before starting process design.

---

## Gotcha 5: Industries Order Management Scope vs External Fulfillment Systems

**What happens:** A Communications Cloud implementation team designs order decomposition rules that terminate at technical order record creation. The provisioning engineering team later confirms that their network provisioning system does not poll for technical order records — it expects a REST webhook callback or a real-time API call when a technical order is ready. The Industries Order Management technical orders are created correctly but provisioning never starts because there is no outbound notification.

**When it occurs:** When the process design work focuses only on the Salesforce-side decomposition logic and does not extend to the downstream provisioning system integration contract. Industries Order Management creates technical order records and tracks their status — but it does not automatically push those records to an external system unless an outbound integration (Integration Procedure, Platform Event, or REST callout) is explicitly configured to do so.

**How to avoid:** During process design, include the external provisioning system integration in scope. For each technical order type, define: (a) how the external system is notified (push vs pull), (b) which Salesforce platform mechanism triggers the notification (Integration Procedure, Platform Event subscriber, or scheduled job), and (c) how the technical order status is updated in Salesforce when the provisioning system reports completion. The process design is not complete until both the Salesforce-side decomposition and the outbound notification mechanism are specified.

---

## Gotcha 6: E&U Service Order Record Type and CIS Map Must Be Configured Before Process Design

**What happens:** An admin designs an E&U service order process and builds the OmniScript capture UI for a new order type. During testing, the service order records are created with the correct field values, but the CIS callout does not fire. Investigation reveals that the new order type was not registered in the service order configuration — it has no CIS endpoint mapping and no status transition rules. The OmniScript creates a record but the platform has no instructions for what to do with it after creation.

**When it occurs:** When process design is treated as an OmniScript/UI design task only, and the service order configuration layer (order type registry, CIS endpoint mapping, status transition rules) is overlooked. The service order configuration layer is a separate setup step from the OmniScript or page layout used to capture the order.

**How to avoid:** Before designing the order capture UI, complete the service order type configuration in E&U Cloud settings: define the order type record, map it to the correct CIS endpoint, configure the status transition rules, and confirm that the CIS can receive and process the new order type. Only after this backend configuration is validated should the OmniScript or custom UI design work begin.
