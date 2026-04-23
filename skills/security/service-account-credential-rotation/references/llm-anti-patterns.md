# LLM Anti-Patterns — Service Account Credential Rotation

## Anti-Pattern 1: Setting `PasswordNeverExpires` To Avoid Rotation

**What the LLM generates:** "Set `PasswordNeverExpires = true` on the integration user so the integration doesn't break."

**Why it happens:** It solves the immediate pain.

**Correct pattern:** Build a real rotation runbook with vault-backed storage. `PasswordNeverExpires` is a critical finding.

## Anti-Pattern 2: Rotating Without A Grace Window

**What the LLM generates:** Rotate connected app secret; update one consumer; done.

**Why it happens:** The engineer sees only their consumer.

**Correct pattern:** Use the dual-credential grace window; coordinate or parallelize consumer updates within the window.

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

**Correct pattern:** Rotate well before expiry; dual-cert handover needs buffer. Align cadence with policy, not with cert expiry.
