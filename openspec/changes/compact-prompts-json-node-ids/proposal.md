## Why

The current init prompt JSON flow is now correct and predictable, but it is still more cumbersome than it needs to be because import identity depends on raw `template` plus `dest_folder` and the exported document mixes editable answers with descriptive metadata. This change makes the machine-facing init flow compact, stable, and reusable across different init destinations by switching to deterministic `node-id` matching and by separating answers from optional parameter metadata.

## What Changes

- Replace init prompt JSON node matching with deterministic `node-id` values derived from the canonical raw template-reference and the init-relative normalized destination-folder identity inside the initialized tree, excluding any invocation root passed to `project init --dest-folder`.
- Normalize template `dest_folder` values at ingestion by trimming whitespace and converting path separators to `/`, compute each reached node's init-relative destination folder inside the initialized tree, and append the real `project init --dest-folder` root only when materializing output paths; sibling declarations still require a non-empty `dest_folder` after normalization.
- Emit at most one prompt node for each canonical template-reference plus init-relative normalized destination-folder identity reached during init export.
- Perform a full prompt JSON contract cutover before release so `node-id` is the only supported import identity.
- Serialize full `node-id` values as 64-character lowercase hexadecimal SHA-256 strings and prefer the first 7 lowercase hexadecimal characters as the compact exported form.
- Export short `node-id` values when they are collision-free within the reached prompt tree, and fall back to the full hash when the short form is already taken by another node.
- Change the prompt JSON shape so node answers live under an `answers` object keyed by parameter name, with exported discovered answer keys initialized to `null`, with values restricted to strings or `null`, and with `null` or an omitted key both meaning unresolved so runtime fallback still applies.
- Add an optional outer `info` object for verbose export. `info` carries descriptive node metadata such as `template`, `dest_folder`, per-parameter metadata excluding values, and caller-side sibling declaration metadata.
- Add `openplate project print-init-json <source>` as the read-only prompt export command, using compact output by default and `--verbose` for the metadata-rich export.
- Accept both compact and verbose documents on import when supplied to `project init` as a top-level JSON array of node objects with valid `node-id` and `answers` fields.
- Emit sibling-declaration conditions on the caller's verbose metadata rather than on the called node, so converging called nodes do not need merged condition metadata.
- Fail prompt export when a reached node cannot be fully inspected for prompt metadata, instead of emitting partial node data.
- Scope prompt JSON export and import to `project init` only.
- Remove the existing update JSON CLI surface instead of carrying it forward: `openplate project update --print-prompts-json`, `--prompts-json-file`, and `--prompts-json-stdin` are deleted by this change.
- Document the compact `node-id` plus `answers` flow as the primary init workflow and the verbose `info` shape as an optional stream-editing path.

## Capabilities

### New Capabilities

### Modified Capabilities
- `project-prompts-json`: Change init prompt JSON node identity to `node-id`, replace per-parameter `value` wrappers with `answers`, add optional outer `info` metadata, use a dedicated init print command, and scope prompt JSON print/import to init only.

## Impact

- Affected code includes template ingestion and init-relative `dest_folder` resolution, prompt document serialization/deserialization, prompt input tracking, prompt export collection, CLI command parsing for `project print-init-json`, removal of update-command prompt JSON flags and dispatch paths, init prompt resolution, and prompt input logging.
- User-facing command documentation for prompt JSON export/import will describe only the new init workflow: `openplate project print-init-json <source>` for export and `project init` JSON input for execution, with `--verbose` documented as the optional metadata-rich variant.
- Existing prompt JSON tests will need to be updated for the new node shape and new import/export matching rules.
- Existing tests that codify partial prompt-export success on discovery failures will need to be replaced with fail-fast export behavior.
- Prompt JSON automation is defined only for `project init`.
- Existing docs and examples for `project init --print-prompts-json`, `project update --print-prompts-json`, `project update --prompts-json-file`, and `project update --prompts-json-stdin` will need to be removed.
- Trial-run prompt artifacts and any hand-authored prompt JSON documents will need regeneration to the new `node-id`-based format.