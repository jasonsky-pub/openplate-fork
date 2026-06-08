## Why

OpenPlate's most common workflows are still nested under `openplate project ...`, which makes the everyday CLI longer than it needs to be and keeps help text centered on an older command shape. The tool should make `init` and `update` first-class entrypoints while preserving the existing `project` forms so current scripts and habits keep working.

## What Changes

- Add `openplate init` and `openplate update` as the primary entrypoints for project initialization and project updates.
- Keep `openplate project init` and `openplate project update` working as backward-compatible command paths.
- Move the shared project-runtime flags needed by init and update onto the new top-level commands so the primary syntax stays fully functional.
- Hide the legacy `project` command from top-level help output and update user-facing documentation to advertise only `openplate init` and `openplate update`.
- Add focused validation for the new command forms, the legacy compatibility path, and help output so the visible CLI contract stays stable.

## Capabilities

### New Capabilities
- `top-level-init-update-commands`: Defines the primary `openplate init` and `openplate update` entrypoints, the backward-compatible legacy `project` aliases, and the help/documentation rules for surfacing only the new command forms.

### Modified Capabilities

## Impact

Affected areas include CLI argument parsing in `src/openplate/__main__.py`, command documentation in `docs/commands.md` and `readme.md`, and focused CLI parser/runtime tests covering help text and backward compatibility.