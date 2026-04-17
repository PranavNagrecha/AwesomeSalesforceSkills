# LLM Anti-Patterns — Agent Action Unit Tests

1. Testing only the happy path with coverage padding.
2. Asserting on user_message text.
3. Skipping the bulk test because 'the agent only sends one at a time right now'.
4. Real HTTP callouts from tests.
5. Using `@TestSetup` for data that each test mutates — causes flakiness.
