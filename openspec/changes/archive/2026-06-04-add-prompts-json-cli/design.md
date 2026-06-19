## Context

OpenPlate already has the core mechanics needed for machine-driven prompting: parameter resolution can fail instead of prompting, and sibling templates are keyed in project state by template source plus destination folder. What is missing is a structured CLI contract to export pending prompt state, let automation edit that state, and feed it back into `project init` and `project update` without scraping terminal output.

This change needs to cross the CLI parser, prompt resolver, and recursive template walk. It also needs to fit the current processing model instead of introducing a parallel planner that fully evaluates conditions, config files, or future sibling selection ahead of time.

## Goals / Non-Goals

**Goals:**
- Add `--print-prompts-json` for `project init` and `project update` to emit the declared prompt document as JSON.
- Make `--print-prompts-json` a read-only planning/export mode that never writes files or updates project state.
- Add `--prompts-json-file` and `--prompts-json-stdin` for `project init` and `project update` to consume prompt answers from JSON and fail instead of prompting.
- Use one hierarchical JSON document for both export and import so automation can round-trip the output by editing `value` fields.
- Scope prompt answers to a template instance using the template reference and destination folder, with parameters nested under that template node.
- During `--print-prompts-json`, walk the full declared template tree without applying sibling `condition` filters.
- Include template `condition` metadata in printed JSON when present, but ignore it during import.
- Scope hidden parameters to `--ask-hidden` on both prompt export and prompt import.
- Distinguish incomplete parameter discovery from truly parameterless templates in the printed JSON document.
- Reuse fetched template sources within a single command invocation so validation/discovery does not clone the same template source twice.
- Preserve current console-style error reporting while adding always-on warnings for extra supplied parameters and always-on ignored-template log messages.

**Non-Goals:**
- Add a separate `--non-interactive` flag.
- Add a top-level JSON wrapper, schema version field, or alternate machine-readable error format.
- Fully precompute condition outcomes that depend on dynamic config files or later template state.
- Change the current runtime behavior where a duplicate sibling template declaration is ignored after the first matching template instance is processed.

## Decisions

### 1. JSON input flags imply no prompting

`--prompts-json-file` and `--prompts-json-stdin` will act as the machine-driven mode for `project init` and `project update`. When either flag is used, OpenPlate will not call interactive prompt paths. Any unresolved parameter or template-command confirmation that would have prompted today will instead fail using the existing error flow.

This keeps the public surface smaller than adding both JSON-input flags and a separate `--non-interactive` switch.

Alternatives considered:
- Add `--non-interactive` anyway. Rejected because the JSON-input flags already imply the same policy and would duplicate configuration.
- Allow JSON-input modes to fall back to interactive prompts. Rejected because stdin cannot safely serve as both JSON input and prompt input, and fallback would make automation behavior less predictable.

### 2. Print mode does full-tree discovery, execution modes do not

`--print-prompts-json` will output a JSON array. Each entry represents one declared template instance and groups its parameters beneath it. The export is a read-only planning step: it must not write files, update `.openplate.project.yaml`, or mutate the working tree.

`--print-prompts-json` is the only mode that performs full-tree discovery beyond the normal execution path. For that print-only discovery walk, OpenPlate will traverse declared sibling templates without using `condition` values to prune the tree.

Normal init, update, and JSON-input execution will keep the existing condition-aware processing path. They will not perform a separate full-tree validation walk before doing real work.

The printed JSON therefore reflects the declared template tree rather than the exact set of templates that a normal execution run will process.

Each template node will include:
- `template`: the raw template reference string for that template instance
- `dest_folder`: the raw destination-folder string for that template instance
- `condition`: the raw condition string when the template declaration has one
- `parameters`: either an object keyed by parameter name or `null` when print-mode discovery could not enumerate parameter metadata for that node

When `parameters` is an object, each parameter entry will include:
- `value`
- `default`
- `existing`
- `description`
- `choices`
- `hidden`
- `required`

`value` semantics are explicit:
- `null` means no answer has been supplied for this parameter, so normal runtime fallback still applies if that parameter is reached
- `""` means an explicit blank string answer
- any other non-null `value` is the authoritative supplied answer for that parameter when the parameter is in scope for the command
- omission of the `value` field in an imported parameter entry is invalid

`required` is derived from current OpenPlate prompt behavior: a parameter is required when it has no resolved existing value, no resolved default value, and therefore would fail if JSON-input mode reaches it without a supplied value.

Hidden parameters are part of the prompt document only when `--ask-hidden` is active for that command. Without `--ask-hidden`, hidden parameters are omitted from `--print-prompts-json` output and ignored during JSON import.

If print-mode discovery can enumerate a template declaration but cannot load that template's config closely enough to discover parameter metadata during export, OpenPlate will still emit the template node using the preserved raw `template`, `dest_folder`, and optional `condition`, and it will emit `parameters` as `null`.

Import will accept the same structure. During import, OpenPlate will use only the template identity fields and each parameter's `value`. A template node with `parameters: null` is treated as having no supplied parameter values. Other fields are treated as informational export metadata and ignored for import semantics, including `condition`, `default`, `existing`, `description`, `choices`, `hidden`, and `required`.

