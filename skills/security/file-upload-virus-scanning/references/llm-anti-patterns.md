# LLM Anti-Patterns — File Upload Virus Scanning

## Anti-Pattern 1: Generating A Trigger That Marks Files Clean Without Scanning

**What the LLM generates:** A ContentVersion trigger that writes `ScanStatus__c = Clean` unconditionally on insert.

**Why it happens:** Code generation without scanner integration is the simplest path.

**Correct pattern:** The trigger must enqueue or invoke the scanner; state transitions only on real verdicts.

## Anti-Pattern 2: Deleting Infected Files

**What the LLM generates:** `delete cv;` when infected.

**Why it happens:** "Delete" feels decisive.

**Correct pattern:** Quarantine — retain the record, restrict sharing, redact the blob to a sanitized placeholder. Preserves audit trail for investigation.

## Anti-Pattern 3: Gating Only The UI

**What the LLM generates:** LWC hides files where `ScanStatus__c != Clean`, but API access and Content Delivery links still serve the file.

**Why it happens:** The UI is what the engineer was looking at.

**Correct pattern:** Gate at the sharing layer (Apex-managed sharing, Public Group revocation, or library-scoped access), not just the UI.

## Anti-Pattern 4: No Fail-Open / Fail-Closed Policy

**What the LLM generates:** On scanner error, quietly set `Scan_Error` and move on.

**Why it happens:** Default-safe handling.

**Correct pattern:** Policy must be explicit. High-risk surfaces fail-closed (block access); low-risk surfaces may fail-open with a scheduled retry.

## Anti-Pattern 5: No Rescan Strategy

**What the LLM generates:** One-shot scan on upload.

**Why it happens:** The upload path is the visible one.

**Correct pattern:** Schedule rescans on a cadence. New signatures catch threats that were unknown at upload time.
