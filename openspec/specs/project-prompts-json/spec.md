# project-prompts-json Specification

## Purpose
TBD - normalized from a previously archived delta-only spec document.
## Requirements
### Requirement: OpenPlate normalizes destination-folder values consistently for init prompt JSON
OpenPlate SHALL normalize each template or CLI `dest_folder` input before using it for init template resolution, parameter resolution, prompt node identity, prompt export metadata, or prompt-related matching and logging.

Normalization SHALL:
- trim leading and trailing whitespace
- replace `\` with `/`

`openplate project print-init-json` SHALL accept the same `--dest-folder` option that `project init` accepts.

For init prompt JSON behavior, OpenPlate SHALL bind prompt export and prompt import to the same normalized init output root that init execution will use.

After normalization, OpenPlate SHALL resolve project-relative destination folders for init prompt-related behavior as follows:
- a top-level init node SHALL use the normalized init output root
- if `--dest-folder` is omitted, the normalized init output root SHALL follow the same runtime-context rules that `project init` uses when `--dest-folder` is omitted
- a sibling declaration SHALL provide a non-empty normalized `dest_folder`; a missing or empty sibling `dest_folder` SHALL be rejected
- a sibling declaration's normalized `dest_folder` SHALL be appended beneath the caller node's project-relative destination folder to produce the called node's project-relative destination folder

Printed `node-id` values, printed `info.dest_folder` values, prompt-related metadata such as rendered defaults, and init prompt-document matching SHALL all use those same normalized project-relative destination folders derived from the chosen init output root.

During init prompt-document matching, OpenPlate SHALL resolve node identity using the same normalized project-relative destination folders used for export. If a user changes the normalized init output root between `project print-init-json` and `project init`, the exported node identifiers SHALL no longer match the reached init nodes.

#### Scenario: Normalize a destination folder before init prompt processing
- **WHEN** a template declares `dest_folder` with surrounding whitespace or `\` separators
- **THEN** OpenPlate normalizes that value before template resolution and parameter resolution continue
- **AND** the normalized value uses `/` separators with surrounding whitespace removed

#### Scenario: Print-init-json accepts dest-folder
- **WHEN** a user runs `openplate project print-init-json <source> --dest-folder generated/app`
- **THEN** OpenPlate parses the command successfully
- **AND** the printed prompt document is derived from the normalized init output root `generated/app`

#### Scenario: Missing top-level destination folder follows normal runtime rules
- **WHEN** a user omits `--dest-folder` when printing or importing init prompt JSON
- **THEN** OpenPlate resolves the top-level init output root using the same runtime-context rules that `project init` uses

#### Scenario: Sibling destination folder is required
- **WHEN** a sibling declaration omits `dest_folder` or its normalized value is empty
- **THEN** OpenPlate rejects that sibling declaration

#### Scenario: Sibling destination folder composes beneath the caller
- **WHEN** a reached caller node has project-relative destination folder `generated/app/services/api`
- **AND** that caller declares a sibling with normalized `dest_folder` `workers/job`
- **THEN** the called node's project-relative destination folder is `generated/app/services/api/workers/job`

#### Scenario: Prompt document is bound to the chosen init root
- **WHEN** a user prints init prompt JSON for normalized `--dest-folder generated/app`
- **AND** later runs `project init` with normalized `--dest-folder services/api`
- **THEN** the printed `node-id` values do not match the reached init nodes
- **AND** OpenPlate treats the supplied prompt nodes as unused input rather than reusing them across init roots

### Requirement: OpenPlate removes legacy prompt JSON flags from non-print verbs
OpenPlate SHALL NOT expose `--print-prompts-json` on `project update`.

Prompt export for update SHALL be available only through `openplate project print-update-json`.

OpenPlate SHALL expose `--prompts-json-file` and `--prompts-json-stdin` on top-level and legacy update commands.

OpenPlate SHALL NOT expose `--print-prompts-json` on `project init`; init prompt export SHALL continue to be available only through `project print-init-json`.

`project print-init-json` SHALL accept the same `--dest-folder` option that `project init` accepts.

#### Scenario: Update no longer accepts print-prompts-json
- **WHEN** a user runs `openplate project update --print-prompts-json`
- **THEN** OpenPlate rejects the command because `--print-prompts-json` is not a valid `project update` argument

#### Scenario: Update now accepts prompts-json-file
- **WHEN** a user runs `openplate update --prompts-json-file prompts.json`
- **THEN** OpenPlate parses the command successfully

#### Scenario: Update now accepts prompts-json-stdin
- **WHEN** a user runs `openplate project update --prompts-json-stdin`
- **THEN** OpenPlate parses the command successfully

#### Scenario: Init no longer accepts print-prompts-json
- **WHEN** a user runs `openplate project init <source> --print-prompts-json`
- **THEN** OpenPlate rejects the command because `--print-prompts-json` is not a valid `project init` argument

#### Scenario: Print-init-json accepts the init dest-folder option
- **WHEN** a user runs `openplate project print-init-json <source> --dest-folder generated/app`
- **THEN** OpenPlate parses the command successfully

### Requirement: OpenPlate prints prompt state as template-grouped JSON
OpenPlate SHALL retain this requirement title to modify the existing capability in place, even though the printed document defined by this change is node-based: each exported entry is a prompt node identified by `node-id`, not a template-keyed wrapper structure.

OpenPlate SHALL support `openplate project print-init-json <source>` as a read-only planning/export command that prints a JSON array of init prompt nodes instead of interactive prompt text.

`openplate project print-init-json <source> --verbose` SHALL print the same JSON node set with additional descriptive metadata.

The print-init command SHALL be read-only. It MUST NOT write files, update project configuration, or otherwise mutate workspace state.

The print-init command SHALL walk the full declared template tree without applying sibling `condition` filters. The printed JSON SHALL include the full declared template tree that can be discovered from the template configuration, including conditional sibling declarations. This export MAY include nodes that later execution does not process.

Each printed node SHALL include `node-id` and `answers`.

When print discovery can enumerate a node's in-scope parameters, exported `answers` SHALL include one key for each discovered in-scope parameter and each such key SHALL be initialized to `null`.

OpenPlate SHALL emit at most one printed node for each canonical raw template-reference plus normalized project-relative destination-folder identity reached by the export walk.

Each emitted `node-id` SHALL use lowercase hexadecimal. A full-hash `node-id` SHALL be the 64-character lowercase hexadecimal SHA-256 encoding of the canonical node identity. The preferred short `node-id` SHALL be the first 7 lowercase hexadecimal characters of that full hash.

`openplate project print-init-json <source>` SHALL emit the compact form and SHALL omit `info`.

`openplate project print-init-json <source> --verbose` SHALL emit the verbose form and SHALL include `info`. When present, `info` SHALL carry descriptive node metadata such as `template`, project-relative `dest_folder`, and `parameters` metadata excluding answer values.

When present, `info.template` SHALL use the raw template reference string for that node rather than a rendered value.

When a node declares sibling templates, verbose `info` MAY also include caller-side sibling declaration metadata such as `require_sibling_templates`. If present, those entries SHALL describe the caller's outgoing declarations, including the raw declared target template reference string, the called node's normalized project-relative destination folder, and any declaration condition.

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

#### Scenario: Print-init-json uses the chosen init root in prompt metadata
- **WHEN** a user runs `openplate project print-init-json <source> --dest-folder generated/app --verbose`
- **THEN** the exported root node reports project-relative `info.dest_folder` values beneath `generated/app`
- **AND** any rendered prompt metadata that depends on `dest_folder` is computed from that chosen init root

#### Scenario: Include conditional sibling declarations in init print export
- **WHEN** a template declares a sibling template behind a condition
- **THEN** either print form includes that sibling node in the printed JSON tree
- **AND** print export does not use that condition to prune the export tree

#### Scenario: Reached canonical init node is emitted once
- **WHEN** the export walk encounters the same canonical template-reference plus normalized project-relative destination-folder identity more than once
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
OpenPlate SHALL support `--prompts-json-file <path>` and `--prompts-json-stdin` for `project init` and `project update`. When either flag is used, OpenPlate MUST consume prompt answers from the provided JSON document and MUST NOT fall back to interactive prompting.

The supplied prompt document MUST be a top-level JSON array of node objects. Any other top-level JSON shape MUST be rejected.

`--prompts-json-file` and `--prompts-json-stdin` SHALL use the normal init or update execution walk. They MUST NOT switch to the full-tree, condition-ignoring discovery behavior reserved for `project print-init-json` or `project print-update-json`.

For init prompt JSON, callers MUST use the same resolved init output root when printing and importing. For update prompt JSON, callers MUST use the same selected project root and tracked template state when printing and importing.

Imported nodes MUST provide `node-id` and `answers`. Imported `info` MAY be present and MUST be ignored for import matching and resolution.

Imported init prompt nodes MUST continue to use the init answer shape, where each `answers` value is either a string or `null`.

Imported update prompt nodes MUST use the update answer-entry shape defined for update prompt JSON.

Documents that do not use the command-appropriate answer shape MUST be rejected.

Imported `node-id` values MUST use lowercase hexadecimal. A 64-character lowercase hexadecimal `node-id` MUST be treated as a full hash. A 7-character lowercase hexadecimal `node-id` MUST be treated as a short prefix. All other `node-id` formats MUST be rejected.

Within init `answers`, a non-null answer value MUST be treated as the authoritative supplied answer for a reached in-scope parameter. `null` and an omitted answer key MUST both mean unresolved so normal runtime fallback applies if that parameter is reached.

For init prompt JSON, hidden parameters MUST be in scope only when `--ask-hidden` is active for that command. Hidden answers supplied without `--ask-hidden` MUST be ignored as unused supplied answers.

For update prompt JSON, hidden parameters MUST always be in scope whether or not the command uses `--ask-hidden`.

If required values remain unresolved after applying supplied JSON, OpenPlate MUST fail instead of prompting. OpenPlate MAY fail on the first unresolved prompt rather than aggregating all missing values.

If template-command confirmation would have prompted during the run and the command has not otherwise been authorized, OpenPlate MUST fail instead of prompting.

Within a single command invocation, OpenPlate MUST NOT fetch or clone the same template source once for prompt validation and then again for actual processing. JSON-input execution MUST reuse fetched template sources for validation and execution.

When a non-null supplied answer value targets a parameter with `choices`, init and update MUST reject any value outside that choice set using the same value validation rule as interactive prompting.

#### Scenario: Supply answers from a compact init file
- **WHEN** a user runs `openplate project init <source> --prompts-json-file prompts.json`
- **AND** `prompts.json` contains nodes with `node-id` and init `answers`
- **THEN** OpenPlate reads prompt answers from `prompts.json`
- **AND** OpenPlate does not prompt for missing values during that run

#### Scenario: Non-array prompt document is rejected
- **WHEN** a supplied prompt document is a JSON object, string, number, or other non-array top-level value
- **THEN** OpenPlate rejects the document before template processing begins

#### Scenario: Supply answers from a verbose init file
- **WHEN** a user runs `openplate project init <source> --prompts-json-file prompts.json`
- **AND** `prompts.json` contains nodes with `node-id`, init `answers`, and `info`
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate ignores `info` for matching and answer resolution

#### Scenario: Supply answers from an update file
- **WHEN** a user runs `openplate update --prompts-json-file prompts.json`
- **AND** `prompts.json` contains nodes with `node-id` and update `answers`
- **THEN** OpenPlate reads prompt answers from `prompts.json`
- **AND** OpenPlate does not prompt for missing values during that run

#### Scenario: Supply answers from update stdin
- **WHEN** a user pipes an update prompt document to `openplate project update --prompts-json-stdin`
- **THEN** OpenPlate reads prompt answers from standard input
- **AND** OpenPlate does not reuse standard input as an interactive prompt channel

#### Scenario: Validation and execution reuse the same source fetch
- **WHEN** a user runs `openplate project init <source> --prompts-json-file prompts.json`
- **THEN** OpenPlate validates prompt input and processes that command without fetching or cloning the same template source twice

#### Scenario: Init prompt JSON requires the same dest-folder context
- **WHEN** a user prints init prompt JSON with one normalized `--dest-folder`
- **AND** later imports that document using a different normalized `--dest-folder`
- **THEN** OpenPlate does not reuse the printed prompt nodes for the later init run
- **AND** the caller must reprint prompt JSON for the later init placement

#### Scenario: Invalid answer value type is rejected
- **WHEN** a supplied JSON document uses a non-string, non-null answer value for init or a non-string, non-null `value` field for update
- **THEN** OpenPlate rejects the document before template processing begins

#### Scenario: Null init answer uses runtime fallback
- **WHEN** an imported init node sets `answers.param1` to `null`
- **THEN** OpenPlate does not answer that parameter from JSON
- **AND** OpenPlate uses the normal runtime fallback for that parameter if it is reached

#### Scenario: Missing init answer key uses runtime fallback
- **WHEN** an imported init node omits `param1` from `answers`
- **THEN** OpenPlate does not treat that parameter as answered by the prompt document
- **AND** OpenPlate uses the normal runtime fallback for that parameter if it is reached

#### Scenario: Non-null init answer overrides existing fallback
- **WHEN** an imported init node sets `answers.param1` to a non-null string for a reached in-scope parameter that already has an existing runtime value
- **THEN** OpenPlate uses the supplied JSON answer for that parameter

#### Scenario: Invalid choice value is rejected for init prompt JSON
- **WHEN** a supplied init prompt document sets a non-null answer for a parameter whose `choices` do not include that value
- **THEN** OpenPlate rejects the supplied prompt document during parameter resolution

#### Scenario: Invalid choice value is rejected for update prompt JSON
- **WHEN** a supplied update prompt document sets `supplied: true` with a non-null `value` for a parameter whose `choices` do not include that value
- **THEN** OpenPlate rejects the supplied prompt document during parameter resolution

#### Scenario: Missing required value in JSON mode
- **WHEN** JSON-input mode is active and a required parameter still has no resolved value after considering supplied answers and runtime fallback
- **THEN** OpenPlate fails
- **AND** OpenPlate does not ask the user for that value interactively

### Requirement: OpenPlate validates supplied prompt documents by template instance
OpenPlate SHALL match supplied prompt nodes using `node-id` only. OpenPlate MUST NOT use `template`, `dest_folder`, or other metadata fields for import matching.

OpenPlate SHALL derive a full node hash from the canonical raw template-reference plus normalized destination-folder identity used by the active prompt export command.

For init prompt JSON behavior, that destination identity SHALL be the normalized project-relative destination folder derived from the chosen init output root used by `project print-init-json` or `project init`.

For update prompt JSON behavior, that destination identity SHALL be the normalized project-relative destination folder from the tracked template configuration resolved from the selected project root used by `project print-update-json` or `update`.

During export, OpenPlate SHALL emit at most one node for each canonical prompt node identity, SHALL assign a short `node-id` when the preferred short hash is not already taken, SHALL reuse the same emitted node and exported `node-id` when the same canonical node is reached again, and SHALL export the full node hash when the preferred short hash is already taken by a different canonical node.

During import, OpenPlate MUST resolve node identifiers in two passes:
- first, exact full-hash matches
- then, unique short-hash matches against remaining unclaimed reached nodes

During import, OpenPlate MUST reject a supplied JSON document that contains duplicate `node-id` entries.

If an imported node does not correspond to a node that is actually processed by the init or update run, OpenPlate MUST ignore that supplied node and MUST print a log message identifying the unused `node-id`.

If supplied answers are present for a matched node but are not needed during processing, OpenPlate MUST print warnings for those unused supplied answers even when debug logging is disabled.

For update prompt JSON, only answer entries with `supplied: true` SHALL count as supplied answers for unused-answer warning behavior.

For update prompt JSON round-trips, callers MUST use the same selected `--project-root` and tracked template state when printing and importing if they expect node identity and metadata to remain valid.

#### Scenario: Round-trip compact init prompt document
- **WHEN** a user edits only init `answers` values in a document previously printed by `project print-init-json` with the same normalized `--dest-folder` context that later `project init` uses
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate matches nodes by `node-id`

#### Scenario: Round-trip verbose init prompt document
- **WHEN** a user edits only init `answers` values in a document previously printed by `project print-init-json --verbose` with the same normalized `--dest-folder` context that later `project init` uses
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate ignores unchanged `info` metadata during import

#### Scenario: Round-trip update prompt document
- **WHEN** a user edits only update `answers` entries in a document previously printed by `project print-update-json` for the same selected `--project-root` and tracked template state that later `update` uses
- **THEN** OpenPlate accepts the document as prompt input
- **AND** OpenPlate matches nodes by `node-id`

#### Scenario: Different init output roots do not share node identity
- **WHEN** one imported init node document was printed for normalized `--dest-folder generated/app`
- **AND** a later init run reaches the same raw template under normalized `--dest-folder services/api`
- **THEN** the earlier document's `node-id` does not match the later reached init node
- **AND** OpenPlate reports the earlier node as unused supplied input if it is provided

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
- **WHEN** a supplied JSON document includes an answered value for a matched reached node and that answer is not needed during processing
- **THEN** OpenPlate completes normal processing behavior for the node
- **AND** OpenPlate prints a warning about the unused supplied answer

### Requirement: OpenPlate prints update prompt state with separate answer intent
OpenPlate SHALL support `openplate project print-update-json` as a read-only planning/export command that prints a JSON array of update prompt nodes for the tracked project templates instead of interactive prompt text.

The print-update command SHALL walk the full declared template tree reachable from the tracked project templates without applying sibling `condition` filters. The printed JSON SHALL include the full declared template tree that can be discovered from the tracked template configuration, including conditional sibling declarations. This export MAY include nodes that later update execution does not process.

Each printed update node SHALL include `node-id`, `answers`, and `info`.

For update prompt export, `answers` SHALL be an object keyed by discovered in-scope parameter name. Each `answers` entry SHALL be an object with `supplied` and `value` fields. Exported update answer entries SHALL initialize `supplied` to `false` and `value` to `null`.

When print discovery can enumerate a node's in-scope parameters, `info.parameters` SHALL include one key for each discovered parameter. Each update parameter metadata entry SHALL include `current`, `existing`, `default`, `description`, `choices`, `hidden`, and `required`.

`current` SHALL be the effective value that update would use for that parameter if the exported answer entry remains unchanged with `supplied: false`.

`info.template` SHALL use the raw template reference string for that node, and `info.dest_folder` SHALL use the normalized project-relative destination folder for that node.

When a node declares sibling templates, `info.require_sibling_templates` MAY include caller-side sibling declaration metadata such as the raw declared target template reference string, the called node's normalized destination folder, and any declaration condition. Called nodes SHALL NOT carry caller-side declaration conditions as `info.condition`.

If print export cannot fully inspect a reached update node's parameters or caller-side sibling declaration metadata, OpenPlate MUST fail the export instead of emitting partial node data.

For update prompt export, hidden parameters SHALL be included in exported `answers` and exported `info.parameters` whether or not the command uses `--ask-hidden`.

#### Scenario: Print update prompts JSON
- **WHEN** a user runs `openplate project print-update-json`
- **THEN** OpenPlate prints a JSON array of update prompt nodes
- **AND** each printed node includes `node-id`, `answers`, and `info`

#### Scenario: Print update prompts JSON without mutating the workspace
- **WHEN** a user runs `openplate project print-update-json`
- **THEN** OpenPlate does not write project files or template output files
- **AND** OpenPlate does not update `.openplate.project.yaml` as part of printing the JSON document

#### Scenario: Update export seeds answers as unsupplied
- **WHEN** print discovery can enumerate the in-scope parameters for a reached update node
- **THEN** exported `answers` includes one key for each discovered in-scope parameter
- **AND** each exported answer entry uses `supplied: false` and `value: null`

#### Scenario: Update export reports current existing and default values
- **WHEN** verbose parameter metadata is available for a reached update node
- **THEN** `info.parameters` includes `current`, `existing`, and `default` fields for each discovered parameter
- **AND** `current` reflects the effective runtime value that update would use when the answer entry is left unsupplied

#### Scenario: Hidden parameters are always included in update export
- **WHEN** a user runs `openplate project print-update-json` without `--ask-hidden`
- **THEN** OpenPlate includes hidden parameters in exported update `answers`
- **AND** OpenPlate includes hidden parameter metadata in exported update `info.parameters`

#### Scenario: Parameterless reached update node emits empty answers
- **WHEN** print discovery succeeds for a reached update node and finds no in-scope parameters
- **THEN** exported `answers` is `{}`

#### Scenario: Include conditional sibling declarations in update print export
- **WHEN** a tracked template declares a sibling template behind a condition
- **THEN** print-update export includes that sibling node in the printed JSON tree
- **AND** print-update export does not use that condition to prune the export tree

### Requirement: OpenPlate interprets update prompt JSON answers explicitly
OpenPlate SHALL support `--prompts-json-file <path>` and `--prompts-json-stdin` for `project update` using an update-specific answer-entry shape.

For update prompt JSON input, each `answers` entry SHALL be an object with `supplied` and `value` fields. `supplied` MUST be a boolean. `value` MUST be either a string or `null`.

When an update answer entry sets `supplied` to `false`, `value` MUST be `null`. OpenPlate MUST treat that entry as not supplied and MUST use the normal update existing/default logic for that parameter.

When an update answer entry sets `supplied` to `true` and `value` to a non-null string, including `""`, OpenPlate MUST treat that value as the authoritative supplied answer for that parameter.

When an update answer entry sets `supplied` to `true` and `value` to `null`, OpenPlate MUST clear any persisted explicit value for that parameter before normal runtime fallback continues. If fallback then resolves only from template/default logic, OpenPlate MUST NOT rewrite that fallback value back as an explicit stored override in project configuration.

Only update answer entries marked with `supplied: true` SHALL count as supplied answers for unused-answer warning behavior.

For update prompt JSON input, hidden parameters SHALL always be in scope whether or not the command uses `--ask-hidden`.

#### Scenario: Unsupplied update answer preserves current behavior
- **WHEN** an imported update answer entry uses `supplied: false` and `value: null`
- **THEN** OpenPlate does not answer that parameter from JSON
- **AND** OpenPlate uses the normal update existing/default logic for that parameter if it is reached

#### Scenario: Supplied update null clears an existing override
- **WHEN** an imported update answer entry uses `supplied: true` and `value: null` for a parameter with a persisted explicit project value
- **THEN** OpenPlate clears that persisted explicit project value before resolving the parameter
- **AND** OpenPlate continues with normal runtime fallback behavior for that parameter

#### Scenario: Supplied update blank string is explicit
- **WHEN** an imported update answer entry uses `supplied: true` and `value: ""`
- **THEN** OpenPlate treats that parameter as explicitly supplied with a blank string value

#### Scenario: Unsupplied update answer cannot carry a value
- **WHEN** an imported update answer entry uses `supplied: false` and a non-null `value`
- **THEN** OpenPlate rejects the document before template processing begins

#### Scenario: Hidden update value is applied without ask-hidden
- **WHEN** an imported update prompt document supplies a hidden parameter value and the command does not use `--ask-hidden`
- **THEN** OpenPlate still applies that hidden supplied value if the parameter is reached

