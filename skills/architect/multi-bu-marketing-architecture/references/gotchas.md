# Gotchas — Multi-BU Marketing Architecture

Non-obvious Marketing Cloud Engagement behaviors that cause real production problems in this domain. Each gotcha names its source. Business-unit configuration screens are documented in Salesforce Help, which does not fetch; claims that rest only on Help carry an inline `UNVERIFIED (2026-10-03):` marker. API-level behavior is grounded in the Marketing Cloud Engagement developer guide (developer.salesforce.com/docs/marketing/marketing-cloud/guide), read 2026-10-03.

## Gotcha 1: Business-Unit Access Is Per User, Per Business Unit

**What happens:** A user with an Administrator role in the Parent BU opens a Child BU through the account switcher and sees nothing or gets a permissions error. Access is not inherited down the hierarchy; each user is associated with specific business units.

**When it occurs:** Every time a Child BU is created, and whenever the central team grows. UNVERIFIED (2026-10-03): that no "inherit from parent" option exists in Setup is stated in earlier versions of this skill, not in a fetched source.

**How to avoid:** Keep a roster of users, business units, and roles, and provision each user into each Child BU they need as part of the BU creation runbook. Automate it through the API where the team manages many BUs. UNVERIFIED (2026-10-03): the REST route `POST /v2/accounts/{id}/members` cited in earlier versions was not confirmed.

**Source:** Marketing Cloud developer guide, AccountUser object: `AssociatedBusinessUnits`, "the business units the account user is associated with and is able to access"; `DefaultBusinessUnit`, "the business unit that the account user sees when they log in".

---

## Gotcha 2: Deeply Nested BU Hierarchies Complicate Send Reporting

**What happens:** Grandchild BUs (Parent, Regional Child, Country Grandchild) report independently, so regional and global send performance needs manual aggregation. UNVERIFIED (2026-10-03): the statement that standard Analytics Builder reports do not roll grandchild sends up to the grandparent is from earlier versions of this skill and was not confirmed in a fetched source.

**When it occurs:** When the org chart is copied into the BU tree.

**How to avoid:** Keep the hierarchy flat: one Parent BU and one tier of Child BUs. Group BUs for reporting by naming convention, SQL Query Activities, or an external BI tool rather than by nesting.

**Source:** Marketing Cloud developer guide, Account and BusinessUnit objects: `ParentID` and `Children` model the hierarchy for "Enterprise, and Enterprise 2.0 account children and business units". The reporting consequence is UNVERIFIED as noted.

---

## Gotcha 3: A Data Extension In The Parent BU Is Not Shared Until Sharing Is Configured

**What happens:** A suppression list or shared audience is created in the Parent BU on the assumption that Child BUs inherit it. Child BU sends proceed without it.

**When it occurs:** Whenever a cross-BU data extension is created without an explicit sharing configuration. UNVERIFIED (2026-10-03): the Shared Data Extension folder permission screens (Read or Read/Write per Child BU) are documented in Salesforce Help only.

**How to avoid:** After creating a cross-BU data extension, configure its sharing for each Child BU that needs it, then log in to a Child BU and confirm it appears. Add that check to the BU and data extension creation checklists.

**Source:** UNVERIFIED as noted. Related, grounded behavior: Content Builder assets and categories are also unshared until `sharedWith` lists the recipient MIDs (Gotcha 8).

---

## Gotcha 4: Whether A Master Unsubscribe Crosses Business Units Is A Per-BU Setting

**What happens:** Earlier versions of this skill said an unsubscribe in Child BU A never stops sends from Child BU B without a shared suppression data extension. The API documents a per-BU setting that decides it: `MasterUnsubscribeBehavior`, with values `ENTIRE_ENTERPRISE` and `BUSINESS_UNIT_ONLY`. A BU set to `BUSINESS_UNIT_ONLY` keeps master unsubscribes local; one set to `ENTIRE_ENTERPRISE` applies them across the enterprise.

**When it occurs:** When BUs are created with different settings, or when the design adds a shared suppression data extension without checking the setting it duplicates or contradicts.

**How to avoid:** Decide the unsubscribe scope per brand with legal, set `MasterUnsubscribeBehavior` accordingly on every BU, and audit it (retrieve script in `references/examples.md`). Use a shared suppression data extension for rules the setting does not express, such as a brand-level opt-out list. Test with a send from each Child BU before go-live.

**Source:** Marketing Cloud developer guide, BusinessUnit object: `MasterUnsubscribeBehavior`, "Defines how master unsubscription requests are handled for a business unit. Valid values include ENTIRE_ENTERPRISE or BUSINESS_UNIT_ONLY"; `SubscriberFilter`, "filter used to assign subscribers to a specific business unit within an Enterprise or Enterprise 2.0 structure."

---

