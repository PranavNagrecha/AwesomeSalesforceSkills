# Telemetry and privacy

## Local default

Runs are local and redacted. Telemetry is transparent and deletable. Do not transmit customer org/project data by default.

## Useful local metrics

- product, mode, versions, terminal status;
- selected context IDs and cost;
- tool operation IDs, bytes, truncation, duration, error class;
- evidence/claim counts and lint/reviewer findings;
- scenario grades;
- install/doctor and host capability status.

## Data classes

- public framework metadata;
- local project metadata/source;
- org metadata/configuration;
- org business data;
- user/person identity;
- logs/job/test evidence;
- credential secret.

Credential secrets are never persisted or model-exposed. Business/user data is minimized. Run bundles use redacted content or local references and follow retention policy.

## Opt-in aggregate product research

With informed consent, collect only aggregate/sanitized values needed to measure install, first value, evidence validity, context, status, repeat use, and defect categories. Publish methodology and allow deletion.
