# Remote Site Settings — Work Template

Use this template when configuring Remote Site Settings or CSP Trusted Sites.

## Scope

**Skill:** `remote-site-settings`

**Issue type:** [ ] Apex callout failing  [ ] Lightning component resource loading failing  [ ] Both  [ ] New integration setup

## Diagnosis

**Error message observed:**
(paste exact error here)

**Call origin:** [ ] Apex Http.send() (server-side)  [ ] Lightning fetch/XHR (browser-side)  [ ] Both

**Correct control to configure:**
- Apex callout → Remote Site Settings
- Lightning component resource → CSP Trusted Sites
- Both → Both must be configured separately

## Remote Site Settings Configuration

**External endpoint URL:** (copy exact URL from Apex code, including protocol)

| Field | Value |
|---|---|
| Remote Site Name | (alphanumeric, no spaces) |
| Remote Site URL | (exact URL with protocol: https://...) |
| Disable Protocol Security | [ ] true (only for HTTP or self-signed certs)  [ ] false (standard) |
| Active | [ ] true |
| Description | (integration name and purpose) |

- [ ] Remote Site Setting added in org
- [ ] Apex callout tested successfully

## CSP Trusted Sites Configuration (if Lightning component is involved)

| Field | Value |
|---|---|
| Site Name | |
| Site URL | |
| Directives | [ ] connect-src  [ ] script-src  [ ] img-src  [ ] other |

- [ ] CSP Trusted Site added in org
- [ ] Lightning component resource loading tested

## Deployment Package Checklist

**Deployment method:** [ ] Change Set  [ ] SFDX/sf CLI  [ ] Manual

For Change Set:
- [ ] Remote Site Setting added to Change Set (Component Type: Remote Site Setting)

For SFDX:
- [ ] `remoteSiteSettings/` folder included in deployment package
- [ ] `RemoteSiteSetting` metadata type in `package.xml`

## Notes

(Record any deviations and protocol verification steps taken.)
