## Context

OpenPlate's current prompt JSON contract is intentionally init-only on the main branch. The parser rejects update-side prompt JSON flags, the documentation describes only the init round-trip, and the manual workflow keeps prompt JSON and update behavior in separate cases. At the same time, the runtime already has most of the shared mechanics needed for update prompt JSON: node-id matching, prompt tracking, source reuse, and choice validation for non-null supplied answers all already exist in the shared prompt-resolution path.

The requested change is not a straight restoration of the earlier archived update JSON flow. Update has a different operator need than init. For init, blank answer slots are enough because there is no prior persisted parameter state. For update, callers need to see current effective values, persisted explicit values, and processed defaults without pre-filling the editable answer channel. They also need a way to say three different things for one parameter: leave it alone, set it explicitly, or clear a stored override and fall back to default logic.

There is also an init-side contract gap to fix while touching this surface. The current init prompt implementation makes prompt matching root-independent, but prompt metadata and default evaluation can still depend on the actual `dest_folder` runtime value. That means an exported prompt document can match on import while still describing the wrong effective defaults if the later init uses a different `--dest-folder`. The prompt planning contract should therefore be bound to the same placement context that execution uses, not to a root-independent abstraction.

This makes the change cross-cutting. It affects CLI parsing, prompt export and import document shapes, update execution, config persistence semantics, shared validation behavior, documentation, automated tests, and the checked-in manual workflow.

## Goals / Non-Goals

**Goals:**
- Add a read-only `openplate project print-update-json` planning command for update prompt export.
- Make `openplate project print-init-json` accept the same `--dest-folder` placement context as init and bind exported identity and metadata to that chosen output root.
- Add `--prompts-json-file` and `--prompts-json-stdin` support to update using the same non-interactive execution policy as init.
- Keep init prompt JSON behavior intact while introducing an update-specific answer shape that distinguishes untouched, explicitly supplied, and explicitly cleared values.
- Make update prompt exports always include hidden parameters and enough state metadata to be actionable without inspecting `.openplate.project.yaml` manually.
- Ensure prompt export and execution commands use the same resolved placement context, and document that requirement clearly for both init and update prompt workflows.
- Ensure prompt JSON choice validation is enforced for both init and update using the same rules as interactive prompting.
- Document the update round-trip clearly in `docs/commands.md` and `docs/templates.md`, and cover it in the checked-in manual workflow.

**Non-Goals:**
- Redesign the existing init prompt JSON document shape.
- Remove or redefine interactive `openplate update --ask-hidden` behavior outside prompt JSON flows.
- Replace node-id matching with a different identity model.
- Add a schema-version wrapper or a second machine-readable error protocol.

## Decisions

### 1. Add a dedicated `project print-update-json` command

Update prompt export will use a dedicated read-only command, `openplate project print-update-json`, rather than reviving `openplate update --print-prompts-json`.

This keeps export aligned with the current init contract, where read-only prompt planning is separated from commands that mutate the workspace. It also avoids overloading `update` with a print-only mode that looks like a normal write path.

Alternatives considered:
- Reintroduce `openplate update --print-prompts-json`. Rejected because the current branch deliberately moved prompt export to explicit print commands.
- Reuse `project print-init-json` with a mode flag. Rejected because init and update have materially different export semantics and required metadata.

### 2. Bind prompt export to the same execution context as the real command

Prompt export must use the same placement context as the command that will later consume it.

For init, `project print-init-json` will accept `--dest-folder`, and prompt identity, `info.dest_folder`, sibling destination composition, and prompt metadata such as rendered defaults will all be derived from the same normalized project-relative destination folders that `init` itself will use.

For update, `project print-update-json` and `update` must be run against the same selected `--project-root` and tracked template state so the exported prompt document describes the same project-relative destination folders and effective current values that update execution will use.

This replaces the current root-independent init prompt identity rule because that rule can make export metadata lie about runtime behavior when `dest_folder` participates in template defaults or sibling paths.

Alternatives considered:
- Keep root-independent init prompt identity and fix only documentation. Rejected because the export would remain a misleading planning surface for `dest_folder`-dependent templates.
- Keep root-independent node identity but add a secondary context field that callers must compare manually. Rejected because the export and import path should reject or naturally mismatch inconsistent placement rather than relying on external discipline alone.

### 3. Update prompt export walks the full declared tree from tracked templates

`project print-update-json` will start from the project's tracked templates and walk the full declared sibling tree without applying sibling `condition` filters, the same way init print export walks its declared tree.

This is necessary for one-pass round-trips. If a caller changes an upstream answer that activates a conditional sibling or newly relevant parameter, the export must already contain the potential target node so the later update run can stay non-interactive.

Alternatives considered:
- Export only the currently active runtime tree. Rejected because changed answers could activate previously unseen nodes and break the promised export-edit-import workflow.

### 4. Update answers separate answer intent from parameter state

Update will use a different `answers` entry shape than init. Each update answer entry will be an object with:
- `supplied`: boolean
- `value`: string or `null`

