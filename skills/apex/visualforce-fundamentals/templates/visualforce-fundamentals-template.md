# Visualforce Fundamentals — Work Template

Use this template when building, reviewing, or debugging a Visualforce page and its Apex controller.

## Scope

**Skill:** `visualforce-fundamentals`

**Request summary:** (fill in what the user asked for — e.g., "Build a custom Account detail page with PDF export")

## Context Gathered

Answer these before writing any code:

- **Page purpose:** [ ] Data entry form  [ ] Read-only display  [ ] PDF output  [ ] Email template preview
- **Controller type:** [ ] Standard Controller  [ ] Standard List Controller  [ ] Custom Controller  [ ] Extension on Standard Controller
- **LEX compatibility required:** [ ] Yes  [ ] No  [ ] Unknown
- **User population:** [ ] Internal employees only  [ ] Experience Cloud guests  [ ] API/external system
- **Known constraints / limits:** (e.g., "200+ records per page", "must render as PDF")

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Standard Controller + extension (custom logic, FLS inherited for bound fields)
- [ ] Custom Controller with `WITH USER_MODE` (full Apex control, explicit FLS)
- [ ] PDF rendering via `renderAs="pdf"` (inline CSS, no JS, server-side data only)
- [ ] JavaScript Remoting / `<apex:remoteAction>` (bypass view state for read-heavy ops)

## Security Checklist

- [ ] All SOQL in custom controllers/extensions uses `WITH USER_MODE` or explicit FLS checks
- [ ] No string concatenation of user-supplied values into SOQL queries
- [ ] State-changing actions (DML) are POST-only: inside `<apex:form>` + `<apex:commandButton>`
- [ ] Page `action` attribute (if used) performs read-only data loading — no DML
- [ ] Tested with a low-privilege user — no unintended data exposure

## View State Checklist

- [ ] Display-only collections (`List<SObject>`, `Map<...>`) declared `transient`
- [ ] SOQL field lists restricted to fields actually rendered on the page
- [ ] View State Inspector run — total view state under 170 KB
- [ ] `<apex:actionRegion>` used where partial postbacks reduce unnecessary serialization

## Lightning Experience Checklist (if applicable)

- [ ] No `window.top`, `window.parent`, or cross-frame DOM access
- [ ] Navigation uses `sforce.one.*` API instead of `window.location`
- [ ] Page layout verified in LEX iframe — no broken CSS or missing components
- [ ] `<apex:slds />` or inline SLDS classes used for consistent styling

## PDF Checklist (if `renderAs="pdf"`)

- [ ] No `<script>` blocks or JS library includes
- [ ] All CSS inline in `<style>` tag — no external CDN stylesheets
- [ ] All data loaded server-side in Apex controller — no client-side data fetching
- [ ] `applyHtmlTag="false"` and `showHeader="false"` set on `<apex:page>`
- [ ] PDF output verified in browser (not just HTML preview)

## Code Review Notes

Record any deviations from standard patterns and why:

-
-

## Test Scenarios

- [ ] Admin user — verify all data renders and save actions work
- [ ] Low-privilege user — verify FLS-restricted fields are not visible or editable
- [ ] Empty data state — verify page handles zero records gracefully
- [ ] Max data state — verify view state stays under 170 KB with realistic record volume
- [ ] LEX and Classic (if both supported) — verify navigation and layout in each context
