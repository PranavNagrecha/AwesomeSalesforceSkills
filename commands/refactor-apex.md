# /refactor-apex — Refactor an Apex class to canonical patterns

Wraps [`agents/apex-refactorer/AGENT.md`](../agents/apex-refactorer/AGENT.md). Takes a target class, returns a refactored version + test class using `templates/apex/`.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Path to the Apex class to refactor?
   Example: force-app/main/default/classes/AccountTrigger.cls

2. Any related paths the refactorer should read alongside it?
   (Helper classes, existing test class — optional)

3. Is a target-org alias connected for MCP lookups? [optional]
   (If yes, the refactorer will call validate_against_org to check for existing frameworks)
```

If the source path is missing or the file doesn't exist, STOP and ask for a valid path. Do not guess.

---

## Step 2 — Load the agent

Read `agents/apex-refactorer/AGENT.md` in full. Also read every file it lists under **Mandatory Reads Before Starting**.

---

## Step 3 — Execute the plan

Follow the 5-step plan inside the AGENT.md exactly:
1. Classify the class shape
2. Apply templates
3. Insert CRUD/FLS enforcement
4. Generate the test class
5. (Optional) org validation

---

## Step 4 — Deliver the output

Return the Output Contract block from the AGENT.md:
- Summary (shape, templates applied, confidence)
- Refactored files (one fenced block per generated file)
- Diff summary with per-change citation
- Risk notes
- Citations

---

## Step 5 — Recommend follow-ups

After the refactor, suggest running (but do not auto-invoke):
- `/scan-security` on the refactored class
- `/optimize-soql` if the class contains SOQL
- `/gen-tests` if the generated test class needs extension

---

## What this command does NOT do

- Does not commit or deploy the refactored code.
- Does not run multiple files in a single invocation.
- Does not freestyle — every change cites a template or skill.
