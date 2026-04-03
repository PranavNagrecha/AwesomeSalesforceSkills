# LWC Security Review Template

## Component Context

| Item | Value |
|---|---|
| Data source | LDS / UI API / Apex / External library |
| Uses light DOM? | Yes / No |
| Uses manual DOM? | Yes / No |
| Runs in Experience Cloud? | Yes / No |

## Checklist

- [ ] Template rendering is preferred over manual DOM work.
- [ ] DOM queries stay within component-owned elements.
- [ ] Apex boundaries use explicit sharing and intentional data enforcement.
- [ ] Third-party libraries are loaded through static resources.
- [ ] Light DOM usage is deliberate and reviewed.

## Findings

Document DOM risks, Apex risks, and any guest/external-user concerns separately.
