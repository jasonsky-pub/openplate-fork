## ADDED Requirements

### Requirement: OpenPlate normalizes destination-folder values consistently for init prompt JSON
OpenPlate SHALL normalize each template or CLI `dest_folder` input before using it for init template resolution, parameter resolution, prompt node identity, prompt export metadata, or prompt-related matching and logging.

Normalization SHALL:
- trim leading and trailing whitespace
- replace `\` with `/`

For init prompt JSON behavior, OpenPlate SHALL distinguish between the normalized init output root supplied to `project init --dest-folder` and each node's init-relative normalized `dest_folder` inside the initialized tree.

After normalization, OpenPlate SHALL resolve init-relative destination folders for prompt-related behavior as follows:
- a top-level template SHALL use the template's normalized `default_dest_folder`
- if `default_dest_folder` is unspecified or normalizes empty, the init-relative top-level destination folder SHALL be `.`
- a sibling declaration SHALL provide a non-empty normalized `dest_folder`; a missing or empty sibling `dest_folder` SHALL be rejected
- a sibling declaration's normalized `dest_folder` SHALL be appended beneath the caller node's init-relative destination folder to produce the called node's init-relative destination folder

OpenPlate SHALL prepend the normalized init output root only when materializing real output paths during `project init`. The init output root SHALL NOT participate in printed `node-id` values, printed `info.dest_folder`, or init prompt-document matching.

During init prompt-document matching, OpenPlate SHALL resolve node identity using the same init-relative normalized `dest_folder` used for export. If the implementation begins from a real output path, it SHALL strip the normalized init output root before hashing or matching.

#### Scenario: Normalize a destination folder before init prompt processing
- **WHEN** a template declares `dest_folder` with surrounding whitespace or `\` separators
- **THEN** OpenPlate normalizes that value before template resolution and parameter resolution continue
- **AND** the normalized value uses `/` separators with surrounding whitespace removed

#### Scenario: Missing top-level destination folder falls back to init root
- **WHEN** a top-level template has no non-empty `default_dest_folder`
- **THEN** OpenPlate uses `.` as the init-relative destination folder for prompt identity

#### Scenario: Sibling destination folder is required
- **WHEN** a sibling declaration omits `dest_folder` or its normalized value is empty
- **THEN** OpenPlate rejects that sibling declaration

#### Scenario: Sibling destination folder composes beneath the caller
- **WHEN** a reached caller node has init-relative destination folder `services/api`
- **AND** that caller declares a sibling with normalized `dest_folder` `workers/job`
- **THEN** the called node's init-relative destination folder is `services/api/workers/job`

#### Scenario: Printed init JSON is reusable across init roots
- **WHEN** a user prints init prompt JSON and later runs `project init` with a different normalized `--dest-folder`
- **THEN** the printed `node-id` values still match the reached init nodes
- **AND** OpenPlate derives that match from init-relative destination folders rather than the invocation root

### Requirement: OpenPlate removes legacy prompt JSON flags from non-print verbs
OpenPlate SHALL NOT expose `--print-prompts-json`, `--prompts-json-file`, or `--prompts-json-stdin` on `project update`.

OpenPlate SHALL remove any `project update` execution path that prints prompt JSON or consumes prompt JSON input.

OpenPlate SHALL NOT expose `--print-prompts-json` on `project init`; init prompt export SHALL be available only through `project print-init-json`.

#### Scenario: Update no longer accepts print-prompts-json
- **WHEN** a user runs `openplate project update --print-prompts-json`
- **THEN** OpenPlate rejects the command because `--print-prompts-json` is not a valid `project update` argument

#### Scenario: Update no longer accepts prompts-json-file
- **WHEN** a user runs `openplate project update --prompts-json-file prompts.json`
- **THEN** OpenPlate rejects the command because `--prompts-json-file` is not a valid `project update` argument

#### Scenario: Update no longer accepts prompts-json-stdin
- **WHEN** a user runs `openplate project update --prompts-json-stdin`
- **THEN** OpenPlate rejects the command because `--prompts-json-stdin` is not a valid `project update` argument

#### Scenario: Init no longer accepts print-prompts-json
- **WHEN** a user runs `openplate project init <source> --print-prompts-json`
- **THEN** OpenPlate rejects the command because `--print-prompts-json` is not a valid `project init` argument

## MODIFIED Requirements

### Requirement: OpenPlate prints prompt state as template-grouped JSON
This requirement title is retained to modify the existing capability in place, but the printed document defined by this change is node-based: each exported entry is a prompt node identified by `node-id`, not a template-keyed wrapper structure.

OpenPlate SHALL support `openplate project print-init-json <source>` as a read-only planning/export command that prints a JSON array of init prompt nodes instead of interactive prompt text.

`openplate project print-init-json <source> --verbose` SHALL print the same JSON node set with additional descriptive metadata.

The print-init command SHALL be read-only. It MUST NOT write files, update project configuration, or otherwise mutate workspace state.

The print-init command SHALL walk the full declared template tree without applying sibling `condition` filters. The printed JSON SHALL include the full declared template tree that can be discovered from the template configuration, including conditional sibling declarations. This export MAY include nodes that later execution does not process.

Each printed node SHALL include `node-id` and `answers`.

When print discovery can enumerate a node's in-scope parameters, exported `answers` SHALL include one key for each discovered in-scope parameter and each such key SHALL be initialized to `null`.

OpenPlate SHALL emit at most one printed node for each canonical raw template-reference plus init-relative normalized destination-folder identity reached by the export walk.

Each emitted `node-id` SHALL use lowercase hexadecimal. A full-hash `node-id` SHALL be the 64-character lowercase hexadecimal SHA-256 encoding of the canonical node identity. The preferred short `node-id` SHALL be the first 7 lowercase hexadecimal characters of that full hash.

`openplate project print-init-json <source>` SHALL emit the compact form and SHALL omit `info`.

`openplate project print-init-json <source> --verbose` SHALL emit the verbose form and SHALL include `info`. When present, `info` SHALL carry descriptive node metadata such as `template`, init-relative `dest_folder`, and `parameters` metadata excluding answer values.

When present, `info.template` SHALL use the raw template reference string for that node rather than a rendered value.

When a node declares sibling templates, verbose `info` MAY also include caller-side sibling declaration metadata such as `require_sibling_templates`. If present, those entries SHALL describe the caller's outgoing declarations, including the raw declared target template reference string, the called node's init-relative normalized destination folder, and any declaration condition.

Called nodes SHALL NOT carry caller-side declaration conditions as `info.condition`.

If print export cannot fully inspect a reached node's parameters or caller-side sibling declaration metadata, OpenPlate MUST fail the export instead of emitting partial node data.

Hidden parameters SHALL be included in exported `answers` and exported `info.parameters` only when `--ask-hidden` is active for that command.

#### Scenario: Print compact init prompts JSON
- **WHEN** a user runs `openplate project print-init-json <source>`
- **THEN** OpenPlate prints a JSON array of prompt nodes
- **AND** each node includes `node-id` and `answers`
- **AND** each node omits `info`

#### Scenario: Print verbose init prompts JSON
- **WHEN** a user runs `openplate project print-init-json <source> --verbose`
- **THEN** OpenPlate prints a JSON array of prompt nodes
- **AND** each node includes `node-id`, `answers`, and `info`

#### Scenario: Print init prompts JSON without mutating the workspace
- **WHEN** a user runs either form of `project print-init-json`
- **THEN** OpenPlate does not write project files or template output files
- **AND** OpenPlate does not update `.openplate.project.yaml` as part of printing the JSON document

#### Scenario: Print-init-json rejects dest-folder
- **WHEN** a user runs `openplate project print-init-json <source> --dest-folder other`
- **THEN** OpenPlate rejects the command because `--dest-folder` is not a valid `project print-init-json` argument

#### Scenario: Include conditional sibling declarations in init print export
- **WHEN** a template declares a sibling template behind a condition
- **THEN** either print form includes that sibling node in the printed JSON tree
- **AND** print export does not use that condition to prune the export tree

#### Scenario: Reached canonical init node is emitted once
- **WHEN** the export walk encounters the same canonical template-reference plus init-relative normalized destination-folder identity more than once
- **THEN** OpenPlate emits one node for that canonical identity
- **AND** OpenPlate reuses the same emitted `node-id` for that node

#### Scenario: Enumerated parameters are seeded in answers
- **WHEN** print discovery can enumerate the in-scope parameters for a reached node
- **THEN** exported `answers` includes one key for each discovered in-scope parameter
- **AND** each exported answer value is `null`

#### Scenario: Parameterless reached node emits empty answers
- **WHEN** print discovery succeeds for a reached node and finds no in-scope parameters
- **THEN** exported `answers` is `{}`

#### Scenario: Verbose conditions are emitted on the caller
- **WHEN** a node declares a conditional sibling template
- **THEN** verbose export may include that declaration in the caller node's `info.require_sibling_templates`
- **AND** the called node does not emit `info.condition`

#### Scenario: Hidden parameters are omitted from export without ask-hidden
- **WHEN** a user runs a print form without `--ask-hidden`
- **THEN** OpenPlate omits hidden parameters from exported `answers`
- **AND** OpenPlate omits hidden parameter metadata from verbose `info.parameters`

#### Scenario: Parameter discovery failure fails export
- **WHEN** print export reaches a node but cannot enumerate that node's prompt parameters
- **THEN** OpenPlate fails the export command
- **AND** OpenPlate does not emit a partial prompt JSON document

#### Scenario: Caller-side sibling discovery failure fails export
- **WHEN** print export reaches a node but cannot inspect its caller-side sibling declaration metadata well enough to build verbose output
- **THEN** OpenPlate fails the export command
- **AND** OpenPlate does not emit a partial prompt JSON document

### Requirement: OpenPlate accepts prompt answers from JSON without prompting
OpenPlate SHALL support `--prompts-json-file <path>` and `--prompts-json-stdin` for `project init`. When either flag is used, OpenPlate MUST consume prompt answers from the provided JSON document and MUST NOT fall back to interactive prompting.

The supplied prompt document MUST be a top-level JSON array of node objects. Any other top-level JSON shape MUST be rejected.

`--prompts-json-file` and `--prompts-json-stdin` SHALL use the normal init execution walk. They MUST NOT switch to the full-tree, condition-ignoring discovery behavior reserved for `project print-init-json`.

Imported nodes MUST provide `node-id` and `answers`. Imported `info` MAY be present and MUST be ignored for import matching and resolution.

Documents that do not use this node shape MUST be rejected.

Imported `node-id` values MUST use lowercase hexadecimal. A 64-character lowercase hexadecimal `node-id` MUST be treated as a full hash. A 7-character lowercase hexadecimal `node-id` MUST be treated as a short prefix. All other `node-id` formats MUST be rejected.

Within `answers`, each value MUST be either a string or `null`. Any other JSON value type MUST be rejected.

Within `answers`, a non-null answer value MUST be treated as the authoritative supplied answer for a reached in-scope parameter. `null` and an omitted answer key MUST both mean unresolved so normal runtime fallback applies if that parameter is reached.

Hidden parameters MUST be in scope only when `--ask-hidden` is active for that command. Hidden answers supplied without `--ask-hidden` MUST be ignored as unused supplied answers.

If required values remain unresolved after applying supplied JSON, OpenPlate MUST fail instead of prompting. OpenPlate MAY fail on the first unresolved prompt rather than aggregating all missing values.

If template-command confirmation would have prompted during the run and the command has not otherwise been authorized, OpenPlate MUST fail instead of prompting.

Within a single command invocation, OpenPlate MUST NOT fetch or clone the same template source once for prompt validation and then again for actual processing. JSON-input execution MUST reuse fetched template sources for validation and execution.

#### Scenario: Supply answers from a compact file
- **WHEN** a user runs `openplate project init <source> --prompts-json-file prompts.json`
- **AND** `prompts.json` contains nodes with `node-id` and `answers`
- **THEN** OpenPlate reads prompt answers from `prompts.json`
- **AND** OpenPlate does not prompt for missing values during that run

#### Scenario: Non-array prompt document is rejected
- **WHEN** a supplied prompt document is a JSON object, string, number, or other non-array top-level value
- **THEN** OpenPlate rejects the document before template processing begins

#### Scenario: Supply answers from a verbose file
- **WHEN** a user runs `openplate project init <source> --prompts-json-file prompts.json`
- **AND** `prompts.json` contains nodes with `node-id`, `answers`, and `info`
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate ignores `info` for matching and answer resolution

#### Scenario: Validation and execution reuse the same source fetch
- **WHEN** a user runs `openplate project init <source> --prompts-json-file prompts.json`
- **THEN** OpenPlate validates prompt input and processes that command without fetching or cloning the same template source twice

#### Scenario: Invalid answer value type is rejected
- **WHEN** a supplied JSON document sets an `answers` value to a non-string, non-null JSON value
- **THEN** OpenPlate rejects the document before template processing begins

#### Scenario: Null answer uses runtime fallback
- **WHEN** an imported node sets `answers.param1` to `null`
- **THEN** OpenPlate does not answer that parameter from JSON
- **AND** OpenPlate uses the normal runtime fallback for that parameter if it is reached

#### Scenario: Missing answer key uses runtime fallback
- **WHEN** an imported node omits `param1` from `answers`
- **THEN** OpenPlate does not treat that parameter as answered by the prompt document
- **AND** OpenPlate uses the normal runtime fallback for that parameter if it is reached

#### Scenario: Non-null answer overrides existing fallback
- **WHEN** an imported node sets `answers.param1` to a non-null string for a reached in-scope parameter that already has an existing runtime value
- **THEN** OpenPlate uses the supplied JSON answer for that parameter

#### Scenario: Missing required value in JSON mode
- **WHEN** JSON-input mode is active and a required parameter still has no resolved value after considering supplied answers and runtime fallback
- **THEN** OpenPlate fails
- **AND** OpenPlate does not ask the user for that value interactively

### Requirement: OpenPlate validates supplied prompt documents by template instance
OpenPlate SHALL match supplied prompt nodes using `node-id` only. OpenPlate MUST NOT use `template`, `dest_folder`, or other metadata fields for import matching.

OpenPlate SHALL derive a full node hash from the canonical raw template-reference plus init-relative normalized destination-folder identity used by init prompt export.

During export, OpenPlate SHALL emit at most one node for each canonical init node identity, SHALL assign a short `node-id` when the preferred short hash is not already taken, SHALL reuse the same emitted node and exported `node-id` when the same canonical init node is reached again, and SHALL export the full node hash when the preferred short hash is already taken by a different canonical node.

During import, OpenPlate MUST resolve node identifiers in two passes:
- first, exact full-hash matches
- then, unique short-hash matches against remaining unclaimed reached nodes

During import, OpenPlate MUST reject a supplied JSON document that contains duplicate `node-id` entries.

If an imported node does not correspond to a node that is actually processed by the init run, OpenPlate MUST ignore that supplied node and MUST print a log message identifying the unused `node-id`. If supplied answers are present for a matched node but are not needed during processing, OpenPlate MUST print warnings for those unused supplied answers even when debug logging is disabled.

#### Scenario: Round-trip compact prompt document
- **WHEN** a user edits only `answers` values in a document previously printed by `project print-init-json`
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate matches nodes by `node-id`

#### Scenario: Round-trip verbose prompt document
- **WHEN** a user edits only `answers` values in a document previously printed by `project print-init-json --verbose`
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate ignores unchanged `info` metadata during import

#### Scenario: Full hash takes precedence over colliding short hash
- **WHEN** one imported node uses a full SHA-256 `node-id`
- **AND** another imported node uses a short `node-id` prefix that would otherwise collide with that full-hash node
- **THEN** OpenPlate resolves the full SHA-256 `node-id` first
- **AND** OpenPlate resolves the short `node-id` only against the remaining unclaimed reached nodes

#### Scenario: Duplicate node identifiers are invalid
- **WHEN** a supplied JSON document contains two nodes with the same `node-id`
- **THEN** OpenPlate fails validation before template processing begins

#### Scenario: Invalid node-id format is rejected
- **WHEN** a supplied JSON document includes a `node-id` that is not exactly 7 or 64 lowercase hexadecimal characters
- **THEN** OpenPlate fails validation before template processing begins

#### Scenario: Unused imported node is ignored
- **WHEN** a supplied JSON document includes a node whose `node-id` is never processed by the run
- **THEN** OpenPlate ignores that node
- **AND** OpenPlate prints a log message identifying the unused `node-id`

#### Scenario: Unused supplied answer is warned
- **WHEN** a supplied JSON document includes an answer for a matched reached node and that answer is not needed during processing
- **THEN** OpenPlate completes normal processing behavior for the node
- **AND** OpenPlate prints a warning about the unused supplied answer