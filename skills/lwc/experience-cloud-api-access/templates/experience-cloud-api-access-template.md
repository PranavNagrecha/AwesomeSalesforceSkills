# Experience Cloud API Access — Design Template

Use this template when designing or reviewing API access for Experience Cloud external users. Fill in all sections before implementing or recommending changes.

---

## Scope

**Skill:** `experience-cloud-api-access`

**Request summary:** (fill in what the user asked for)

**Site URL / name:** (fill in)

---

## User Context

- **User type:** [ ] Guest (unauthenticated) [ ] Authenticated external user
- **License tier:** [ ] Customer Community [ ] Customer Community Plus [ ] Partner Community [ ] Other: _____
- **Profile name:** (fill in — required to locate the guest profile or external profile)
- **Is API entitlement present?** Customer Community = No. Customer Community Plus / Partner Community = Yes (subject to profile configuration).

> STOP: If license is Customer Community and the requirement is direct REST/SOAP API access, the requirement cannot be met with this license. Document the gap and recommend a license upgrade or mid-tier integration pattern before proceeding.

---

## API Access Requirement

- **Type of access needed:** [ ] On-page data (LWC + Apex) [ ] Direct REST API [ ] Direct SOAP API [ ] Bulk API [ ] Other: _____
- **Objects and fields required:** (list the sObjects and specific fields the API call must return or modify)
- **Operation types:** [ ] Read [ ] Create [ ] Update [ ] Delete
- **Calling context:** [ ] LWC component on Experience Cloud page [ ] External mobile app [ ] Server-side integration [ ] Other: _____

---

## Guest Profile Audit (Guest Users Only)

Complete this section if any access path involves guest (unauthenticated) users.

- **Guest profile name:** (automatically named `[Site Name] Guest User`)
- **Object permissions on guest profile:** (list objects and whether Read/Create/Edit/Delete is enabled — should be minimum necessary)
- **FLS on guest profile:** (list fields with read access — this is the hard enforcement boundary, not permission sets)
- **Apex classes enabled on guest profile:** (list classes the guest user can invoke)
- **External OWD for each required object:** (check Setup > Sharing Settings > External Access column)

---

## Authenticated External User Configuration (Customer Community Plus / Partner Community Only)

- **"API Enabled" on profile:** [ ] Yes [ ] No — must be Yes for any direct API access
- **Connected App name:** (fill in)
- **OAuth scopes granted:** (minimum should be `api`; flag if `full` or `admin` are included)
- **OAuth flow type:** [ ] Username-Password (server-to-server) [ ] Web Server (interactive) [ ] JWT Bearer (machine-to-machine) [ ] Other: _____
- **Token lifetime / refresh token policy:** (fill in)

---

## Sharing Configuration Review

- **External OWD for each required object:** (table: Object | Internal OWD | External OWD | Gap?)
- **Sharing Sets configured:** [ ] Yes [ ] No [ ] Not applicable
  - If yes, list mapping rules (e.g., `User.AccountId = Case.AccountId`)
- **Share Groups configured:** [ ] Yes [ ] No [ ] Not applicable
- **Sharing Debugger verification done:** [ ] Yes [ ] No (run Setup > Sharing Settings > Sharing Debugger with a test user)

---

## Apex Class Review (On-Page Access)

For each Apex class callable by external or guest users:

| Class Name | Sharing Mode | FLS Checked? | CRUD Checked? | Guest Profile Enabled? |
|---|---|---|---|---|
| (fill in) | with sharing / without sharing / inherited sharing | Yes / No | Yes / No | Yes / No / N/A |

All guest-accessible Apex must be `with sharing`. Flag any `without sharing` or missing sharing declaration.

---

## Test Plan

- [ ] Tested as guest user (not sysadmin): expected data returned, out-of-scope data not returned
- [ ] Tested as external user with actual license type: API calls succeed, sharing enforces correctly
- [ ] Negative test: records outside the user's sharing access return zero rows, not an error
- [ ] API usage monitored: call volume does not exceed daily allocation for the org
- [ ] Sharing Debugger confirms expected access

---

## Risk Notes

(Record any deviations from the standard pattern, compensating controls, or known limitations)

---

## Checklist Before Marking Complete

- [ ] License tier confirmed — Customer Community users are not being asked to call REST/SOAP API directly
- [ ] Guest profile FLS is the minimum necessary — no extra object or field permissions left open
- [ ] Every guest-accessible Apex class is declared `with sharing`
- [ ] External OWDs reviewed for all objects — they are not assumed to match internal OWDs
- [ ] "API Enabled" enabled on external user profile (Customer Community Plus / Partner Community only)
- [ ] Connected App OAuth scope is `api` (not `full`) for external user integrations
- [ ] Sharing Debugger or real-user test confirms correct record visibility
- [ ] API usage allocation reviewed
