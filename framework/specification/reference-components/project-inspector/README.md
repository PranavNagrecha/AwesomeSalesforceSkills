# SfSkills V2 Project Inspector Add-on

This is one self-contained product component for testing the download-and-integrate workflow.

It fixes a specific architecture problem: SfSkills is not itself a Salesforce DX project, so deployment/test triage must treat local metadata as optional enrichment.

## Contents

- reviewed Python discovery and mapping implementation;
- read-only CLI;
- focused Cursor subagent definition;
- JSON output schema;
- unit tests;
- product documentation;
- exact Cursor integration/review prompt.

## Quick local validation of this bundle

From this package directory:

```bash
./run_standalone_tests.sh
```

The script creates a temporary copy of the supplied repository-relative files and runs the component test module without changing your SfSkills checkout.

## Integration

Give Cursor `CURSOR_ADD_PROJECT_INSPECTOR_PROMPT.md` and this ZIP. Cursor should merge the files into the current local V2 branch, update the native plugin builder and triage orchestration, run the full checks, make one local commit, and return the required review ZIP.
