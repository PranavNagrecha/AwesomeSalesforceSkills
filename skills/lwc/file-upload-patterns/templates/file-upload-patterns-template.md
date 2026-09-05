# LWC File Upload Patterns — Work Template

Record the four decisions this skill exists to force, then attach the checker output. Anything
left blank is a decision that will be made by accident later.

## Scope

**Skill:** `file-upload-patterns`
**Component / feature:**
**Requested by / date:**

---

## 1. Tier decision

| Question | Answer |
|---|---|
| Does the parent record exist when the user picks the file? | |
| Largest file the business actually sends | |
| Pre-processing required on the bytes before storage? | |
| **Chosen tier** (`lightning-file-upload` / custom input + Apex) | |
| If Apex: why the base component was rejected | |

"More control" is not a reason. Record the specific capability the base component does not
provide.

## 2. Size budget (Apex path only)

| Item | Value |
|---|---|
| Largest raw file to accept (bytes) | |
| Raw + ~37 % base64 (`object_reference L79833`) | |
| Heap ceiling for the context (6 MB sync / 12 MB async, `apexdev L19577`) | |
| Cap constant in the Apex controller | |
| Cap constant in the JavaScript guard | |
| Measured `Limits.getHeapSize()` at the cap | |

If the third row is smaller than the second, the Apex path is not available. Say so here
rather than chunking around it.

## 3. Association and sharing

| Question | Answer |
|---|---|
| `FirstPublishLocationId` on insert, or explicit `ContentDocumentLink`? | |
| Could the file ever need a different parent record? | |
| `ShareType` (`V` / `C` / `I`) and why | |
| `Visibility` (`InternalUsers` / `AllUsers` / `SharedUsers`) and who approved it | |
| Is any linked record surfaced in an Experience Cloud site? | |

`ShareType` is a required field; `C` cannot be created from an Apex trigger
(`object_reference L77269`, `L77276-L77277`).

## 4. Surface and access

| Question | Answer |
|---|---|
| Target surface (record page / app page / LWR site / standalone) | |
| Confirmation mechanism (`lightning/toast` vs `platformShowToastEvent`) | |
| Permission set granting Apex class access | |
| Guest or Experience Cloud users in scope? If yes, who approved the design | |
| File-type allowlist, and the magic-number check that enforces it | |

## 5. Validation before release

- [ ] `python3 scripts/check_file_upload_patterns.py --manifest-dir <source tree> --strict` — output pasted below
- [ ] Jest suite covers the `uploadfinished` payload (Bundle A) or the `FileReader` + Apex mock path (Bundle B)
- [ ] Apex test asserts a `ContentDocumentLink` row exists with the intended `ShareType` and `Visibility`
- [ ] Verification SOQL run against a real upload; row count, `ShareType`, `Visibility` and byte count recorded
- [ ] Gotchas in `references/gotchas.md` reviewed against this design
- [ ] Anti-patterns in `references/llm-anti-patterns.md` not triggered by the generated code

```text
<paste checker output here>
```

## Notes and open questions
