# SFAEF-120 — Output contract and user experience

## Output principles

A product result should be useful in one screen and inspectable in depth. Evidence must be visible without making the primary answer unreadable.

## Result anatomy

1. Status and target identity.
2. One-paragraph outcome.
3. Evidence/mode summary.
4. Prioritized findings.
5. Root cause and symptom relationships.
6. Ordered action plan.
7. Safe verification steps.
8. Unknowns, contradictions, and limits.
9. Independent review outcome.
10. Run ID and replay location.

## Requirements

SFAEF-120-001. Human-readable output MUST be rendered from validated structured output.

SFAEF-120-002. Material findings MUST show claim IDs and evidence references in a discoverable form.

SFAEF-120-003. The result MUST separate observed fact, inference, recommendation, and unknown.

SFAEF-120-004. The result MUST state execution mode and target org/project/job identities.

SFAEF-120-005. Partial results MUST explain what is unavailable and how it affects conclusions.

SFAEF-120-006. Safe verification commands MAY be displayed but MUST NOT be executed unless the product contract explicitly permits the read-only operation.

SFAEF-120-007. Destructive or mutating commands MUST NOT be presented as an automatic next step. If mentioned for human workflow context, they MUST be clearly marked outside product authority.

SFAEF-120-008. Output MUST avoid false precision, generic filler, and long unprioritized checklists.

SFAEF-120-009. The user SHOULD be able to request `why`, `show evidence`, `compare`, or `replay` without re-running all upstream tools when evidence remains valid.

## Accessibility and portability

SFAEF-120-020. Core results MUST be representable as Markdown and JSON.

SFAEF-120-021. Severity, confidence, and status MUST not rely on color alone.

SFAEF-120-022. Host-specific rich UI MAY enhance but must not hide required information.
