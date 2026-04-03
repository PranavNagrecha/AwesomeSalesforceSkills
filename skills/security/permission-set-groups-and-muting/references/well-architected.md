# Well-Architected Notes - Permission Set Groups And Muting

## Relevant Pillars

- **Security** - least privilege depends on coherent bundles and controlled subtraction.
- **Operational Excellence** - PSGs reduce access-management sprawl only when they are named and governed well.

## Architectural Tradeoffs

- **Direct permission-set assignment vs PSGs:** flexibility versus compositional clarity.
- **Clone a bundle vs mute it:** simpler mental model versus less duplication.
- **Profile-heavy access vs profile-minimized access:** short-term familiarity versus long-term maintainability.

## Anti-Patterns

1. **Junk-drawer PSGs** - unrelated access grouped without a clear purpose.
2. **Muting as cleanup for bad design** - subtraction should not replace modeling.
3. **Profile-heavy org with token PSG adoption** - complexity increases without real governance gain.

## Official Sources Used

- Permission Set Groups - https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm&type=5
- Muting Permission Sets - https://help.salesforce.com/s/articleView?id=sf.perm_set_groups_muting_overview.htm&type=5
- Permission Sets Overview - https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm&type=5
