## Why

OpenPlate's current prompt JSON workflow is clear for init but unavailable for update, which forces automated or model-driven update runs back to interactive prompting or ad hoc project-file edits. The current init export path also treats prompt identity as root-independent, which can make printed metadata disagree with what a later `init --dest-folder ...` run will actually resolve when prompt defaults or sibling paths depend on `dest_folder`.

## What Changes

- Add a read-only update prompt export flow so users can inspect update prompt state first, edit JSON, and then run update with that JSON instead of interactive prompts.
- Change init prompt export so `project print-init-json` accepts the same `--dest-folder` context as `init` and binds prompt identity and metadata to that chosen destination root instead of a root-independent abstraction.
- Add prompt JSON input support to update using the same non-interactive execution model as init, including the same node-id matching, unused-input warnings, and invalid-answer-type rejection behavior.
- Define update-specific prompt JSON metadata so exports show each parameter's effective current value, existing stored value, and processed default value while keeping the editable answer channel separate.
- Add an explicit update answer-state model so exported update answers default to "not supplied", `null` means "clear supplied answer and use normal existing/default logic", and non-null strings, including `""`, remain authoritative explicit answers.
- Make update prompt JSON always include hidden parameters instead of depending on `--ask-hidden`, so update exports are complete and do not require callers to infer whether a prior hidden override exists.
- Require prompt export and execution commands to use consistent placement context: the same resolved `--dest-folder` for init prompt export and init import, and the same selected `--project-root` and tracked template state for update prompt export and update import.
- Require choice validation parity for prompt JSON imports so invalid choice values fail for both init and update under the same rules as interactive prompting.
- Update command and template documentation to explain the update prompt JSON round-trip as clearly as the current init documentation.
- Update command and template documentation to call out that print and execution commands must use the same destination or project context for prompt JSON round-trips to remain valid.
- Update focused automated tests and checked-in manual test coverage for the update prompt JSON flow and its validation rules.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `project-prompts-json`: extend prompt JSON behavior from init-only to a documented update round-trip flow, while also changing init prompt export to bind identity and metadata to the chosen init destination root.
- `manual-tests-workflow`: extend the checked-in manual workflow inventory and case coverage so prompt JSON behavior includes the new update flow and its validation expectations.

## Impact

- Affected specs: `project-prompts-json`, `manual-tests-workflow`.
- Affected CLI surfaces: `openplate init`, `openplate project print-init-json`, `openplate update`, `openplate project update`, and a new read-only `openplate project print-update-json` planning path.
- Affected runtime areas: parser wiring in `src/openplate/__main__.py`, prompt export and import helpers under `src/openplate/prompts/`, init and update execution in `src/openplate/commands/project_init.py` and `src/openplate/commands/project_update.py`, and shared parameter resolution and validation paths.
- Affected docs and validation: `docs/commands.md`, `docs/templates.md`, automated prompt JSON tests, and the checked-in manual test cases and artifacts for prompt JSON and update flows.