## Gotcha 5: Sender Authentication And IP Setup Are Repeated For Each New Child BU

**What happens:** A new Child BU sends production email before its sender authentication and domain setup exist, which hurts deliverability and domain alignment. UNVERIFIED (2026-10-03): that SAP, DKIM, Reply Mail Management, and IP assignment do not carry over to new Child BUs is from earlier versions of this skill and Salesforce Help.

**When it occurs:** When a BU is created and used the same week.

**How to avoid:** Make sender authentication, reply mail, default send classification, and (where used) IP warm-up mandatory runbook steps before the first send.

**Source:** Marketing Cloud developer guide, BusinessUnit object: `DefaultSendClassification` ("default send classification for all sends from a specific business unit") and the per-BU address fields show that sending identity is configured per BU. Carry-over behavior: UNVERIFIED as noted.

---

## Gotcha 6: API Tokens Belong To One Business Unit At A Time

**What happens:** A CRM connector or ETL job authenticates once and then fails, or silently writes to the wrong BU, when it works across Child BUs. "Access tokens and refresh tokens act in the context of a single business unit." A token "doesn't flow down through child accounts". A server-to-server integration must also be enabled for each BU before it can get a token there.

**When it occurs:** When integrations are built against the Parent BU and later extended to Child BUs, or when a legacy installed package is used across many BUs.

**How to avoid:** Pass the target BU's MID as `account_id` on every `v2/token` request, enable the integration for each BU on the Installed Packages Access tab, and handle 401 and 403 for BUs the integration or user cannot reach. Prefer enhanced packages: legacy packages need a credential set per BU, enhanced packages can serve many BUs with one.

**Source:** Marketing Cloud developer guide, Integration Considerations (single-BU token context; S2S enablement per BU; `account_id`); Access Token for Server-to-Server Integrations (`account_id`: "Account identifier, or MID, of the target business unit"; 20-minute token lifetime); Authenticate Your SOAP API Calls ("It doesn't flow down through child accounts"); Installed Package Types (Business Unit Support row).

---

## Gotcha 7: Deleting The BU That Owns An Installed Package Breaks Every Integration In It

**What happens:** A business unit is retired during clean-up. The installed packages created in that BU stop authenticating, and the CRM connector or partner app fails across the enterprise. A deleted BU cannot be recovered.

**When it occurs:** During brand consolidation or when a "sandbox" BU used to create packages is tidied away.

**How to avoid:** Create installed packages in a BU that will live as long as the integrations, usually the Parent BU. Before deleting any BU, list the packages it owns and confirm they are unused.

**Source:** Marketing Cloud developer guide, Integration Considerations: "Business Units that own packages must remain active for the app to continue working. If a business unit is deleted or deprecated, the packages created under that business unit fail the OAuth 2.0 authorization flow ... After a business unit is deleted, it can't be recovered."

---

## Gotcha 8: Content Sharing Rules Differ Between Enterprise 1.0 And 2.0, And Edits Propagate

**What happens:** A team plans to share a master email from a regional BU to a sibling and cannot, or shares with edit rights and finds one brand's change appearing in every BU. In Enterprise 1.0, assets can be shared only down to child BUs; in Enterprise 2.0, to any BU. With `edit` sharing, "any edit made in one business unit appears in the other business units." A `local` share, available for emails only, gives the recipient its own copy.

**When it occurs:** When content governance assumes sharing behaves like copying, or when an Enterprise 1.0 account is planned with Enterprise 2.0 behavior.

**How to avoid:** Confirm the edition. Share templates and legal blocks with `view` or `edit` from the Parent BU, and use `local` when a brand must adapt an email. Remember `sharedWith` holds up to 100 MIDs, `0` shares with the whole enterprise, and shared categories are owned by the enterprise BU.

**Source:** Marketing Cloud developer guide, Content Builder Sharing ("In Enterprise 1.0 accounts, assets can only be shared down to child business units. In Enterprise 2.0 accounts, assets can be shared to any business unit"; up to 100 MIDs; sharing types) and Shared Categories.

---

## Gotcha 9: All Business Units Share One Tenant, So BU Separation Is Not Infrastructure Isolation

**What happens:** A regulated brand is placed in its own Child BU on the assumption that this isolates its data at the infrastructure level. Every BU in an Enterprise account sits in one tenant with one tenant-specific subdomain and shared endpoints.

**When it occurs:** When contractual or regulatory separation requirements are mapped to BUs without legal review.

**How to avoid:** Treat Child BUs as an access-control boundary inside one tenant. Where a requirement demands infrastructure separation, provision a separate Marketing Cloud account and record the decision.

**Source:** Marketing Cloud developer guide, Your Subdomain and Your Tenant's Endpoints: "A tenant represents your top-level Enterprise account and its business units"; each tenant has "a unique, system-generated subdomain".
