## Gotchas — Flow Element Naming Conventions

Non-obvious Salesforce platform behaviors that cause real production problems
when naming or renaming Flow elements, variables, and outcomes.

---

## Gotcha 1: API Name is immutable in the contract sense (post-package-install especially)

**What happens:** Salesforce lets you rename any Flow element or variable in
Flow Builder — there is no in-product "find references" check. After the
rename, every formula reference, fault path, and Subflow caller that
referenced the old name fails at runtime, not at save time.

**When it occurs:** any time you rename an element that is referenced
externally — most painfully when a managed/unlocked package has been
installed in subscriber orgs (subscribers cannot edit the flow but their
parent flows still call your subflow by API name).

**How to avoid:**
- Treat Subflow input/output API Names, public Flow API Names, and any
  element whose Id appears in a formula as a published contract.
- For renames, bump the Flow version per `flow-versioning-strategy`,
  keep the old variable alongside the new for a release cycle, and update
  parent callers before retiring the old version.
- Manually grep the Flow XML for every reference (`{!<OldName>` and
  `<elementReference>OldName</elementReference>`) before saving the rename.

---

## Gotcha 2: Renaming a Subflow input variable breaks parent flows silently

**What happens:** you rename `inputAccountId` → `inputAcctId` in the subflow
and save. Salesforce shows no warning. The next time a parent flow calls the
subflow, it fails with `The flow couldn't find a referenced variable
inputAccountId.`

**When it occurs:** any rename of a variable marked `Available for input` or
`Available for output` on an active subflow. Even renames done while the
parent flow is open in another tab will not trigger a warning in either tab.

**How to avoid:**
- Never rename a Subflow input/output on an active version. Create a new
  version (per `flow-versioning-strategy`), update parents, then retire.
- Document the input/output contract in the Flow Description field so Git
  diffs surface contract changes during review.
- If a rename is unavoidable, add the new variable, populate it from the old
  variable internally, deprecate the old variable in the Description, and
  remove it only after all parents are updated.

---

## Gotcha 3: Spaces and special characters are auto-replaced with underscores

**What happens:** typing `Get Open Cases` as the API Name in Flow Builder
yields an actual API Name of `Get_Open_Cases`. The Label retains the spaces.
Type `Get-Open-Cases` and you get `Get_Open_Cases` too. Type
`Get Open Cases (Today)` and you get `Get_Open_Cases_Today_`.

**When it occurs:** every time an author edits the API Name field with
non-alphanumeric input. Worst when the auto-replacement creates a name
collision with an existing element — Salesforce will append `_1`, `_2` and
the author may not notice.

**How to avoid:**
- Always type API Names with explicit underscores from the start so the
  visible name and the saved name match.
- Audit Flow XML after authoring to confirm there are no trailing
  underscores or `_<n>` collision suffixes.
- Use the Decision Guidance table in `SKILL.md` for canonical shapes.

---

## Gotcha 4: Reserved words shadow built-ins or refuse to save

**What happens:** naming a variable `null`, `true`, `false`, `Id`, `Name`,
or other reserved words causes one of three behaviors:
1. Save-time error (`Id` as a variable name).
2. Silent shadowing — `{!null}` resolves to your variable, not the built-in,
   and downstream formulas behave unexpectedly.
3. Save succeeds but runtime fails on first interview with a cryptic
   "invalid reference" error.

**When it occurs:** authors borrowing names from Apex / SOQL conventions
(`Id`, `LastModifiedDate`) or shorthand from JavaScript (`null`, `true`).

**How to avoid:**
- Never use bare reserved words. Always prefix with the resource type token
  (`varId`, `varName`) so collisions are impossible.
- See the Apex reserved word list in the Apex Developer Guide; the Flow
  Builder reserved set is a superset of the Apex one for variable purposes.

---

## Gotcha 5: Process Builder → Flow auto-conversion leaves ugly auto-generated names

**What happens:** the Process Builder → Flow conversion tool produces flows
with element API Names like `myWaitEvent_4`, `myDecision_2_A1`,
`myRule_1_A1`, `myActionCall_3`. These are valid but carry no semantic
meaning, and the conversion tool does not offer a rename pass.

**When it occurs:** every Process Builder migration. The fault emails,
metadata diffs, and downstream maintenance burden inherit the auto-names.

**How to avoid:**
- Treat the rename pass as a **required step** of the migration, not a
  cleanup item to defer. Use the Decision Guidance table in `SKILL.md` to
  apply canonical names before the first production deploy.
- Track every `my<Type>_<n>` name in the migration plan as a renamed item.
- See `process-builder-to-flow-migration` for the surrounding workflow.

---

## Gotcha 6: 80-character API Name limit truncates silently in some tools

**What happens:** Salesforce enforces an 80-character max on Flow element /
variable API Names. Long verb-object-qualifier names approach this limit
fast (`Update_OpportunityStageToClosedWonAndNotifyAccountOwnerByEmail` is
already 64 chars). Some external tools (Git diff viewers, custom metadata
parsers, third-party documentation generators) silently truncate at 60 or
72 chars and obscure the difference between two similarly-named elements.

**When it occurs:** any long qualifier on an Update or Decision element.

**How to avoid:**
- Aim for <= 60 chars in practice. If a name needs more, the qualifier is
  doing too much work — move logic into a subflow and name the subflow.
- Audit Flow XML for any `<name>` value over 60 chars and consider a
  refactor to a subflow.
