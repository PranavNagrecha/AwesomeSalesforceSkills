# LLM Anti-Patterns — Flow and Platform Events

1. Treating PE as transactional
2. One PE for too many different events
3. Missing idempotency on subscribers
4. No monitoring of subscriber errors
5. Publishing PE instead of calling a service inline for trivial sync work
