## Why

OpenPlate currently resolves and persists `last_updater_email` whenever the run is not marked as automation, even when no template needs that value and even when the operator has not explicitly allowed it. At the same time, the top-level CLI still exposes `verify` only through the legacy `project verify` path, and the command docs do not explain how to preconfigure Git SSH key selection for template clones that require a non-default key.

## What Changes

- Add explicit consent controls for `last_updater_email` through persistent user configuration and a one-time CLI override.
- Add a template-level flag that declares whether a template requires `last_updater_email` before OpenPlate resolves or injects that value for that template.
- Define init and update behavior when a template requires `last_updater_email` but the operator has not pre-authorized it, including prompting rules for interactive runs and non-interactive defaults for automation and prompt-JSON-driven runs.
- Restrict project-file persistence so `last_updater_email` is saved only when at least one tracked template requires it and permission has been granted, and clear it on save when no tracked template requires it.
- Expose `openplate verify` as the documented top-level command while keeping `openplate project verify` as a hidden compatibility alias.
- Update the running-commands documentation to show how to export `GIT_SSH_COMMAND` before invoking OpenPlate when a special SSH key is needed.

## Capabilities

### New Capabilities
- `last-updater-email-consent`: Governs when templates may require `last_updater_email`, how operators authorize its use, when OpenPlate may prompt for consent, and when the value is persisted into project state.

### Modified Capabilities
- `top-level-init-update-commands`: Extend the top-level CLI command family so `verify` is available and documented alongside `init` and `update` while the legacy nested `project verify` form remains hidden but supported.

## Impact

- Affected code: CLI argument parsing, persistent user settings, project/template config serialization, runtime metadata resolution, prompt handling for init and update, project save behavior, and verify command help/docs.
- Affected docs: `docs/commands.md` for top-level `verify` usage and SSH key export guidance.
- Affected tests: CLI parsing/help coverage, `last_updater_email` runtime and persistence behavior, prompt/automation handling, and compatibility coverage for legacy `project verify`.