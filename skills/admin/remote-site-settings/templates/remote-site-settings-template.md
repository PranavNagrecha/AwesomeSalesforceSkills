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
- Lightning component resource → Trusted URL (`CspTrustedSite`, formerly CSP Trusted Sites)
- Apex callout to `callout:<NamedCredential>` → no Remote Site Setting needed (apexdev 264 L34761)
- Both → Both must be configured separately

## Remote Site Settings Configuration

**External endpoint URL:** (copy exact URL from Apex code, including protocol)

| Field | Value |
|---|---|
| Remote Site Name | (letters and underscores, starts with a letter, no double or trailing underscore) |
| Remote Site URL | (exact URL with protocol: https://...) |
| Disable Protocol Security | [ ] false (standard)  [ ] true (lets code pass data between HTTPS and HTTP sessions; needs security sign-off — not a certificate switch) |
| Active | [ ] true |
| Description | (integration name and purpose) |

- [ ] Remote Site Setting added in org
- [ ] Apex callout tested successfully

## CSP Trusted Sites Configuration (if Lightning component is involved)

| Field | Value |
|---|---|
| Site Name | |
| Site URL | |
| Directives | [ ] isApplicableToConnectSrc  [ ] FontSrc  [ ] FrameSrc  [ ] ImgSrc  [ ] MediaSrc  [ ] StyleSrc (there is no script-src flag) |

- [ ] Trusted URL added in org
- [ ] Lightning component resource loading tested

## Deployment Package Checklist

**Deployment method:** [ ] Change Set  [ ] SFDX/sf CLI  [ ] Manual

For Change Set:
- [ ] Remote Site Setting added to Change Set explicitly (UNVERIFIED (2026-10-21): the Component Type picker label and whether Change Sets ever add it as an Apex dependency are Help-only)

For SFDX:
- [ ] `remoteSiteSettings/<Name>.remoteSite` files included in deployment package
- [ ] `check_remote_site_settings.py --manifest-dir <dir>` run clean
- [ ] `RemoteSiteSetting` metadata type in `package.xml`

## Notes

(Record any deviations and protocol verification steps taken.)
