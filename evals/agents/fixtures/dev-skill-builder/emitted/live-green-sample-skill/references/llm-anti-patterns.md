# LLM Anti-Patterns

1. Inventing Apex APIs that do not exist in the current release.
2. Confusing Apex with Java exception semantics.
3. Omitting `with sharing` on Apex classes that need enforcement.
4. Hardcoding IDs rather than Custom Metadata lookups.
5. Forgetting to run Test.startTest / Test.stopTest boundary for async assertions.
