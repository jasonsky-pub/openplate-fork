## Why

OpenPlate projects already persist enough state to update and verify templates, but humans still have to inspect `.openplate.project.yaml` directly to understand which templates are present, where they are rooted, and which parameter values are currently saved. That gets worse once sibling templates are introduced because the tracked template list no longer tells a reader which templates were explicitly requested versus added automatically.

## What Changes

- Add a human-readable `openplate info` command that reports tracked templates, destination folders, saved parameter values, and prompt metadata derived from the template sources when they can be inspected.
- Add an `--offline` option so `info` can display the project-file-only view without fetching template sources.
- Add a `--show-hidden` option for resolved `info` output so hidden prompt parameters can be included on demand.
- Track template provenance in the project configuration so `info` can distinguish directly requested templates from inherited sibling templates.
- Expose the new command as a top-level CLI command and keep a legacy `openplate project info` compatibility form consistent with the existing project command family.

## Capabilities

### New Capabilities
- `project-info-command`: Human-readable project inspection for tracked templates, prompt metadata, offline fallback, and template provenance.

### Modified Capabilities
- `top-level-init-update-commands`: Extend the primary top-level CLI workflow to include `info` and reflect that in help and legacy compatibility behavior.

## Impact

- CLI argument parsing and command dispatch in the top-level OpenPlate entry point.
- New command implementation for human-readable project inspection.
- Project configuration serialization for template provenance metadata.
- Reuse of template-inspection/prompt-metadata plumbing for resolved `info` output.
- Command documentation and focused tests covering online and offline `info` behavior.