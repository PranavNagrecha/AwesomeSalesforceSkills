# Well-Architected Notes — Agent Topic Design

## Relevant Pillars

- **User Experience** - well-bounded topics make the agent feel focused instead of random.
- **Reliability** - cleaner topic routing reduces wrong-action and wrong-answer behavior.
- **Operational Excellence** - smaller, explicit topic sets are easier to review and evolve safely.

## Architectural Tradeoffs

- **Few broad topics vs many narrow topics:** broad topics are easier to list, but often too fuzzy; narrow topics are safer, but can become noisy if there are too many.
- **Flat topic list vs topic selector:** a flat list is simpler at first, but selectors help when the domain becomes too large.
- **Optimistic in-topic handling vs explicit handoff:** keeping the agent in control feels smoother, but explicit handoff is safer once the topic boundary is crossed.

## Anti-Patterns

1. **Department-style topics** - these are not sharp enough to guide reliable routing.
2. **No out-of-scope behavior** - the agent keeps operating beyond its real boundary.
3. **Topic sprawl with overlapping capabilities** - review and maintenance become unreliable.

## Official Sources Used

- Agentforce Developer Guide - https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services - https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
