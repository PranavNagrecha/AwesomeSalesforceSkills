# Gotchas — Apex Design Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Service Layers Become God-Classes Faster Than Teams Expect

**What happens:** The team adds every new concern to the service layer because it already “owns orchestration.”

**When it occurs:** There is no discipline about when logic belongs in domain, selector, or integration-specific collaborators.

**How to avoid:** Review service classes for mixed responsibilities regularly and split them when they absorb query definitions, validation rules, and transport details together.

---

## Selector Reuse Can Backfire If Field Lists Balloon

**What happens:** One selector method keeps accumulating more fields for every caller until the query is no longer efficient or reviewable.

**When it occurs:** Teams use one broad “selectEverything” method instead of intent-specific selectors.

**How to avoid:** Keep selectors focused on use cases and create separate methods for distinct query shapes.

---

## `Test.isRunningTest()` Is A Design Smell, Not Dependency Injection

**What happens:** Production code branches around integrations or expensive logic only in test context.

**When it occurs:** There is no interface boundary or injected collaborator.

**How to avoid:** Use interfaces and factories so tests replace the dependency cleanly.

---

## Framework-Like Naming Does Not Equal Good Design

**What happens:** Classes are named `SomethingService`, `SomethingSelector`, and `SomethingDomain`, but each still performs mixed responsibilities.

**When it occurs:** Teams copy naming conventions without enforcing the actual behavioral contract of each layer.

**How to avoid:** Review what each class does, not just what it is called.
