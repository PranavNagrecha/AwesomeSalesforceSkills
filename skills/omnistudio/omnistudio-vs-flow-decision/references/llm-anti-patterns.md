# LLM Anti-Patterns — OmniStudio vs Flow Decision

## Anti-Pattern 1: Picking A Tool Before Decomposing Layers

**What the LLM generates:** "Build this in OmniStudio" or "Build this in Flow" as one decision.

**Correct pattern:** Decompose to UI / orchestration / data. Pick per layer.

## Anti-Pattern 2: Ignoring Licensing

**What the LLM generates:** An OmniScript recommendation on a core SKU org.

**Correct pattern:** Confirm entitlement first; OmniStudio is not universal.

## Anti-Pattern 3: Recommending FlexCard For Every Record Page

**What the LLM generates:** "Use a FlexCard for this detail view."

**Correct pattern:** Use Lightning Record Page unless FlexCard features are specifically needed (designer-managed actions, IP-powered save, reuse in Experience Cloud).

## Anti-Pattern 4: Ignoring Team Skill Set

**What the LLM generates:** OmniStudio recommendation for an admin team with no OmniStudio experience.

**Correct pattern:** Ops model matters. Pick a tool the owning team can operate at the required cadence.

## Anti-Pattern 5: Using Flow For External JSON Shaping

**What the LLM generates:** A Flow with 15 formula resources producing a nested JSON string for a webhook.

**Correct pattern:** Integration Procedure with DataRaptor Transform. Flow's expression engine is not designed for JSON composition.
