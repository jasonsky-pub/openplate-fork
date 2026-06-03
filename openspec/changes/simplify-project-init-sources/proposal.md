## Why

OpenPlate's `project init` entrypoints currently split template sources across name, URL, and folder modes, while the implementation already treats URL-like sources as the primary path. That makes the CLI harder to learn, leaves useful Git-compatible inputs like `file://` under-documented, and blocks a common repository layout where the template lives in a sub-folder of a larger repo.

## What Changes

- Extend URL-based template sources to support an optional `?path=<sub-folder>` query that selects a template root inside the cloned repository.
- Treat Git-compatible `file://` locations as supported URL inputs for `openplate project init`.
- Allow `openplate project init <url>` as the primary invocation form, while keeping `-r/--url` working for backward compatibility.
- **BREAKING** Remove the `-n/--name` and `-f/--folder` init source options so `project init` uses URL-driven sources only.
- Expand documentation to clearly describe supported URL forms, ref selection with `#branch-or-tag`, default-branch behavior, local `file://` usage, and repo-subfolder template selection.

## Capabilities

### New Capabilities
- `project-init-source-urls`: Defines the accepted `openplate project init` source URL formats, including positional URLs, `file://` URLs, and repository sub-folder selection with `?path=`.

### Modified Capabilities

## Impact

Affected areas include the `project init` CLI argument parsing, URL source parsing and validation, template source resolution after clone, and the command documentation in the repository docs and README.