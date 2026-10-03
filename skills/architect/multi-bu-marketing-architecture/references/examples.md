# Examples — Multi-BU Marketing Architecture

## Example 1: Global Retail Brand Sharing Suppression Lists Across Regional Child BUs

**Context:** A global retail company has one Marketing Cloud Enterprise 2.0 org with a Parent BU and six regional Child BUs (North America, EMEA, APAC, LATAM, Middle East, ANZ). Each region operates its own email program, but privacy regulations (GDPR in EMEA, CAN-SPAM in North America) require that an opt-out recorded in any region is honored globally before any subsequent send.

**Problem:** Without a centralized suppression mechanism, a subscriber who opts out of the EMEA BU's sends continues to receive emails from the North America BU. Each Child BU maintains its own unsubscribe list and there is no cross-BU enforcement.

**Solution:**

1. In the Parent BU, create a Data Extension called `Global_Suppression_Master` with columns: `EmailAddress`, `OptOutDate`, `OptOutBU`, `Reason`.
2. Create a folder in the Parent BU named `Shared Suppression` and move `Global_Suppression_Master` into it.
3. Configure the folder's Shared Data Extension Permissions to grant **Read** access to all six regional Child BUs.
4. In each Child BU, build a nightly Automation that uses a SQL Query Activity to append that BU's local unsubscribes to `Global_Suppression_Master` (via a cross-BU write-back mechanism using the Parent BU's Automation Studio or API).
5. Reference `Global_Suppression_Master` as a suppression list in every Child BU's email send activities and Journey Builder email steps.

**Why it works:** The Shared DE in the Parent BU acts as the single source of truth for suppression. Because it is accessible to all Child BUs, a send in any region checks the same list before delivery. Changes to folder permissions are Parent-BU-admin-controlled, preventing individual regions from accidentally breaking the suppression chain.

---

## Example 2: Multi-Brand Organization with Strict Data Segregation

**Context:** A financial services holding company owns two insurance brands — Brand A targeting consumers and Brand B targeting small businesses. Both brands share a single Marketing Cloud Enterprise 2.0 org for cost efficiency, but they have separate data ownership obligations: Brand A's customer data must not be accessible to Brand B's marketing team, and vice versa.

**Problem:** If both brands are operated within a single Child BU (or the Parent BU), a misconfigured user role or a shared folder could expose Brand A's subscriber records to Brand B's team. Platform-level enforcement is needed, not just access controls.

**Solution:**

1. Create two separate Child BUs: `BrandA-Consumer` and `BrandB-SMB`.
2. Provision Brand A's marketing team exclusively in `BrandA-Consumer`; provision Brand B's team exclusively in `BrandB-SMB`. No team member has access to both Child BUs.
3. Configure separate SAP, DKIM, and Reply Mail Management for each Child BU so that sending identities are fully distinct.
4. Do not configure any Shared DE permissions between `BrandA-Consumer` and `BrandB-SMB`. The Parent BU's shared folder, if used at all, is limited to content that legitimately spans both brands (e.g., company-wide legal footer content blocks).
5. Run all analytics and reporting scoped to each Child BU independently; do not export combined subscriber data across both BUs.

**Why it works:** BU-level scoping is a platform-enforced boundary. Data Extensions, automations, sends, and subscriber records in `BrandA-Consumer` are structurally inaccessible from `BrandB-SMB` without an explicit Shared DE configuration. The absence of shared permissions is the control.

---

## Anti-Pattern: Attempting Brand Separation Within a Single Child BU

**What practitioners do:** To avoid the overhead of provisioning separate Child BUs, teams try to separate two brands within one Child BU using folder permissions and Marketing Cloud role restrictions — e.g., giving Brand A's team access only to Brand A's DE folders and restricting Brand B's team to their own folders.

**What goes wrong:** Marketing Cloud's folder-level role restrictions within a BU are not consistently enforced across all tools. A user with the Marketing Cloud Administrator role at the Child BU level can see all DEs regardless of folder-level restrictions. Journey Builder and Automation Studio also provide data access pathways that folder restrictions do not cover. The result is a permission model that appears correct but has exploitable gaps.

**Correct approach:** Use separate Child BUs for each brand. Platform-enforced BU scoping provides the clean boundary that folder restrictions within a BU cannot reliably deliver.

---

## Example 3: Business-Unit Audit Scripts and a Worked Decision Record

**Context:** A holding company runs one Marketing Cloud Engagement Enterprise 2.0 account with a Parent BU and four Child BUs: two consumer brands that share customers, one B2B brand, and one regulated insurance brand. A CRM connector and a nightly ETL job write to all four.

**Audit 1: does the integration reach every BU?** A server-to-server token is issued per BU, and only for BUs where the integration is enabled. File: `ops/mc/bu-token-audit.sh` in the marketing operations repository. This is not Salesforce core metadata; there is no `package.xml` member.

