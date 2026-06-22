## 1. CLI surface and tracked-template schema

- [x] 1.1 Add top-level `openplate info` and legacy `openplate project info` parser/dispatch support, including `--project-root`, `--offline`, and `--show-hidden` option handling.
- [x] 1.2 Extend tracked project-template serialization and deserialization with an optional provenance field that preserves backward compatibility for older `.openplate.project.yaml` files.

## 2. Provenance stamping

- [x] 2.1 Mark directly initialized templates as `requested`, promote previously inherited tracked templates to `requested`, and prevent later sibling discovery from demoting them.
- [x] 2.2 Mark newly auto-added sibling templates as `inherited` during recursive processing and add focused tests for requested/inherited persistence and promotion behavior.

## 3. Human-readable info command

- [x] 3.1 Implement resolved `info` inspection by loading the tracked project configuration, reusing prompt-document collection for live template metadata, and rendering human-readable template sections with parameter details.
- [x] 3.2 Implement `info --offline` as a project-file-only renderer that skips template inspection and prints only persisted tracked-template data.
- [x] 3.3 Enforce `--show-hidden` for resolved inspection only, render hidden parameters using the existing prompt-metadata behavior, and add focused CLI/output tests for resolved, offline, hidden, and template-inspection-failure cases.

## 4. Documentation and validation

- [x] 4.1 Update command documentation and README/help-facing examples to introduce `openplate info` and the `--offline` workflow.
- [x] 4.2 Run targeted automated coverage for CLI parsing, project-config provenance persistence, and resolved/offline info output behavior.