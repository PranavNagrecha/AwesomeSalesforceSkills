# Well-Architected Notes — LWC Locker → LWS Migration

This skill maps primarily to **Security**, **Reliability**, and **Operational Excellence** in the Salesforce Well-Architected framework. Each pillar contributes a distinct lens on why the migration matters and how to execute it safely.

## Relevant Pillars

- **Security** — LWS is the security boundary itself. The migration is a change in the JavaScript sandbox model (per-namespace `SecureElement` proxies → per-realm isolation), so getting it right is a security-posture event:
  - *Trusted* — LWS uses standards-based browser primitives (realms, distortions) instead of custom proxies, which makes the security model auditable against the published distortion list rather than against opaque Locker proxy behaviour.
  - *Compliant* — Salesforce has announced Locker for LWC will be retired; running on the supported runtime is part of staying on a vendor-supported configuration, which is a compliance baseline for many regulated industries.
  - *Hardened* — the migration is a forcing function to remove `eval`-adjacent and `Function`-adjacent workarounds that snuck in to support old library forks; cleaner code is more reviewable.
- **Reliability** — the sandbox the LWC runs in is part of the system's reliability surface:
  - *Available* — the org-wide nature of the toggle means a botched flip can degrade every Lightning page at once. The sandbox-first runbook in `SKILL.md` is the availability-protection mechanism.
  - *Recoverable* — the toggle is reversible (flip it back), but in-flight code changes that depended on LWS realm semantics are not. Keeping the LWS flip and the workaround-removal as separable changes preserves the recover-by-toggle path.
  - *Resilient under change* — third-party libraries fail differently under LWS than Locker. Exercising every library in a sandbox before the production flip is the resilience test.
- **Operational Excellence** — flipping a runtime is an operational event, not a code refactor:
  - *Observable* — DevTools under LWS shows real DOM nodes (not `Proxy {}`), which makes production triage faster forever after. The migration improves observability permanently.
  - *Manageable* — LWS reduces the number of "Locker-shaped" code paths that operators must learn to recognise. Ops runbooks shrink.
  - *Compliant* (operational sense) — once on LWS, the org is on the supported runtime path. Future Salesforce platform changes are tested against LWS, not Locker; staying on Locker accumulates platform risk.

## Architectural Tradeoffs

- **Org-wide blast radius vs no per-component opt-out.** The flip cannot be staged per-component. The mitigation is sandbox exercise + a single defined cutover window — not per-component feature flags. Teams that want per-component rollout have to fix everything before the flip; there is no middle ground.
- **Removing Locker workarounds risks introducing different bugs.** Deep-clone shims, patched library forks, `instanceof SecureElement` guards — each of these does something. Removing them under LWS is usually correct, but each removal is a small behaviour change that needs its own test. The clean-up phase should follow the flip, not precede it, so the baseline (flipped, but with old shims still in) is testable as an intermediate state.
- **Aura LWS lags LWC LWS.** Even after a clean LWC LWS migration, mixed Aura+LWC orgs still have an Aura runtime under Aura Locker. Don't claim "the org is on LWS" without qualifying which runtime — the lift only completes when the (separate) Aura LWS toggle is also enabled.
- **Third-party library posture changes from "patched fork" to "current upstream."** This trades one kind of dependency risk (drift from the upstream library, missed security fixes in a fork) for another (upstream churn, breaking changes between major versions). The new posture is generally healthier, but it requires a routine "library version" hygiene step that the patched-fork approach didn't.

## Anti-Patterns

1. **Bundling the LWS flip with downstream clean-ups in one PR** — couples a high-risk org-wide change with localised refactors. Rollback becomes ambiguous. Always split: flip first, stabilise, then clean up workarounds in subsequent changes.
2. **Treating Jest passes as the migration sign-off** — Jest does not run inside Locker or LWS. The runtime change can only be validated by sandbox manual exercise of every page that hosts custom LWCs. (See `references/llm-anti-patterns.md` Anti-Pattern 6.)
3. **Re-introducing `eval` / `new Function` "because LWS allows it now"** — LWS removes the SecureWindow proxy but does not relax the page CSP. `eval` is still off-limits and the workaround was insecure under Locker too. (See `references/llm-anti-patterns.md` Anti-Pattern 1.)
4. **Maintaining a custom-fork library indefinitely after the flip** — a "Locker-compatible" fork that worked under Locker still works under LWS, but it is now drifting from upstream security fixes for no benefit. Migrate back to upstream as part of the post-flip clean-up.

## Official Sources Used

- **Salesforce Help — Lightning Web Security**: <https://help.salesforce.com/s/articleView?id=sf.security_lws_intro.htm&type=5> — defines the LWS architecture, the Session Settings toggle, and the relationship to Locker.
- **LWC Developer Guide — Lightning Web Security and Lightning Locker**: <https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html> — official position statement on third-party-library compatibility, real-DOM behaviour under LWS, and migration semantics.
- **LWS Distortion Viewer**: <https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-distortions.html> — the canonical reference for per-API differences between native browser behaviour and LWS-distorted behaviour. Use this when triaging a third-party-library regression after the flip.
- **Spring '23 Release Notes — Lightning Web Security GA for LWC**: <https://help.salesforce.com/s/articleView?id=release-notes.rn_security_lws_ga.htm&type=5> — confirms GA milestone and the deprecation timeline for Locker for LWC.
- **Salesforce Architects — Well-Architected Trusted (Security) pillar**: <https://architect.salesforce.com/well-architected/trusted/secure> — frames the "supported runtime" and "auditable boundary" arguments mapped to the Security pillar above.
- **Salesforce Architects — Well-Architected Resilient pillar**: <https://architect.salesforce.com/well-architected/adaptable/resilient> — frames the recoverability and "available under change" arguments for the Reliability mapping above.
- **Salesforce Architects — Well-Architected Manageable (Operational Excellence)**: <https://architect.salesforce.com/well-architected/well-managed/manageable> — frames the observability and operability improvements LWS provides.
