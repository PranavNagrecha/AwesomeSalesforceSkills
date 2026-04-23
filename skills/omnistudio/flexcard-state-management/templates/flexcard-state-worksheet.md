# FlexCard State Design Worksheet

## Card Inventory

| Card Name | Role (parent/child/sibling) | Data Source | Refreshes On |
|---|---|---|---|
|   |   |   |   |

## Action Refresh Matrix

| Action | Trigger Element | Refresh Target | Reason |
|---|---|---|---|
|   |   |   |   |

## Coupling Contracts

- Parent → Child parameters:
- Sibling pubsub events (namespaced):
- Session variables (namespaced, with owner):

## Conditional Visibility Rules

| Rule | Field Read | Field Exists In Cache? | Action That Populates It |
|---|---|---|---|
|   |   |   |   |

## Sign-Off

- [ ] Each action has a justified refresh target.
- [ ] No cross-card reach-in reads.
- [ ] All pubsub events namespaced.
- [ ] All conditional-visibility fields are in the data source projection or action output.
