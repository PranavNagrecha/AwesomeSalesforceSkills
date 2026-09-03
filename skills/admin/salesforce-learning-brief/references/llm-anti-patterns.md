# LLM Anti-Patterns

Use this list after drafting the learning brief. A polished lesson that contains any of these patterns is not complete.

## 1. Memory fill-in

**Mistake:** Add plausible Salesforce behavior that the research packet did not establish.

**Why it happens:** The model recognizes the topic and tries to make the lesson comprehensive.

**Correct form:** Teach only mapped claims. Put missing or contradictory statements under `Do Not Teach as Fact`, state the confidence impact, and identify the evidence needed.

## 2. Audience cosplay

**Mistake:** Change tone or vocabulary while teaching the same content to an administrator, developer, architect, and release manager.

**Why it happens:** Personalization is reduced to style rather than task selection.

**Correct form:** Change prerequisites, mental model, decision points, example, depth, practice, and knowledge checks according to the learner's role, current level, and intended outcome.

## 3. Citation appendix

**Mistake:** Put a source list at the end without mapping sources to the claims taught.

**Why it happens:** Bibliographies are easier than maintaining provenance throughout a lesson.

**Correct form:** Keep claim IDs from the research packet or place citations beside the supported statement. Explain which evidence is official behavior, recommendation, org fact, inference, or scenario assumption.

## 4. Recommendation as guarantee

**Mistake:** Rewrite “consider,” “recommended,” or “typically” as “Salesforce requires” or “always.”

**Why it happens:** Definitive language sounds clearer and more authoritative.

**Correct form:** Preserve modality. Distinguish enforced platform rules, documented recommendations, repository opinion, and scenario choice. State exceptions and prerequisites when the evidence supplies them.

## 5. Illustrative-org fabrication

**Mistake:** Imply that sample objects, fields, products, permissions, licenses, or feature settings exist in the learner's org.

**Why it happens:** Concrete examples feel more useful when written as real configuration.

**Correct form:** Label illustrative names and assumptions. Separate “in this example” from “in your org,” and require describe/retrieval evidence before making target-specific claims.

## 6. Release erasure

**Mistake:** Teach preview, retired, renamed, or version-gated behavior as current everywhere.

**Why it happens:** Learning material is simplified into timeless steps.

**Correct form:** Include the applicable Salesforce release, API/tool version, product, host, edition/license, or lifecycle caveat. When official sources disagree by rollout stage, teach the validation decision instead of one universal setup.

## 7. Definition dump

**Mistake:** Reproduce documentation order or a glossary without helping the learner reason about the system.

**Why it happens:** Definitions are easy to summarize and appear complete.

**Correct form:** Start with the outcome and mental model, introduce the smallest concept set, show decision points and causal relationships, then demonstrate one worked example.

## 8. Example without verification

**Mistake:** Provide steps or code with no expected result, failure signal, or proof boundary.

**Why it happens:** The example ends when the artifact is produced.

**Correct form:** State assumptions, inputs, safe environment, expected result, verification command/check, and what success does not prove. Keep sample values illustrative.

## 9. Trivia quiz

**Mistake:** Ask learners to repeat labels, menu paths, or wording from the brief.

**Why it happens:** Recall questions are simple to generate and grade.

**Correct form:** Change one constraint, ask the learner to choose or diagnose, and provide answer reasoning. Test misconceptions, evidence boundaries, and transfer to a neighboring scenario.

## 10. Unsafe lab

**Mistake:** Propose production metadata changes, broad permission grants, unrestricted queries, or data mutation as practice.

**Why it happens:** Realistic exercises are confused with live operational authority.

**Correct form:** Use conceptual, read-only, scratch, or explicitly approved non-production practice. Name the target, authority, acceptance checks, cleanup, and stop condition. Never assume production permission.

## 11. Everything-at-once brief

**Mistake:** Cover every neighboring Salesforce feature because it is related to the topic.

**Why it happens:** The model tries to maximize coverage and anticipates follow-up questions.

**Correct form:** Keep one observable learning outcome. List prerequisites and deferred topics explicitly; recommend only the single next lesson that most directly advances the outcome.

## 12. Confidence laundering

**Mistake:** Hide unknowns, failed retrievals, or unsupported claims because the final lesson reads more smoothly without them.

**Why it happens:** Uncertainty interrupts pedagogy and can sound less helpful.

**Correct form:** Include a concise caveat where it changes action, preserve a `Do Not Teach as Fact` section, and cap confidence according to missing evidence. Honest partial teaching is preferable to fabricated completeness.
