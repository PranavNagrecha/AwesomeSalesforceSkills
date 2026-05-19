# Global Search Configuration — Work Template

Use this template when auditing, refreshing, or extending global search configuration in a Salesforce org.

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
- **Pre-existing Synonym Group count (active):** ____________ (cap: 2,000)

## Search Layout Audit — Per Object

For each object users search frequently:

| Object | Default Layout (Lightning) cols | Search Results (Classic) cols | Lookup Dialog cols | Lookup Phone Dialog cols | Tab cols | Search Filter Fields |
|---|---|---|---|---|---|---|
| Account | (current: ____) (target: ____) | | | | | |
| Contact | | | | | | |
| Case | | | | | | |
| Opportunity | | | | | | |
| (custom obj) | | | | | | |

Notes:
- Column count per slot capped at 10 (Lightning) / 6 (Classic Lookup Dialog).
- First column always Name.
- Slots are independent — configure each one needed.

## Synonym Groups

**Active standard groups:** ____________
**Active custom groups:** ____________
**Proposed additions:**

| Term variants | Reason | Scope-impact check (other objects affected) |
|---|---|---|
| `VIP, Priority, Strategic` | Sales tier vocabulary | Checked Accounts ✓ / Cases ✗ (Priority is a Case picklist value — synonym may pollute case search) |
| | | |

## Setup → Search Settings

| Setting | Current | Target | Reason |
|---|---|---|---|
| Lookup Auto-Completion (per object) | | | |
| Drop-Down List size (default 5, max 10) | | | |
| Limit to Recently Viewed Records | | | |
| Sidebar Search Settings (Classic) | | | (skip if Lightning-only) |
| Number of Search Results per Object (Classic) | | | (skip if Lightning-only) |

## External Object Searchability

For each Salesforce Connect external object expected in search:

| External Object | Data Source `Allow Search` | External Object `Allow Search` | Adapter Type | SOSL-Capable? | Validated via SOSL probe? |
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
- [ ] Wait 15 minutes after deploy in each environment before validation
- [ ] Validation: global search bar + lookup picker on related object + (if applicable) Classic search
- [ ] Configuration Workbook updated with new state

## Notes

Record any deviations from the standard pattern and why. Note any external-object adapters that do not support SOSL and the workaround chosen (custom LWC, custom Search Manager, etc.).
