# Package and review validators

## Validate this specification kit

```bash
python3 tools/validate_spec_package.py
```

The check is offline and validates schemas, cross-references, requirements, product read-only constraints, context ceilings, sample runs, links, and package cleanliness.

## Validate Cursor's returned review ZIP

```bash
python3 tools/validate_cursor_return.py /path/to/sfskills-v2-cursor-return-YYYYMMDD-HHMMSS.zip --deep
```

Add `--release` only when Cursor claims a completed V2 release candidate. A blocked return package can pass structural validation while preserving real failing test logs; it cannot pass release validation.

The built-in scan detects only high-risk secret patterns. It supplements rather than replaces a dedicated secret scanner in the Cursor implementation.
