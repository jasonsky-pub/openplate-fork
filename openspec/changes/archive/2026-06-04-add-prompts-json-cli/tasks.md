## 1. CLI and prompt document plumbing

- [x] 1.1 Add `--print-prompts-json`, `--prompts-json-file`, and `--prompts-json-stdin` to `project init` and `project update`, including argument validation so the JSON-input flags imply non-interactive behavior.
- [x] 1.2 Introduce a prompt-document model and JSON serialization/deserialization helpers for the template-grouped array format used by export and import.
- [x] 1.3 Reject duplicate supplied template nodes up front by validating the `(template, dest_folder)` pair before template processing begins.
- [x] 1.4 Preserve raw sibling template declarations before rendering so prompt export and JSON-input matching can use the original `template`, `dest_folder`, and `condition` strings.
- [x] 1.5 Add per-command source reuse for prompt discovery, validation, and execution so the same template source is not fetched twice within one invocation.

## 2. Prompt export and import behavior

- [x] 2.1 Implement `--print-prompts-json` as a read-only planning mode that performs the full print-only tree walk without applying sibling `condition` filters, emits raw `template`, raw `dest_folder`, optional `condition`, and never writes project state.
- [x] 2.2 During print-mode discovery, emit `parameters: null` for template declarations whose configs cannot be loaded closely enough to enumerate parameter metadata, so exported JSON distinguishes incomplete discovery from truly parameterless templates.
- [x] 2.3 Deduplicate exported template nodes by raw `(template, dest_folder)` using first-match behavior so exported JSON remains valid input.
- [x] 2.4 Thread imported prompt values into parameter resolution so JSON input uses parameter `value` fields, distinguishes `null` from `""`, rejects omitted `value` fields, and never falls back to interactive prompting.
- [x] 2.5 Ensure JSON-input modes stay on the normal runtime walk, fail on unresolved parameters or template-command confirmations instead of prompting, and do not switch to the print-only full-tree discovery behavior.
- [x] 2.6 Scope hidden parameters to `--ask-hidden` on prompt export and prompt import, while treating non-null JSON `value` fields as authoritative for in-scope parameters regardless of existing/default runtime fallback.

## 3. Validation, warnings, and coverage

- [x] 3.1 Track supplied template and parameter usage during processing so unmatched template nodes produce always-on ignored-template log messages and unused supplied parameters produce always-on warnings.
- [x] 3.2 Preserve the existing first-match runtime behavior for duplicate discovered sibling templates while keeping export deduplication and import validation strict for duplicate supplied template nodes.
- [x] 3.3 Add focused tests for read-only prompt JSON export, print-only full-tree export without applying conditions, `parameters: null` declaration nodes, export deduplication, JSON import from file and stdin, duplicate-template validation, ignored-template log messages, omitted-value failures, blank-string handling, unused-parameter warnings, single-fetch reuse, and unresolved-value failure paths.
- [x] 3.4 Update command documentation with the JSON round-trip workflow for machine-driven `project init` and `project update`.
- [x] 3.5 Add focused tests for hidden-parameter export scoping, hidden JSON import scoping, and authoritative non-null JSON overrides of existing runtime values.
- [x] 3.6 Clarify the OpenSpec artifacts and docs so `null`, non-null `value`, metadata-only fields, and `--ask-hidden` scope are all explicit.