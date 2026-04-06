# reCAPTCHA and Bot Prevention — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `recaptcha-and-bot-prevention`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Public-facing surfaces in scope:** (list: Web-to-Case, Web-to-Lead, Experience Cloud forms, Headless Identity, other)
- **reCAPTCHA version(s) needed:** (v2 checkbox / v2 invisible / v3 score-based)
- **Google reCAPTCHA keys available:** (yes — existing project / no — need to register)
- **Current spam volume and type:** (automated bots / human spam farms / unknown)
- **Environment key separation:** (separate keys per org / shared keys — needs fix)

## Approach

**Pattern selected:** (Built-in toggle / Custom Apex verification / Headless Identity v3 config / Layered defense)

**Why this pattern:** (reference Decision Guidance table from SKILL.md)

## Implementation Checklist

### Configuration

- [ ] Google reCAPTCHA project registered with correct version
- [ ] Site key and secret key generated for each environment (prod, sandbox)
- [ ] Secret key stored in Named Credential or Custom Metadata Type — not in Apex source
- [ ] CSP Trusted Sites added: `https://www.google.com` and `https://www.gstatic.com`
- [ ] Remote Site Setting added: `https://www.google.com`

### For Built-In Toggle (Web-to-Case / Web-to-Lead)

- [ ] "Require reCAPTCHA Verification" enabled in Setup
- [ ] HTML form regenerated after enabling the toggle
- [ ] New HTML deployed to all external sites hosting the form
- [ ] Old HTML form removed from all locations

### For Custom Apex Verification (Experience Cloud / Custom UI)

- [ ] LWC loads reCAPTCHA script from Google CDN
- [ ] Token generated at submit time, not page load
- [ ] Token passed to `@AuraEnabled` Apex method
- [ ] Apex method calls `https://www.google.com/recaptcha/api/siteverify` with POST
- [ ] Apex checks HTTP status code before parsing response
- [ ] For v3: score compared against configured threshold
- [ ] DML occurs only after successful verification

### For Headless Identity

- [ ] reCAPTCHA v3 key (not v2) configured in Headless Identity Settings
- [ ] Score threshold set and documented
- [ ] Mobile app / client passes token in `X-Recaptcha-Token` header

### Layered Defenses (if applicable)

- [ ] Honeypot hidden field added to form
- [ ] Server-side rate limiting implemented (Platform Cache or custom object)
- [ ] Email domain denylist applied for disposable email providers
- [ ] Transaction Security policy configured for bulk record creation

## Testing

- [ ] Submission succeeds with valid reCAPTCHA token from real browser
- [ ] Submission fails with missing token — user sees a clear error
- [ ] Submission fails with expired token (waited > 2 minutes)
- [ ] Submission fails with invalid/forged token
- [ ] For v3: submission fails when score is below threshold
- [ ] Incognito/private browser test confirms widget renders correctly

## Notes

(Record any deviations from the standard pattern and why.)
