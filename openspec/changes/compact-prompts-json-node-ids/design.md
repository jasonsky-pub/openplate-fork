## Context

OpenPlate's current prompt JSON contract is still heavier than it needs to be because it uses raw runtime locator details as the import identity and interleaves answers with descriptive metadata. This change performs a full pre-release cutover to a cleaner contract centered on deterministic `node-id` values, a compact `answers` object, and an optional outer `info` object for verbose export.

This is a cross-cutting change. It affects CLI command and flag parsing for init-only prompt JSON workflows, prompt document serialization and parsing, prompt export collection, prompt input tracking, input logging, docs, tests, and reusable prompt artifacts. Because the feature has not been released yet, the implementation should replace the in-progress contract outright rather than adding compatibility layers.

## Goals / Non-Goals

**Goals:**
- Replace init import matching with deterministic `node-id` matching.
- Add `openplate project print-init-json <source>` as the compact prompt export command.
- Make `openplate project print-init-json <source> --verbose` emit the same nodes plus an outer `info` object with descriptive metadata.
- Keep one node shape for both compact and verbose init import so users can stream-edit exported JSON directly.
- Keep answer semantics simple: non-null is authoritative, `null` is unresolved, and an omitted answer key is also unresolved.
- Preserve current runtime rules for hidden parameters, existing/default fallback, full-tree print discovery, ignored unused nodes, and ignored unused answers.
- Make printed init JSON reusable across different `project init --dest-folder` values.
- Make prompt export fail fast when it cannot inspect a reached node well enough to produce complete prompt metadata.
- Allow short git-style `node-id` values while keeping round-trips correct when short-hash collisions occur.
- Remove the existing `project update` prompt JSON flags and update-command JSON execution path rather than preserving a second JSON surface.

**Non-Goals:**
- Add a compatibility layer for older pre-release prompt JSON drafts.
- Add a top-level plan identifier or wrapper object.
- Expand prompt JSON automation beyond `project init`.
- Change sibling selection, condition evaluation, or duplicate discovered sibling behavior.
- Introduce a separate answers-only document format in this change.

## Decisions

### 1. `node-id` is derived from canonical raw node identity plus init-relative path

Each template or CLI `dest_folder` input is normalized once at ingestion before the app uses it for template resolution, parameter resolution, prompt export, prompt identity hashing, prompt matching, or logging.