```bash
#!/usr/bin/env bash
# ops/mc/bu-token-audit.sh: request a token in each BU to prove the
# server-to-server integration is enabled there.
# Env: MC_SUBDOMAIN, MC_CLIENT_ID, MC_CLIENT_SECRET.  Args: BU MIDs.
set -euo pipefail
[ "$#" -gt 0 ] || { echo "usage: $0 MID [MID ...]"; exit 1; }
fail=0
for mid in "$@"; do
  out=$(mktemp)
  code=$(curl -sS -o "$out" -w '%{http_code}' -X POST \
    "https://${MC_SUBDOMAIN}.auth.marketingcloudapis.com/v2/token" \
    -H 'Content-Type: application/json' \
    -d "{\"grant_type\":\"client_credentials\",\"client_id\":\"${MC_CLIENT_ID}\",\"client_secret\":\"${MC_CLIENT_SECRET}\",\"account_id\":\"${mid}\"}")
  if [ "$code" = "200" ]; then
    echo "OK    MID ${mid}"
  else
    echo "ERROR MID ${mid}: HTTP ${code} (integration not enabled for this BU, or bad credentials)"
    fail=1
  fi
  rm -f "$out"
done
exit "$fail"
```

Grounding: `POST /v2/token` on the tenant's auth subdomain with `grant_type`, `client_id`, `client_secret`, and `account_id` ("MID of the target business unit") comes from Access Token for Server-to-Server Integrations; the per-BU enablement requirement comes from Integration Considerations.

**Audit 2: what does each BU do with a master unsubscribe?** A SOAP Retrieve of `BusinessUnit` with `QueryAllAccounts` returns every BU in the enterprise. Send it to the `soap_instance_url` returned with the token.

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Header>
    <fueloauth>YOUR_ACCESS_TOKEN</fueloauth>
  </soapenv:Header>
  <soapenv:Body>
    <RetrieveRequestMsg xmlns="http://exacttarget.com/wsdl/partnerAPI">
      <RetrieveRequest>
        <ObjectType>BusinessUnit</ObjectType>
        <Properties>ID</Properties>
        <Properties>Name</Properties>
        <Properties>ParentID</Properties>
        <Properties>MasterUnsubscribeBehavior</Properties>
        <QueryAllAccounts>true</QueryAllAccounts>
      </RetrieveRequest>
    </RetrieveRequestMsg>
  </soapenv:Body>
</soapenv:Envelope>
```

Grounding: `RetrieveRequest` with `ObjectType`, `Properties`, and `QueryAllAccounts` ("Queries all accounts, including parent and all children"); the `fueloauth` header from Authenticate Your SOAP API Calls; the `BusinessUnit` properties from the BusinessUnit object page. UNVERIFIED (2026-10-03): the `partnerAPI` namespace, the `/Service.asmx` path that usually follows the SOAP instance URL, and whether `MasterUnsubscribeBehavior` is retrievable (rather than only settable) were not confirmed from a fetched page. A Retrieve returning more than 2,500 records reports `MoreDataAvailable`.

**The decision record** at `docs/adr/0110-mc-bu-structure-and-unsubscribe-scope.md`:

```markdown
# ADR-0110: Flat BU tree; enterprise-wide unsubscribe for consumer brands only

## Status
Accepted (2026-10-03), Marketing Architecture Board + Privacy Counsel

## Context
- Enterprise 2.0: Content Builder assets can be shared to any BU;
  edit-shared assets propagate edits to every recipient BU.
- MasterUnsubscribeBehavior is per BU: ENTIRE_ENTERPRISE or
  BUSINESS_UNIT_ONLY. Audit 2 found all four BUs on BUSINESS_UNIT_ONLY.
- Tokens are single-BU. Audit 1 found the ETL package not enabled in
  the insurance BU; its nightly writes there had been failing.
- The CRM connector's package is owned by a BU scheduled for deletion.
  Deleting a package-owning BU breaks its OAuth flow permanently.
- All BUs share one tenant and subdomain; BU separation is access
  separation, not infrastructure isolation.

## Decision
1. Keep one tier of Child BUs. No grandchild BUs.
2. Consumer Brand A and Brand B: MasterUnsubscribeBehavior =
   ENTIRE_ENTERPRISE (shared customers, one privacy notice).
   B2B and Insurance: BUSINESS_UNIT_ONLY.
3. Recreate the CRM connector's installed package in the Parent BU
   before the old BU is deleted; enable it for all four BUs.
4. Insurance stays a Child BU. Privacy Counsel confirmed access
   separation meets the contract; revisit if a regulator asks for
   infrastructure separation.

## Consequences
### Positive
- A consumer opt-out stops both consumer brands, as the notice says.
### Negative
- B2B and Insurance opt-outs stay local by design; each brand's
  preference center must say so.
- Package migration needs a connector re-authorization window.

## Alternatives Considered
### Shared suppression data extension only, settings untouched
Rejected: duplicates a platform setting and depends on every send
referencing the list.
### Separate Marketing Cloud account for Insurance
Rejected for now: contract requires access separation only.

## Date
2026-10-03
```

**Why it works:** both audits are cheap to rerun after every new BU, and each design line rests on a documented platform behavior (per-BU unsubscribe scope, single-BU tokens, package ownership, one tenant).

