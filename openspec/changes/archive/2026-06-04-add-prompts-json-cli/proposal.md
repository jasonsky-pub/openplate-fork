## Why

OpenPlate can already stop when a prompt would be required, but it does not give automation a structured way to discover pending prompts or feed answers back in for `project init` and `project update`. That forces AI and CI workflows to scrape terminal text, guess sibling template identity, or fall back to interactive runs.

## What Changes

- Add JSON-based prompt export for `project init` and `project update` with `--print-prompts-json`.
- Add JSON-based prompt input for `project init` and `project update` with `--prompts-json-file` and `--prompts-json-stdin`.
- Define a hierarchical JSON format grouped by template reference and destination folder, with parameter values nested inside each template node.
- Make `--print-prompts-json` a read-only planning/export mode that does not write project files or mutate workspace state.
- Make `--print-prompts-json` the only mode that walks the full declared template tree without applying sibling `condition` filters.
- Include template `condition` metadata in printed JSON output for visibility, while ignoring that field on import.
- Scope hidden parameters to `--ask-hidden` on both prompt export and prompt import.
- Require JSON-input modes to fail instead of prompting when required values are still unresolved.
- Warn when supplied JSON contains extra parameters that were not needed, and print a log message including the template and destination folder when a template instance from the JSON is ignored because it is not processed by the run.
- Reject duplicate template-instance entries that use the same template reference and destination folder.
- Define `value: null` as "do not answer this parameter; let runtime fallback apply", `value: ""` as an intentional blank string answer, and any other non-null `value` as the authoritative supplied answer for that in-scope parameter.
- When print-mode can discover a template declaration but cannot inspect its parameter metadata, emit `parameters: null` so automation can distinguish incomplete discovery from templates that truly have no parameters.
- Reuse fetched template sources within a command invocation so OpenPlate does not pull a repo once for prompt validation and then pull it again for actual processing.

## Capabilities

### New Capabilities
- `project-prompts-json`: Defines prompt discovery and prompt input through JSON for `project init` and `project update`, including template-instance scoping, validation, and warning behavior.

### Modified Capabilities

## Impact

Affected areas include CLI argument parsing in `src/openplate/__main__.py`, prompt resolution in `src/openplate/project_config_resolver.py`, recursive sibling-template walking in `src/openplate/walk/source_template_recursive_walk.py`, template source reuse for prompt discovery and execution, prompt JSON serialization/deserialization helpers, and documentation for machine-driven init and update workflows.