# Well-Architected Notes — LWC Focus Management

## Relevant Pillars

- **User Experience** — focus management is the load-bearing a11y concern
  for dynamic UI.
- **Security** — inaccessible flows block users, which is a compliance
  concern for public-sector and regulated industries.

## Architectural Tradeoffs

- **Parent orchestrates vs children self-manage:** parent orchestration is
  cleaner for wizards; self-management is cleaner for isolated widgets.
- **Imperative `.focus()` vs declarative `autofocus`:** imperative is
  explicit and test-friendly; `autofocus` works for first render only.
- **Focus trap helpers vs roll-your-own:** helpers reduce bugs but add
  dependency.

## Official Sources Used

- LWC Shadow DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-shadow-dom.html
- WCAG — Focus Visible — https://www.w3.org/TR/WCAG21/#focus-visible
- Salesforce Accessibility — https://help.salesforce.com/s/articleView?id=sf.accessibility_overview.htm