Exported update answers will initialize every discovered parameter to `{"supplied": false, "value": null}`.

Import semantics will be:
- `supplied: false`, `value: null`: leave this parameter untouched and use normal update existing/default logic.
- `supplied: true`, non-null string value: use the supplied value authoritatively. `""` remains an explicit blank string.
- `supplied: true`, `value: null`: clear any persisted explicit value for this parameter and continue with normal fallback resolution.

To avoid silent mistakes, `supplied: false` with a non-null `value` will be rejected as an invalid combination.

Alternatives considered:
- Pre-fill editable answers with current values. Rejected because callers and models would have to infer which values were intentionally changed versus simply copied forward, and newly added parameters would be too easy to freeze accidentally.
- Keep update on the init scalar answer shape and treat `null` as clear. Rejected because there would be no way to distinguish "leave unchanged" from "clear the override".

### 5. Update metadata reports `current`, `existing`, and `default`

Update export needs to show parameter state without making that state itself the editable answer channel. The exported metadata for each update parameter will therefore include:
- `current`: the effective value update would use if `supplied` stays `false`
- `existing`: the persisted explicit project value, if any
- `default`: the processed template or global default value, if any
- `description`, `choices`, `hidden`, and `required`

The field is named `current` rather than `literal` so it clearly represents effective runtime behavior, not raw template text.

Alternatives considered:
- Show only `existing` and `default`. Rejected because callers would still need to reconstruct current behavior themselves.
- Put state only in `.openplate.project.yaml`. Rejected because the prompt export needs to be self-contained.

### 6. Hidden parameters are always included for update prompt JSON

Update prompt JSON export and import will ignore `--ask-hidden` and always include hidden parameters in scope. Interactive update behavior can keep its existing `--ask-hidden` semantics; this change is limited to prompt JSON flows.

This avoids the core ambiguity the user called out: with update, callers otherwise cannot tell whether a hidden parameter already has a stored explicit value that should be preserved, changed, or cleared.

Alternatives considered:
- Reuse `--ask-hidden` for update prompt JSON. Rejected because it makes complete update exports depend on an orthogonal flag and hides persisted state.

### 7. Clearing an override must not immediately re-persist fallback as an override

`supplied: true` with `value: null` means "clear the explicit override and use normal existing/default logic," not "set the parameter to whatever fallback value happens to resolve right now."

Implementation therefore needs an explicit cleared-state path in update parameter resolution and write-back. If fallback comes only from template/default logic after the clear, OpenPlate should keep the parameter absent from persisted project configuration rather than re-writing the fallback value as a new explicit override.

Alternatives considered:
- Treat clear as "delete, then immediately store the resolved default." Rejected because it defeats the point of clearing the override.

### 8. Shared validation remains unified across init and update

Init and update will continue to share node-id matching, `info`-ignored import behavior, duplicate-node rejection, source reuse, and non-interactive failure behavior.

Both commands must also reject invalid prompt JSON choice values under the same rule as interactive prompting. The current shared resolver already validates non-null supplied values against `parameter.choices`; this change will preserve that path and add explicit test and spec coverage for both init and update.

For update-specific unused-answer warnings, only entries with `supplied: true` count as supplied answers. Exported-but-untouched entries with `supplied: false` must remain inert.

## Risks / Trade-offs

- [Init and update will have different answer shapes] -> Keep init unchanged for compatibility and document the difference explicitly in command docs and specs.
- [Init prompt documents printed for one placement will no longer be reusable for another] -> Make `print-init-json` accept `--dest-folder`, ensure mismatched contexts fail to match naturally, and document the same-context requirement explicitly.
- [Clear semantics require persistence changes] -> Add focused tests for clearing an existing override, preserving omission after fallback, and explicit blank-string persistence.
- [Full-tree update export may include nodes not processed later] -> Preserve ignored-node logging and document that update print export is broader than runtime selection.
- [Always including hidden update parameters exposes more state than init] -> Limit the behavior to update prompt JSON and document why update differs.
- [Prompt JSON manual coverage becomes larger] -> Keep prompt JSON flows grouped under one case and use scripted fixtures so the additional update coverage stays deterministic.

## Migration Plan

1. Extend the spec and docs first so the new update round-trip contract and the new init placement-binding rule are explicit before implementation begins.
2. Add parser wiring for `project print-init-json --dest-folder`, `project print-update-json`, and update-side prompt document plumbing while preserving the existing init answer shape.
3. Extend prompt export and import helpers to support update-specific answer entries and clear-state persistence.
4. Align init prompt identity and prompt metadata with the actual normalized init output root so export and import use the same placement context.
5. Add focused automated coverage for parser acceptance, init `--dest-folder` fidelity, export shape, hidden-parameter inclusion, clear behavior, and choice validation for both init and update.
6. Update the checked-in manual workflow, regenerate the affected prompt JSON artifacts, and rerun the relevant manual cases.

## Open Questions

None.