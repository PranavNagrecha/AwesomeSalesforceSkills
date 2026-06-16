# templates/ — CHANGELOG

Notable changes to the shared, cross-skill canonical templates (see
[`README.md`](./README.md)). Templates are hand-written scaffolds that consuming
projects copy and rename, so "breaking" here means a consumer would have to
change how they use a template — not merely re-copy it.

## 2026-06-15

### Changed

- Standardized `apiVersion` across **all 16** template `-meta.xml` files to
  **`67.0` (Summer '26)**, the current GA API version. Previously 14 files were
  at `62.0` (Winter '25) and 2 at `64.0` (Summer '25), while `README.md` claimed
  every template targeted `64.0` and labeled that "Spring '26" — incorrect on
  both the version number (`64.0` is Summer '25; Spring '26 is `66.0`) and the
  resulting drift. Consumers on an older release should lower `apiVersion` on
  copy, as the README's "Versioning" note describes. Non-breaking: the API
  surface used by these scaffolds is stable across these versions.
