# Well-Architected Notes — Screen Flow Accessibility

## Relevant Pillars

- **User Experience** — accessibility is a UX baseline, not an add-on.
- **Security** — inaccessible flows can effectively lock out employees with
  disabilities, a compliance risk.

## Architectural Tradeoffs

- **Standard Flow components vs custom LWCs:** standard components inherit
  some a11y behavior; custom LWCs require explicit work.
- **One long screen vs several short ones:** long screens reduce context
  switches but lengthen Tab paths; short screens are better for assistive tech
  but add clicks.
- **Inline errors vs error summary:** inline is immediate; summary is scannable
  — do both.
- **Hard-blocking validation vs soft warnings:** hard-block is clearer for
  assistive tech but more frustrating for all users.

## Official Sources Used

- Salesforce Accessibility — https://help.salesforce.com/s/articleView?id=sf.accessibility_overview.htm
- WCAG 2.1 AA — https://www.w3.org/TR/WCAG21/
- Salesforce Well-Architected User Experience — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable
