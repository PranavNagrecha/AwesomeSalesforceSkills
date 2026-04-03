# Agent Actions — Gotchas

## 1. Generic Action Names Hurt Selection Quality

An action can be technically functional and still be hard for the agent to choose correctly.

Avoid it:
- Name actions by business outcome.
- Keep descriptions concrete.

## 2. Prompt Actions And Transaction Actions Should Stay Separate

Generation tasks and record-mutation tasks have different risk profiles.

Avoid it:
- Use prompt-template actions for generation.
- Use Flow or Apex actions for operational side effects.

## 3. Confirmation Is A Design Requirement, Not UX Polish

Side-effecting actions without clear confirmation design are risky.

Avoid it:
- Define which actions require user confirmation.
- Decide what happens when confirmation is denied or missing.

## 4. Raw Exceptions Are Weak Agent Contracts

They may help developers, but they do not help the agent recover safely.

Avoid it:
- Return business-safe result objects where appropriate.
- Preserve technical detail in logs, not in the conversational surface.
