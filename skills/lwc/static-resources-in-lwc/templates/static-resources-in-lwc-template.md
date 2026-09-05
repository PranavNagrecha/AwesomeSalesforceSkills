# Static Resource Integration Worksheet

## Dependency Summary

- Library or asset name:
- Business reason it is needed:
- Native platform alternative considered:

## Packaging Plan

- Static resource name (letters/digits/underscore, starts with a letter, no trailing or doubled underscore):
- Version convention:
- Single file or zip:
- Build format (must be UMD or IIFE, never ESM):
- Internal path contract (every file path consumers concatenate):
- Archive size / current org total (ceilings: 5 MB per resource, 250 MB per org):
- Namespace prefix required (`ns__name`)? Yes / No

## Resource Metadata

- `contentType`:
- `cacheControl`: Private / Public
- Reason for that `cacheControl` value (Public = readable by unauthenticated internet traffic once cached):
- `description` records the archive layout and consumer list: Yes / No

## Loading Plan

- Uses `resourceUrl` directly: Yes / No
- Uses `loadScript` or `loadStyle`: Yes / No
- Loaded from `renderedCallback()` on first render: Yes / No
- One-time load guard (field name):
- Promise aggregation (`Promise.all`) and `catch` behaviour:
- Library writes DOM -> `lwc:dom="manual"` container: Yes / No / N/A
- Teardown in `disconnectedCallback()`:
- Failure handling:

## Security Notes

- Remote CDN avoided:
- Org runs Lightning Web Security or Lightning Locker:
- Library creates globals / uses `eval()` / scans the document:
- Trusted access required:
- Review owner:

## Sign-Off Checklist

- [ ] Packaging is versioned.
- [ ] Load path is supported.
- [ ] Repeated initialization is prevented.
- [ ] Consumers know the internal asset paths.
- [ ] `cacheControl` and `contentType` are set and justified.
- [ ] Jest test asserts the exact archive path and a single load across renders.
- [ ] `check_static_resources_in_lwc.py --manifest-dir <src>` reports no issues.
