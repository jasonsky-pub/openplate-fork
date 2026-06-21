## 1. CLI And Prompt-Document Wiring

- [x] 1.1 Add `openplate project print-init-json --dest-folder` and `openplate project print-update-json` to the CLI, and route them through read-only prompt export paths that resolve the same placement context the corresponding execution command uses.
- [x] 1.2 Add `--prompts-json-file` and `--prompts-json-stdin` to top-level and legacy update commands, load update prompt documents in `async_main()`, and pass prompt-document state into `project_update.run()`.
- [x] 1.3 Preserve the existing init answer shape while updating parser tests to cover `print-init-json --dest-folder`, accepted update JSON flags, rejected update print flags, and the new print-update command shape.

## 2. Update Prompt Export And Import Semantics

- [x] 2.2 Align init prompt identity and prompt metadata with the actual normalized init output root so `print-init-json` and `init` use the same project-relative destination context for node IDs, metadata, and rendered defaults.
- [x] 2.3 Implement update prompt export collection to walk the full declared tree from tracked templates, always include hidden parameters, and emit per-parameter metadata for `current`, `existing`, `default`, `description`, `choices`, `hidden`, and `required` using the same selected project context that update execution uses.
- [x] 2.4 Implement update prompt import behavior so `supplied: false` stays inert, `supplied: true` with a non-null string is authoritative, and `supplied: true` with `null` clears persisted explicit values before normal fallback logic continues.
- [x] 2.5 Update prompt tracking, unused-answer warnings, and ignored-node logging so update counts only `supplied: true` entries as supplied answers while preserving shared node-id matching and source-reuse behavior.
- [x] 3.1 Keep the shared prompt-resolution path enforcing choice validation for both init and update prompt JSON imports, and add explicit regression coverage for invalid choice values in both flows.
- [x] 3.2 Ensure clearing an update override does not immediately re-persist fallback-only values as explicit project config, and add focused tests for clear, preserve, and explicit blank-string cases.
- [x] 3.3 Add or update focused automated tests for init `--dest-folder` export fidelity, dest-folder-dependent defaults or sibling paths, mismatched init placement behavior, and parser acceptance for `print-init-json --dest-folder`.
- [x] 3.4 Add or update focused automated tests for update prompt export shape, hidden-parameter inclusion without `--ask-hidden`, full-tree export behavior, update stdin import, invalid update answer shapes, duplicate node-id handling, unused supplied-answer warnings, project-context consistency, and round-trip node-id matching.

## 4. Docs And Manual Workflow

- [x] 4.1 Update `docs/commands.md` and `docs/templates.md` to document that init prompt export must use the same `--dest-folder` as the later init run, that update prompt export must use the same selected project context as the later update run, explain the difference between init and update answer shapes, call out update hidden-parameter behavior, and document the clear-versus-unchanged semantics explicitly.
- [x] 4.2 Update the checked-in manual workflow docs, coverage matrix, and case files so prompt JSON coverage includes `project print-init-json --dest-folder`, `project print-update-json`, init placement-consistency behavior, update project-context consistency, update hidden-parameter visibility, and prompt JSON invalid-choice rejection behavior.
- [x] 4.3 Regenerate any checked-in prompt JSON examples or manual-test artifacts affected by the update round-trip contract.
- [x] 4.4 Run the focused automated prompt JSON tests and the relevant checked-in manual test cases before considering the change ready, including the prompt JSON workflow case and the update lifecycle case if its fixtures or expectations change.