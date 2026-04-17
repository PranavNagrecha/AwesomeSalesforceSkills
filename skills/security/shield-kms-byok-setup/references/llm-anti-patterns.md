# LLM Anti-Patterns — Shield Platform Encryption — BYOK / KMS Setup

1. Using default tenant secret indefinitely
2. Encrypting a field and then using SOQL LIKE on it
3. No runbook for KMS outage
4. Rotating tenant secret without running Encryption Key Rotation batch
5. Storing BYOK material in a shared drive prior to upload