For parameters that are in scope for the command, a non-null JSON `value` overrides runtime fallback even when the template already has an existing value or interactive mode would not have re-prompted that parameter. `--ask-again` continues to control interactive re-prompting, but it does not block a non-null supplied JSON answer.

Alternatives considered:
- Use a flat list of parameter rows. Rejected because it duplicates template identity on every entry and makes sibling targeting harder to read.
- Add a root object with schema metadata. Rejected because the user wants the JSON shape to start directly at the template list.

### 3. Template identity stays raw and is keyed by template plus destination folder

Printed JSON will use the templated strings rather than rendered values for sibling template references and destination folders. This keeps the contract aligned with template configuration as written and avoids making the export format depend on partial rendering state.

Because the current walk mutates sibling declarations as it renders them, the implementation must preserve the original raw template reference, raw destination-folder string, and raw condition before any rendering or in-place mutation occurs. JSON export and JSON-input matching will use those preserved raw values.

For import validation, template-instance uniqueness is the pair `(template, dest_folder)`. Duplicate entries with the same pair in supplied JSON will be rejected before processing begins.

If print-mode discovery encounters the same raw `(template, dest_folder)` pair more than once, export will keep only the first discovered node so the emitted JSON remains valid input for later import.

Alternatives considered:
- Print rendered template identifiers. Rejected because the rendered value may depend on partial state and is harder to keep stable during prompt editing.
- Add a synthetic template-instance identifier. Rejected because the project already has a natural identity boundary and a new identifier would need separate lifecycle rules.

### 4. Validation is incremental, with duplicate errors, ignored unused templates, and warnings for extra parameters

OpenPlate will validate supplied JSON against the actual template instances that are processed during init or update.

- If supplied JSON contains a duplicate template node, OpenPlate errors before processing.
- If supplied JSON contains a template node that is never processed, OpenPlate ignores that node and prints an always-on log message identifying the raw `template` and `dest_folder` that were ignored.
- If supplied JSON contains parameter values that are not needed by the matched template instance, including hidden parameters supplied without `--ask-hidden`, OpenPlate collects warnings and prints them at the end even when debug logging is disabled.

This approach avoids a larger refactor to fully predict selection outcomes up front, especially for conditions that can depend on config files or later template state.

The full declared tree exported by `--print-prompts-json` is broader than the set of templates that may actually run. During execution, OpenPlate will still validate supplied JSON against the templates that are actually processed and will log ignored-template messages for template nodes that remain unused by the end of the run.

Alternatives considered:
- Fully evaluate template selection before processing. Rejected because it would require broader planning/reflection support than the current pipeline provides.
- Silently ignore extra templates or parameters. Rejected because it would hide stale automation inputs and make prompt documents harder to trust.

### 5. Duplicate discovered siblings retain current first-match behavior

If the existing template walk encounters the same sibling template instance more than once, OpenPlate will continue to use the first discovered instance and ignore later duplicates. The new JSON features will follow that same runtime behavior rather than changing sibling-resolution semantics in this change. Print-mode export will mirror that rule by collapsing duplicate discovered nodes to the first raw `(template, dest_folder)` pair.

Alternatives considered:
- Fail runtime processing when duplicate sibling declarations are discovered. Rejected because it changes existing behavior and is broader than the JSON prompt contract.

### 6. One command invocation must not fetch the same source twice for validation and execution

Within a single command invocation, OpenPlate must reuse fetched or cloned template sources between prompt discovery, prompt validation, and actual processing. JSON-input execution must validate against the same fetched sources that the command will use for real init or update work, rather than doing a pre-validation fetch and then fetching the same repo again for execution.

This keeps JSON-driven runs from paying the cost of a redundant clone/fetch and avoids introducing extra source-state drift within one command.

Alternatives considered:
- Add a separate preflight validation pass that clones sources before the real run. Rejected because it duplicates work and creates the exact double-pull behavior the user wants to avoid.

## Risks / Trade-offs

- [Print-mode full-tree discovery may include templates not processed later] -> Keep full-tree discovery limited to `--print-prompts-json` and log ignored-template messages rather than failing when exported-but-unused nodes are returned.
- [Raw template identity may be less convenient for humans than rendered values] -> Keep the JSON stable for round-tripping and include descriptions/defaults so the editable fields stay obvious.
- [Export may encounter declarations whose parameter metadata cannot be loaded during print discovery] -> Emit those nodes with preserved raw identity and `parameters: null` so automation can distinguish incomplete discovery from truly parameterless templates.
- [Warnings for extra parameters could be noisy in stale automation documents] -> Limit warnings to actually supplied but unused parameter values and keep the text actionable.
- [JSON-input modes affect both parameter prompts and template-command confirmations] -> Document that these flags imply no prompting of any kind, not only parameter entry.

## Migration Plan

- Add the new flags without changing existing interactive init or update flows when the JSON flags are not used.
- Document the read-only export/import JSON workflow for automation and AI-assisted runs, including that full-tree discovery is print-only, runtime validation uses actual processed templates, and template sources are reused within a command.
- Keep existing human-readable error messages, with new validation and warning text layered onto the current failure paths.
- Document hidden-parameter scope, `null` versus non-null `value` semantics, and metadata-only fields directly in the command reference so automation can author prompt JSON without inferring behavior.

## Open Questions

None at this time.