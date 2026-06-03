## 1. CLI source contract

- [x] 1.1 Update `project init` argument parsing to accept a positional URL source while keeping `-r` / `--url` as a backward-compatible alias.
- [x] 1.2 Remove `-n` / `--name` and `-f` / `--folder`, and add validation and migration errors for conflicting URL inputs and missing refs.

## 2. URL parsing and source resolution

- [x] 2.1 Add a URL source parser for `<repo-location>[?path=<relative-template-subdir>][#<ref>]` that extracts repo location, optional template path, and optional ref.
- [x] 2.2 Update the URL-backed template source flow to validate `?path=`, clone the repository, and expose the selected sub-folder as the template root.
- [x] 2.3 Ensure Git-compatible `file://` URLs follow the same URL-backed source path and preserve repository-root behavior when no `?path=` is supplied.

## 3. Verification and documentation

- [x] 3.1 Add or update focused validation for positional URL init, `-r` / `--url` compatibility, `file://` URLs, `?path=` template selection, invalid template paths, and removed source options.
- [x] 3.2 Update README and command documentation to describe supported URL forms, `#<ref>` requirements, `--allow-default-branch`, `?path=` usage, and migration from removed options.