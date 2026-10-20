# LLM Anti-Patterns — Service Account Credential Rotation

## Anti-Pattern 1: Granting Password Never Expires To Avoid Rotation

**What the LLM generates:** "Set `PasswordNeverExpires = true` on the integration user record so the integration doesn't break." There is no such User field; Password Never Expires is a user permission granted through a profile or permission set (secguide 262 L6398; platform_events 264 L25315).

**Why it happens:** It solves the immediate pain.

**Correct pattern:** Build a real rotation runbook with vault-backed storage, and remove the permission (`<userPermissions><name>PasswordNeverExpires</name>`) from the integration profile and permission sets. Its presence is a critical finding.

## Anti-Pattern 2: Rotating A Shared Secret Without Coordinating Every Consumer

**What the LLM generates:** Rotate connected app secret; update one consumer; done.

**Why it happens:** The engineer sees only their consumer.

**Correct pattern:** Coordinate every consumer's switch in one window — `consumerSecret` can't be edited after save in metadata (api_meta 264 L37441-37443) and a staged old-plus-new window is UNVERIFIED (2026-10-20) — or move consumers to a new app first.

## Anti-Pattern 3: Storing Secret In Source Code

**What the LLM generates:** Hardcoded password or client secret in CI/CD variable or pipeline YAML.

**Why it happens:** Fastest path to a working pipeline.

**Correct pattern:** Secrets live in a vault. Pipelines read at runtime. Rotation updates the vault; no code change.

## Anti-Pattern 4: Post-Rotation Verification Skipped

**What the LLM generates:** Runbook ending at "update credential."

**Why it happens:** Success is assumed.

**Correct pattern:** Every rotation runbook ends with a health check — an API call or a login-history verification — before closing the ticket.

## Anti-Pattern 5: Treating Cert Expiry As Rotation

**What the LLM generates:** "Rotation cadence for JWT = cert expiry."

**Why it happens:** The expiry is the visible deadline.

**Correct pattern:** Rotate well before expiry; with one `certificate` per app (api_meta 264 L37419) the cutover needs a scheduled window. Align cadence with policy, not with cert expiry.
