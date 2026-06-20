## Context

OpenPlate currently treats `last_updater_email` as unconditional project metadata. `resolve_project_metadata()` refreshes it from the Git identity on every non-automation run, `compile_template_options()` injects it into every template option set, and `.openplate.project.yaml` persists it without checking whether any tracked template actually needs it.

That behavior creates three problems:

- there is no operator consent boundary for exposing an email address into template rendering
- templates that do not care about `last_updater_email` still receive it at runtime
- project persistence cannot distinguish between required and unneeded email state

The same request also bundles two smaller but related CLI surface issues:

- `verify` is still only exposed through the legacy `openplate project verify` path even though `init` and `update` already have top-level forms
- command documentation does not tell users how to select a non-default SSH key before running OpenPlate against SSH template URLs

## Goals / Non-Goals

**Goals:**
- Add a persistent user setting and one-time CLI override that explicitly allow `last_updater_email` usage.
- Add a template-authored configuration flag that declares when a template requires `last_updater_email`.
- Ensure init and update only resolve, inject, prompt for, or persist `last_updater_email` when at least one relevant template requires it.
- Define deterministic non-interactive behavior: automation and prompt-JSON-driven runs default consent to false and fail instead of prompting.
- Save `last_updater_email` into `.openplate.project.yaml` only when at least one tracked template requires it and consent was granted; clear it on save otherwise.
- Expose `openplate verify` as the primary top-level command while keeping `openplate project verify` functional but hidden from help and docs.
- Update `docs/commands.md` so SSH key selection is documented with a `GIT_SSH_COMMAND` export example.

**Non-Goals:**
- Add generic prompt-JSON import support to update.
- Turn `last_updater_email` into a normal template parameter answered through the existing parameter question flow.
- Change verify semantics to prompt for new email consent during drift checks.
- Add SSH transport selection logic inside OpenPlate itself; the docs change only explains the existing Git mechanism.

## Decisions

### 1. Model consent as a dedicated runtime policy, not as a template parameter

Add a persistent settings field named `allow_last_updater_email` and expose it through `openplate config set` in the same style as the existing `allow_template_commands` toggle. Add a per-run CLI flag named `--allow-last-updater-email` to init and update command surfaces, including their legacy `project` forms.

Consent precedence:

1. per-run CLI allow flag
2. persistent user setting
3. interactive prompt when a requiring template is encountered
4. implicit false in non-interactive contexts

Alternative rejected: treat the email as a normal template parameter. That would make a global trust decision look like template content and would incorrectly mix operator consent with template-authored parameter prompts.

### 2. Put the requirement flag in template config and mirror it onto tracked template state

Add a template-authored boolean field `requires_last_updater_email` to template configuration. Its default is false.

When a template is loaded, OpenPlate copies the current value of that flag into the tracked `ProjectTemplateConfig` entry for that template. This gives the runtime a persisted view of whether each tracked template currently requires the email, which allows project save logic to clear `last_updater_email` without recloning every tracked template during unrelated runs.

Alternative rejected: determine whether any template requires the email only by re-opening every tracked template source before each save. That would work functionally but adds avoidable source-loading overhead and makes save-time behavior depend on remote availability.

### 3. Resolve and inject `last_updater_email` only for requiring templates

The runtime shall treat `last_updater_email` as template-scoped consent-gated metadata even though the resolved value is stored once at the project level.

Rules:

- if the current template does not require the email, template option compilation sets `last_updater_email` to an empty string for that template
- if the current template requires the email and consent is allowed, OpenPlate resolves the Git email and stores it on `ProjectConfig.last_updater_email`
- if the current template requires the email and consent is not allowed, the template fails before file processing continues

The gating hook belongs in the metadata-resolution path that already feeds prompt collection and template option compilation, not in the generic parameter resolver.

### 4. Ask for consent once per run and default to false when prompting is not allowed

When the first requiring template is encountered during init or update and neither the CLI flag nor the persistent setting allows email use, OpenPlate prompts the operator once for consent and reuses that decision for the rest of the run.

Prompt handling:

- interactive init or update: ask once and cache the answer for the run
- automation mode (`--automation`): do not prompt; treat consent as false
- prompt-JSON init input present: do not prompt; treat consent as false

When consent resolves to false for a requiring template, OpenPlate fails that template with a targeted message explaining that `last_updater_email` was required but not allowed.

Alternative rejected: silently skip the variable and continue. That would let requiring templates render incomplete or misleading output while hiding a policy failure.

### 5. Save project email state only when the tracked template set still requires it

Before `.openplate.project.yaml` is written, OpenPlate derives a project-level `has_requiring_template` boolean from tracked template state.

- if `has_requiring_template` is false, clear `ProjectConfig.last_updater_email`
- if `has_requiring_template` is true and the current run has allowed email usage, persist the resolved value
- if `has_requiring_template` is true but no resolved value is available because the run failed consent gating, the run should already have stopped before save

This keeps the persisted project file aligned with the currently tracked template set rather than with whatever metadata a previous run happened to capture.

### 6. Make `verify` a top-level alias without expanding legacy help surface

Follow the existing `init` and `update` pattern:

- add `openplate verify` as a top-level parser entry using the current verify execution path
- keep `openplate project verify` as a compatibility form
- hide the `project` command from top-level help
- document `verify` as the supported syntax and mention the nested form only as legacy compatibility if needed

### 7. Document SSH key selection as a Git precondition, not an OpenPlate option

Update `docs/commands.md` in the init and command-runtime guidance to show that users who need a special SSH key should export `GIT_SSH_COMMAND` before invoking OpenPlate, for example with `ssh -i <key> -o IdentitiesOnly=yes`.

The documentation should make clear that this matters only for SSH template URLs because OpenPlate passes the source URL directly to Git.

## Risks / Trade-offs

- [Tracked requirement state can drift from template sources] → Refresh the mirrored per-template requirement flag whenever a template is walked during init or update.
- [Consent failures will stop previously permissive runs] → Use explicit error text that points to the CLI flag and persistent config setting.
- [A run-scoped cached consent answer broadens one approval across multiple requiring templates] → This is intentional to avoid repeated prompts during sibling-template or multi-template update flows; document it in the design and tests.
- [Verify remains read-only and will not gather new consent] → Rely on persisted project state for verify runs and keep consent acquisition scoped to init and update as requested.
- [SSH documentation may be misread as transport rewriting] → State that the export only affects Git SSH invocations and does nothing for HTTPS template URLs.

## Migration Plan

1. Extend settings, CLI parsing, and config-set handling for `allow_last_updater_email` and `--allow-last-updater-email`.
2. Extend template config deserialization for `requires_last_updater_email` and mirror that value into tracked template config.
3. Add run-scoped consent evaluation to init and update metadata resolution so requiring templates either resolve the email or fail deterministically.
4. Gate `compile_template_options()` so non-requiring templates see an empty `last_updater_email`.
5. Add project-save cleanup so `last_updater_email` is removed when no tracked template still requires it.
6. Add the top-level `verify` parser and update docs/help examples.
7. Update command docs with the `GIT_SSH_COMMAND` export example and add focused tests for parsing, consent behavior, persistence cleanup, and legacy verify compatibility.

## Open Questions

None. The main remaining work is encoding the consent gate consistently across init, update, tracked-template persistence, and documentation.