Normalization rules:
- trim leading and trailing whitespace
- replace `\` with `/`

For init prompt JSON behavior, OpenPlate distinguishes between:
- the normalized init output root from `project init --dest-folder`, which controls where files are written
- the init-relative destination folder for each reached node, which describes that node's location inside the initialized output tree before the init output root is prepended

OpenPlate computes init-relative destination folders as follows:
- top-level templates use the template's normalized `default_dest_folder`
- if `default_dest_folder` is unspecified or normalizes empty, the init-relative top-level destination folder is `.`
- sibling declarations require a non-empty normalized `dest_folder`; a missing or empty sibling `dest_folder` is invalid
- a sibling declaration's normalized `dest_folder` is appended beneath the caller node's init-relative destination folder to produce the called node's init-relative destination folder
- when init execution writes files, the normalized init output root is prepended to the init-relative destination folder to produce the real output path
- when prompt export or init prompt-input matching needs node identity, the normalized init output root is excluded; implementations that begin from the real output path must strip the normalized init output root before hashing or lookup

Each reached init prompt node computes a canonical identity string from:
- raw template reference
- init-relative normalized destination folder

OpenPlate will hash that canonical identity with SHA-256 and treat the full SHA-256 hash as the node's stable internal identity.

The serialized full `node-id` is the 64-character lowercase hexadecimal encoding of that SHA-256 hash. The preferred short `node-id` is the first 7 lowercase hexadecimal characters of the full hash.

Exported `node-id` values use a registry local to the export invocation:
- compute the full hash for the reached init node
- derive a preferred short ID from the leading hash characters
- if the same canonical init node already has an exported ID, reuse it
- if the preferred short ID is unused, assign it to this node
- if the preferred short ID is already assigned to a different canonical node, export the full hash for the new node

Export collection is keyed by canonical init identity. If the same canonical init node is encountered again during export, OpenPlate reuses and updates the existing emitted node instead of appending a second node to the JSON array.

Import resolution uses two passes against the actually reached init runtime nodes:
- first, resolve any supplied `node-id` that exactly matches a full hash and mark that runtime node as claimed
- second, resolve the remaining supplied `node-id` values as short prefixes against the remaining unclaimed init runtime node hashes

If a short `node-id` matches more than one remaining reached init node, import fails as ambiguous.

This keeps the common case compact while still making collisions deterministic and reversible, while allowing the same printed init JSON to be reused for different init roots.

Alternatives considered:
- Including the CLI init root in node identity. Rejected because it would force users to regenerate or rewrite prompt JSON whenever they change the init destination.
- Template-authored IDs. Rejected because they identify declarations rather than effective runtime nodes and do not solve converging-path identity.
- Random export-local IDs. Rejected because they are not stable enough for regeneration or debugging.
- Variable-length shortest-unique-prefix IDs for every node. Rejected because the chosen UX is first-come short IDs with full-hash fallback for later collisions.

### 2. The prompt document uses one node shape with `answers` and optional `info`

Both exported and imported prompt documents use a top-level JSON array of node objects. Any other top-level JSON shape is invalid.

Each node uses this shape:

```json
{
  "node-id": "123abcd",
  "answers": {
    "param1": null,
    "param2": "value"
  },
  "info": {
    "template": "...",
    "dest_folder": "...",
    "parameters": {
      "param1": {
        "default": "...",
        "existing": "...",
        "description": "...",
        "choices": ["..."],
        "hidden": false,
        "required": true
      }
    },
    "require_sibling_templates": [
      {
        "template": "...",
        "dest_folder": "...",
        "condition": "..."
      }
    ]
  }
}
```

Rules:
- `answers` is always the editable answer surface
- in exported documents, when parameter enumeration succeeds, `answers` includes one key for each discovered in-scope parameter and each key is initialized to `null`
- `answers` values are either strings or `null`
- any non-null answer value whose JSON type is not a string is invalid
- a missing key in `answers` means the same thing as `null`: unresolved, use runtime fallback if the parameter is reached
- `info` is optional and ignored on import
- when present, `info.template` carries the raw template reference string for that node rather than a rendered value
- when present, `info.dest_folder` carries the init-relative normalized destination folder used for that node's identity
- when present, `info.parameters` carries parameter metadata excluding answer values
- when present, `info.require_sibling_templates` carries caller-side sibling declaration metadata, including the raw declared template reference string, the called node's init-relative normalized destination folder, and any optional declaration condition

Compact export from `openplate project print-init-json <source>` includes `node-id` and `answers` only. Verbose export from `openplate project print-init-json <source> --verbose` includes the same node plus `info`.

If print discovery succeeds for a reached node and finds no in-scope parameters, that node still exports normally with `answers: {}`. If print discovery cannot inspect a reached node's parameter metadata or caller-side sibling declaration metadata well enough to produce a trustworthy prompt surface, prompt export fails instead of emitting partial node data.

Alternatives considered:
- Keeping per-parameter value wrappers. Rejected because they make the primary compact workflow more verbose without adding runtime value.
- Using a separate answers document. Rejected because it would create a second public contract when one node shape already supports both compact and verbose flows.

### 3. Dedicated init print and init import share the same core contract

`openplate project print-init-json <source>` is the read-only export command. By default it prints only:
- `node-id`
- `answers`

`openplate project print-init-json <source> --verbose` is the metadata-rich export mode. It prints:
- `node-id`
- `answers`
- `info`

Both forms remain read-only and continue to walk the full declared sibling tree without applying sibling `condition` filters.

`project init <source>` no longer exposes `--print-prompts-json`; print/export now exists only on `project print-init-json`, so use of the old flag fails by normal argument parsing because that option is no longer registered on `project init`.

`project print-init-json <source>` does not accept `--dest-folder`; that option remains specific to `project init`, and passing it to the print command fails by normal argument parsing because it is not registered for that verb.

`project init <source>` accepts a top-level JSON array of node objects from a file or stdin using this same node contract. `node-id` and `answers` are required. `info` is optional and ignored.

Prompt JSON automation in this contract applies only to `project init`.

As part of that narrowing, the existing `project update` prompt JSON flags are removed rather than merely undocumented. `project update` no longer accepts `--print-prompts-json`, `--prompts-json-file`, or `--prompts-json-stdin`, and its command path no longer loads prompt documents or prints them.

Conditions belong to caller-side verbose metadata, not to called nodes. When verbose export includes sibling declaration metadata, it does so on the caller through `info.require_sibling_templates` rather than as `info.condition` on the called node.

Because prompt export is intended to be a trustworthy planning artifact, any reached node that cannot be fully inspected causes export to fail rather than return a partial document.

Imported `node-id` values must use lowercase hexadecimal. A 64-character lowercase hexadecimal `node-id` is a full hash. A 7-character lowercase hexadecimal `node-id` is a short prefix. All other `node-id` formats are invalid.

Alternatives considered:
- Keeping print under `project init` behind a flag. Rejected because print/export is not init execution and deserves a dedicated command.
- Expanding prompt JSON automation beyond `project init` now. Rejected because this contract should stay focused on the init workflow it is actually standardizing.
- Adding separate import flags for compact and verbose documents. Rejected because both shapes are the same node contract with an optional metadata section.

### 4. Answer semantics stay simple and consistent

For a reached parameter in scope for the current init command:
- a non-null answer string is authoritative
- `""` is an explicit blank answer
- `null` means unresolved, use runtime fallback
- an omitted answer key also means unresolved, use runtime fallback

Hidden parameters continue to participate only when `--ask-hidden` is active.

Import validation changes:
- the imported document must be a top-level JSON array of node objects
- duplicate `node-id` entries in the input document are invalid
- nodes that omit `node-id` or `answers` are invalid
- `node-id` values that are not exactly 7 or 64 lowercase hexadecimal characters are invalid
- answer values whose JSON type is neither string nor `null` are invalid
- nodes not processed by the init run are ignored and logged by `node-id`
- answer keys that are not needed by a matched reached node are warned as unused

This keeps the matching contract explicit: `node-id` is the identity surface, `answers` are the answer surface, and `info` is descriptive only.

Alternatives considered:
- Treating omitted keys as invalid. Rejected because omission is the most natural compact spelling of "leave this unresolved".
- Using `info.template` and `info.dest_folder` as a fallback locator. Rejected because the cutover intentionally removes non-`node-id` matching.

### 5. `info` keeps debug context without reintroducing matching complexity

The `info` object preserves the helpful inspection context from the richer prompt view without making it part of the apply contract.

At minimum, `info` should contain:
- `template`
- `dest_folder`
- `parameters`

When available, `info` may also include caller-side sibling declaration metadata such as `require_sibling_templates`.

For a deduplicated canonical init node, canonical fields such as `template`, init-relative normalized `dest_folder`, and `parameters` come from the canonical node record. Conditions remain attached to the caller-side sibling declarations that introduced those edges rather than to the called node.

This keeps the stream-edit workflow intact: a user or model can export verbose, change only `answers`, and send the same structure back in. Import ignores `info`.

Alternatives considered:
- Removing metadata entirely. Rejected because it makes debugging and AI-assisted editing harder.

## Risks / Trade-offs

- [Short-hash collisions could make hand-authored IDs ambiguous] -> Prefer exact full-hash matches first during import and fail when a short hash is ambiguous.
- [Prompt export now fails for nodes that were previously partially printable] -> Treat that as the correct fail-fast behavior, surface the inspection error clearly, and update existing tests that codify partial-success export.
- [Prompt JSON automation applies only to init] -> Keep the contract focused on the workflow it is actually standardizing instead of inventing a second JSON surface without a concrete need.
- [Removing existing update JSON flags narrows currently documented behavior] -> Treat the init-only contract as authoritative and delete the old update JSON parser surface and docs instead of preserving it implicitly.
- [No top-level plan ID means short IDs are scoped only by the reached runtime node set] -> Use deterministic full hashes underneath and conservative short-ID allocation during export.
- [Full-tree print discovery still exports nodes that runtime execution may not reach] -> Preserve ignored-node logging on import and keep this behavior explicit in docs.

## Migration Plan

1. Add `node-id` generation and export-ID registry helpers based on canonical raw template-reference plus init-relative normalized destination-folder identity.
2. Replace the prompt document model so nodes carry `node-id`, `answers`, and optional `info`.
3. Add `openplate project print-init-json <source>` with `--verbose`, remove the old flag-driven print surface, and delete the existing `project update` prompt JSON flags and dispatch path.
4. Update init import parsing to require `node-id` and `answers`, remove all pre-cutover matching paths, preserve single-fetch source reuse, and implement the two-pass full-hash-then-short-hash resolution.
5. Update init prompt JSON docs, tests, and reusable trial artifacts to the new format, including removal of old update JSON examples.
6. Ship the cutover as a single replacement of the unreleased init prompt JSON contract.

## Open Questions

None at this time.