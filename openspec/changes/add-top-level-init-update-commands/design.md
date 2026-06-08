## Context

OpenPlate currently exposes its main project workflows as nested subcommands under `project`, so the everyday entrypoints are `openplate project init` and `openplate project update`. The parser in `src/openplate/__main__.py` also attaches shared project-runtime flags such as `--project-folder`, `--ask-again`, `--ask-hidden`, and `--ignore-tool-version` to that legacy `project` parser, which means the current structure is both user-visible and implementation-significant.

The requested change is not just an alias rename in docs. The visible primary interface must become `openplate init` and `openplate update`, while existing `openplate project init` and `openplate project update` invocations keep working. Top-level help should advertise only the new entrypoints.

## Goals / Non-Goals

**Goals:**
- Make `openplate init` and `openplate update` the primary command forms shown in help and docs.
- Preserve `openplate project init` and `openplate project update` as compatibility paths.
- Keep init and update behavior, option parsing, and runtime dispatch aligned across new and legacy forms.
- Ensure shared project-runtime flags remain available for the new primary commands.
- Add focused tests for help output and compatibility routing.

**Non-Goals:**
- Redesign unrelated commands such as `config`.
- Rename `verify` as part of this change unless it is needed for parser consistency.
- Change init/update business logic beyond what is required to expose the new command surface.
- Remove the legacy `project` compatibility path in this change.

## Decisions

### 1. Make `init` and `update` first-class top-level parsers

`create_arg_parser()` should define top-level `init` and `update` subparsers alongside existing top-level commands such as `config`. These top-level parsers will set the same command identifiers currently used by the runtime dispatch (`project-init` and `project-update`) so the downstream execution path remains stable.

Alternatives considered:
- Rewrite argv before parsing. Rejected because it obscures help behavior and makes option placement rules harder to reason about.
- Introduce new command identifiers and separate dispatch branches. Rejected because the behavior is already implemented and does not need a second runtime path.

### 2. Extract shared project options into reusable parser helpers

The flags currently hanging off `project` are required for the primary init/update workflows. A shared helper should add the common project-runtime options to both new top-level parsers and legacy compatibility parsers so the new command forms are self-sufficient and the old forms stay behaviorally aligned.

This keeps parser construction explicit and avoids maintaining two divergent copies of flags over time.

Alternatives considered:
- Hoist the project flags to the global parser. Rejected because those flags are not meaningful for `config` and would clutter global help.
- Leave shared flags only on the legacy `project` path. Rejected because it would make the new primary commands incomplete.

### 3. Keep a hidden `project` compatibility parser

The parser should retain a top-level `project` command, but its help entry should be suppressed so `openplate --help` advertises only the new primary forms. Inside that hidden parser, `init` and `update` remain available and should map to the same command identifiers and shared option helpers as the new top-level commands.

This approach preserves compatibility while giving help output a clean break.

Alternatives considered:
- Remove `project` entirely and break legacy invocations. Rejected because backward compatibility is an explicit requirement.
- Keep `project` visible in help with a deprecation note. Rejected because the requested behavior is that help should only show the new commands.

### 4. Update docs and tests to treat legacy forms as compatibility-only

User-facing docs should be rewritten to show `openplate init` and `openplate update` as the supported syntax. Legacy `openplate project ...` forms may be mentioned only as compatibility notes where needed. Focused tests should cover parser acceptance for both new and old forms plus the top-level help contract.

Alternatives considered:
- Limit the change to parser behavior and leave docs/help mixed. Rejected because the visible contract would remain ambiguous.

## Risks / Trade-offs

- [Option drift between new and legacy parsers] -> Build init/update parsers from shared helper functions instead of duplicating flags manually.
- [Hidden compatibility command still discoverable through direct use] -> Accept this as an intentional trade-off for backward compatibility while keeping top-level help and docs clean.
- [Existing automation may depend on exact help text ordering] -> Add focused tests for the important visible help contract and keep the runtime command identifiers unchanged.
- [Future command additions may forget the new primary/legacy split] -> Keep parser construction centralized and documented in the design and tasks.

## Migration Plan

- Add top-level `init` and `update` parsers that dispatch through the existing runtime command flow.
- Rebuild the legacy `project` parser as a hidden compatibility path for `init` and `update`.
- Update command documentation and README examples to use `openplate init` and `openplate update`.
- Add focused tests covering both the new primary syntax and the hidden compatibility syntax.

## Open Questions

- Should a follow-up change also introduce `openplate verify` so the remaining project workflow commands follow the same top-level shape?