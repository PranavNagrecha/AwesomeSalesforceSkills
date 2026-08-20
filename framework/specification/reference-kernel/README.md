# SFAEF reference kernel

This standard-library Python package is a tested implementation seed for the deterministic controls defined by the specification. It is not a complete SfSkills runtime and does not call Salesforce, models, or Cursor.

It provides:

- stable run/evidence/claim identifiers;
- deterministic context selection and overflow reporting;
- claim/evidence lint and confidence calculation;
- deny-by-default product policy and reference shell classification;
- run-state transition validation;
- JSON Schema validation when `jsonschema` is installed;
- review-package checksum and required-artifact validation;
- a small CLI.

Run:

```bash
cd reference-kernel
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m saef_kernel --help
```

Cursor should integrate or adapt this logic into repository conventions. It must preserve behavior through tests rather than copying code blindly.
