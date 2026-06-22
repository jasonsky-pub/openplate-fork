## Context

OpenPlate already has two different sources of project inspection data, but neither is presented in a human-oriented command. `.openplate.project.yaml` persists tracked template instances, source URLs, destination folders, versions, and saved parameter overrides, while the prompt-document collection path can fetch live templates and derive prompt descriptions, defaults, current values, choices, and sibling declaration metadata. Users currently have to read the YAML file directly or work indirectly from prompt JSON commands to understand the project state.

This change needs to add a human-readable `info` command without broadening the runtime scope beyond that goal. In particular, the user wants explicit offline behavior when template URLs are unreachable, does not want a machine-readable `info` mode, and does not want this change to refactor the existing prompt-metadata plumbing into best-effort partial output.

Two existing constraints shape the design:

- live prompt metadata is currently derived by fetching template sources through the prompt-document collection path, and that path fails when it cannot fully inspect a reached template
- the persisted project file does not currently distinguish directly requested templates from sibling-inherited templates, so provenance must be added if `info` is expected to show that distinction in both resolved and offline modes

## Goals / Non-Goals

**Goals:**
- Add a human-readable top-level `openplate info` command with a legacy `openplate project info` compatibility form.
- Make resolved `info` output show tracked templates, destination folders, saved values, and prompt metadata derived from inspected template sources.
- Add `--offline` so users can inspect tracked project data without fetching template sources.
- Add `--show-hidden` for resolved output so hidden prompt parameters can be shown on demand.
- Persist template provenance as `requested` or `inherited` so direct and sibling-added templates can be distinguished later.

**Non-Goals:**
- Add a machine-readable `info` output format.
- Change prompt JSON export or import contracts.
- Refactor the prompt-metadata collection path into partial or best-effort behavior.
- Redefine conditional-hidden semantics or add new hidden-reason reporting.

## Decisions

### 1. Build resolved info on top of prompt-document collection, not the init/update walker

The resolved `info` command should reuse the existing template-inspection path in `collect_prompt_document_all()` rather than reuse the recursive init/update walker directly. That path already fetches tracked templates, walks sibling declarations for metadata purposes, and derives the parameter details that matter for human inspection.

The new command should translate that collected metadata into a human-readable report instead of exposing the raw prompt JSON structure.

Alternatives considered:
- Reuse the update walker directly. Rejected because `info` does not need init/update side-effect behavior and the prompt-document collector is already the narrower read-only inspection surface.
- Read only `.openplate.project.yaml`. Rejected because the default command needs prompt descriptions and other live template-derived details.

### 2. Support two explicit inspection modes: resolved by default and offline on request

`openplate info` should default to resolved inspection, which loads the project file and then fetches tracked template sources to derive prompt metadata. `openplate info --offline` should skip template fetching entirely and report only persisted project-file data.

Resolved mode will intentionally keep the current strict failure behavior of the prompt-document collector. If a tracked template cannot be inspected, the command should fail and direct the user to `--offline` when they only need persisted state.

Alternatives considered:
- Make resolved mode silently fall back to partial offline output. Rejected because the user explicitly wants to keep this change narrow and avoid changing the existing strict inspection plumbing.
- Split this into two different commands. Rejected because the user wants one human-facing entry point with one explicit no-fetch option.

### 3. Persist template provenance on each tracked template entry

`ProjectTemplateConfig` should gain a backward-compatible optional provenance field serialized into `.openplate.project.yaml` using string values `requested` and `inherited`.

State rules:

- a direct CLI init adds or promotes the target template to `requested`
- a sibling auto-added during recursive processing is recorded as `inherited`
- once a template is `requested`, later sibling discovery must not demote it back to `inherited`
- older project files without the field remain valid and are treated as unknown provenance for display purposes

This keeps offline and resolved `info` output aligned and avoids trying to reconstruct origin after the fact.

Alternatives considered:
- Infer provenance at display time by comparing tracked templates to current sibling declarations. Rejected because it is brittle, depends on reachable templates, and cannot answer offline.
- Persist a single parent pointer for inherited templates. Rejected because one template instance can be discovered from multiple callers and that extra linkage is not required for the requested display.

### 4. Make full detail the default output and keep offline intentionally smaller

When template inspection succeeds, the report should show the richest available human-facing detail by default: template source, destination folder, provenance, version when available, parameter names, current values, saved existing values, defaults, descriptions, requiredness, and choices.

Offline mode should stay intentionally smaller because that information does not exist in the project file. Offline output should show only persisted fields such as template source, destination folder, provenance, version, and saved parameter overrides.

Alternatives considered:
- Make the command terse by default and require `--verbose` for useful details. Rejected because the user wants the default command to save humans from digging through YAML and, when fetching is already required, there is little value in hiding available detail.

### 5. Restrict --show-hidden to resolved inspection and keep hidden semantics aligned with existing prompt metadata behavior

`--show-hidden` should only be valid when `info` is performing resolved template inspection. In that mode, the command should pass through the same hidden-parameter inclusion behavior already used by prompt metadata collection rather than define a new hidden-evaluation rule.

`--offline --show-hidden` should be rejected because offline mode does not load the template definitions needed to decide which additional parameters become visible.

Alternatives considered:
- Allow `--show-hidden` in offline mode and print all saved parameter overrides. Rejected because offline data does not identify which parameters are hidden versus visible.
- Extend this change to modify conditional-hidden evaluation in prompt metadata. Rejected because the user explicitly removed that from scope.

### 6. Extend the existing top-level/legacy command family rather than invent a one-off entry path

The CLI parser should add `info` beside `init`, `update`, and `verify`, and the hidden legacy `project` subcommand should gain a matching `info` form for compatibility and consistency.

This keeps shared `--project-root` handling aligned with the existing command family and keeps help output predictable.

## Risks / Trade-offs

- [Resolved info depends on reachable template sources] -> Keep `--offline` as the explicit no-fetch path and document it in the command help and proposal artifacts.
- [Persisted provenance introduces a project-file schema addition] -> Make the field optional on read and write only when known so existing project files remain valid.
- [Default resolved output can become long for large projects] -> Keep the report grouped by tracked template and reserve offline mode for quick persisted-state checks.
- [Prompt metadata and project-file data are different sources of truth] -> Make offline output intentionally smaller so it is obvious which details are persisted and which require template inspection.

## Migration Plan

- Add a backward-compatible provenance field to tracked template serialization and deserialization.
- Stamp provenance during direct init and sibling auto-discovery.
- Add a new `info` command path and human-readable renderer, plus matching legacy parser support.
- Reuse prompt-document collection to build resolved inspection output and add an offline project-file-only renderer.
- Add focused tests for CLI parsing, provenance persistence, resolved info output, offline info output, and `--show-hidden` validation.
- Update user-facing command documentation to introduce `openplate info` and `--offline`.

No mandatory data migration is required because existing project files remain readable without provenance.

## Open Questions

- None.