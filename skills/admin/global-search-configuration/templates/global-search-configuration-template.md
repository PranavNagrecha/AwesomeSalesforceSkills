# Global Search Configuration — Work Template

Use this template when auditing, refreshing, or extending global search configuration in a Salesforce org.

UNVERIFIED (2026-10-20) (file-level): column caps, the synonym cap, Setup page names and the Customize Application requirement for search layouts are Help-only.

## Scope

**Skill:** `global-search-configuration`

**Request summary:** (fill in what the user asked for)

**Surface matrix:**
- [ ] Lightning Experience users present
- [ ] Classic users present
- [ ] Einstein Search enabled
- [ ] Salesforce Connect external objects in use

## Context Gathered

- **Editions / licenses:** ____________
- **User populations relying on global search heavily:** ____________
- **Customize Application permission holders (audit list):** ____________
- **Pre-existing Synonym Group count:** ____________ (cap: 2,000 — UNVERIFIED (2026-10-20), Help-only)

## Search Layout Audit — Per Object

For each object users search frequently:

| Object | searchResultsAdditionalFields | profileSearchLayouts (profiles) | lookupDialogsAdditionalFields | lookupPhoneDialogsAdditionalFields | customTabListAdditionalFields | searchFilterFields |
|---|---|---|---|---|---|---|
| Account | (current: ____) (target: ____) | | | | | |
| Contact | | | | | | |
| Case | | | | | | |
| Opportunity | | | | | | |
| (custom obj) | | | | | | |

Notes:
- Column count per list capped at 10 / 6 in a Classic lookup dialog (UNVERIFIED (2026-10-20): Help-only caps).
- First column always Name (text-type Name is mandatory, api_meta 264 L47509).
- Lists are separate fields; a profile layout overrides the default search results list.

## Synonym Groups

**Standard groups in use (UNVERIFIED (2026-10-20): Help-only):** ____________
**Custom groups (`SynonymDictionary`):** ____________
**Proposed additions:**

| Term variants | Reason | Scope-impact check (other objects affected) |
|---|---|---|
| `VIP, Priority, Strategic` | Sales tier vocabulary | Checked Accounts ✓ / Cases ✗ (Priority is a Case picklist value — synonym may pollute case search) |
| | | |

## Setup → Search Settings

| Setting | Current | Target | Reason |
|---|---|---|---|
| Lookup Auto-Completion (per object) | | | |
| Results per page (per object, `resultsPerPageCount`) | | | |
| Blank User lookup uses recently viewed users (User object only) | | | |
| Sidebar Search Settings (Classic) | | | (skip if Lightning-only) |

## External Object Searchability

For each Salesforce Connect external object expected in search:

| External Object | Data Source `Enable Search` | External Object `Allow Search` | Adapter Type | `SEARCH` capability (custom adapter) | Validated via SOSL probe? |
|---|---|---|---|---|---|
| | | | | | |

## FLS Audit Per Added Column

For every field added to a Search Layout column:

| Field | Profiles/Permission Sets WITH read FLS | Without | Action |
|---|---|---|---|
| Account.Industry | All sales profiles | Support profile | Confirm support users don't rely on column |
| | | | |

## Deployment Plan

- [ ] Sandbox-first deploy (Developer Sandbox → Full Sandbox → Production)
- [ ] Metadata API package XML built (`CustomObject` entries with `<searchLayouts>`, `synonymDictionary` entries if applicable)
- [ ] Wait at least 15 minutes after record changes before validating search hits (ldv 264 L160-162)
- [ ] Validation: global search bar + lookup picker on related object + (if applicable) Classic search
- [ ] Configuration Workbook updated with new state

## Notes

Record any deviations from the standard pattern and why. Note any external-object adapters that do not support SOSL and the workaround chosen (custom LWC, custom Search Manager, etc.).
