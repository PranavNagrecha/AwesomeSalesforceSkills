# Gotchas — Data Cloud Provisioning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Org Model Is Permanently Fixed at Provisioning Time

**What happens:** After Data Cloud (Data 360) is enabled in an org — whether a Dedicated Home Org or an existing Sales/Service Cloud org — the deployment model cannot be changed. There is no in-place migration path from existing-org to Dedicated Home Org or vice versa.

**When it occurs:** Teams that provision in an existing org to save setup time and later discover they need Dedicated Home Org-only features (real-time CRM data streams, native Salesforce activation, certain AI-powered features). The realization typically surfaces during a feature expansion project, 3–12 months post-go-live.

**How to avoid:** Treat the org model choice as an architecture decision requiring documented stakeholder sign-off before provisioning begins. If future requirements are unclear, do not provision in an existing org without explicitly accepting and documenting that Dedicated Home Org capabilities will not be available. A pre-provisioning architecture review with a Salesforce Data Cloud specialist is strongly recommended for any enterprise implementation.

---

## Gotcha 2: Data Cloud Admin Permission Set Does Not Include Activation Target Creation

**What happens:** A user assigned the "Data Cloud Admin" permission set cannot create Activation Targets. The "New" button on the Activation Targets page is greyed out or absent. This affects even system administrators who have been given Data Cloud Admin rather than Data Cloud Marketing Admin.

**When it occurs:** During activation setup when IT assigns "Data Cloud Admin" to marketing operations users on the assumption it is the most permissive set. Affects every user who needs to connect Data Cloud to Marketing Cloud Engagement, advertising platforms, or other activation destinations.

**How to avoid:** Use the permission set assignment matrix explicitly. Only "Data Cloud Marketing Admin" and "Data Cloud Marketing Manager" include the Activation Target creation capability. If a user needs both platform administration and activation target creation, assign both Data Cloud Admin and Data Cloud Marketing Admin simultaneously — there is no single permission set that covers both fully.

---

## Gotcha 3: Ingestion API Source Registration Fails Silently Without `cdp_ingest_api` OAuth Scope

**What happens:** When registering an Ingestion API source in Data Cloud Setup, the wizard performs an OAuth authentication test. If the Connected App does not have the `cdp_ingest_api` scope, the authentication step fails with a vague "connection could not be established" or generic HTTP error. The wizard does not specify that the missing OAuth scope is the cause.

**When it occurs:** When the admin creates a Connected App for Ingestion API using a generic OAuth template (e.g., copying a scope set from a REST API integration), omitting the Data Cloud-specific `cdp_ingest_api` scope.

**How to avoid:** Before registering any Ingestion API source, verify the Connected App includes the `cdp_ingest_api` scope. In Setup > App Manager, open the Connected App, go to OAuth Settings, and confirm the scope labeled "Access and manage your data cloud ingestion API data (cdp_ingest_api)" is in the Selected Scopes list. Add it if missing and save before returning to Data Cloud Setup.

---

## Gotcha 4: Provisioning Confirmation Email Can Be Delayed — Do Not Proceed Without It

**What happens:** After clicking "Turn On Data 360" in Setup, the Data Cloud tenant provisioning process runs asynchronously. If an admin proceeds to create data spaces or assign permission sets before receiving the confirmation email, they may encounter incomplete menu options, missing Data Cloud Setup tabs, or silent failures that are difficult to diagnose.

**When it occurs:** Eager admins who click through Setup immediately after enabling Data 360 without waiting for the provisioning confirmation. More likely in large orgs where background provisioning takes longer.

**How to avoid:** Wait for the provisioning confirmation email sent to the system administrator address before taking any further Data Cloud setup actions. Do not treat the "Turn On" button click as equivalent to provisioning completion. If the email has not arrived after 24 hours, contact Salesforce Support — do not attempt to re-run provisioning manually.

---

## Gotcha 5: Data Space Permission Sets Must Be Assigned Separately From Standard Permission Sets

**What happens:** Assigning a standard Data Cloud permission set (e.g., Data Cloud User) to a user gives them platform access, but does not automatically grant them access to any specific data space. Data spaces have their own permission assignments. A user with Data Cloud User who has not been added to a data space's access list will see an empty Data Cloud environment with no data streams, segments, or objects.

**When it occurs:** During bulk user setup when admins assign the permission set via a profile or permission set group but skip the data space membership step in Data Cloud Setup (Data Cloud > Data Spaces > [data space] > Manage Assignments).

**How to avoid:** After assigning the standard permission set, explicitly assign the user to each data space they need via the Data Spaces management screen. Treat data space membership as a second, required step after permission set assignment — not as something that follows automatically.
