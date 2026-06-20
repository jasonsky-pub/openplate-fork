## 1. Settings And CLI Surface

- [x] 1.1 Extend persistent OpenPlate settings and `config set` handling to support `allow_last_updater_email`.
- [x] 1.2 Add `--allow-last-updater-email` to init and update command parsing, including legacy `project` command forms.
- [x] 1.3 Add the top-level `openplate verify` parser entry while keeping `openplate project verify` functional and hidden from help.

## 2. Template Requirement Tracking And Consent

- [x] 2.1 Extend template config loading to accept `requires_last_updater_email` and mirror that requirement onto tracked template state.
- [x] 2.2 Implement run-scoped consent evaluation for requiring templates during init and update, including a single interactive prompt path and deterministic non-interactive failure behavior.
- [x] 2.3 Gate metadata resolution and template option compilation so only requiring templates receive `last_updater_email`.

## 3. Project Persistence And Runtime Cleanup

- [x] 3.1 Update project save behavior so `last_updater_email` is persisted only when at least one tracked template still requires it and consent was granted.
- [x] 3.2 Clear `last_updater_email` from `.openplate.project.yaml` when no tracked template requires it.
- [x] 3.3 Ensure verify continues to use existing execution flow without introducing new consent prompts.

## 4. Documentation And Validation

- [x] 4.1 Update `docs/commands.md` to document `openplate verify` as the primary verification command and keep nested `project verify` out of primary help and usage text.
- [x] 4.2 Add SSH template URL guidance showing how to export `GIT_SSH_COMMAND` before running OpenPlate with a non-default key.
- [x] 4.3 Add or update focused automated tests for settings parsing, CLI help output, consent gating, automation and prompt-JSON defaults, and project persistence cleanup.
- [x] 4.4 Update any relevant checked-in workflow coverage and run the focused validation commands needed for the CLI and consent-gating slices.