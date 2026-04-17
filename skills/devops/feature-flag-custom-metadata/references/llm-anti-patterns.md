# LLM Anti-Patterns — Feature Flags via Custom Metadata

1. Custom Setting for flags (doesn't deploy cleanly)
2. Random rollout instead of hashed
3. Never deleting old flags
4. Flag check inside inner loop (use caching)
5. Skipping the kill-switch test in staging
