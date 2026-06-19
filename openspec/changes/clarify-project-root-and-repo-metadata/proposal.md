## Why

OpenPlate currently blurs the folder an operator launches from, the root folder the tool should manage, and the destination path where a template instance should land. That ambiguity is most visible when OpenPlate is run from a Git subfolder: repo-root-owned files such as `.github/` become hard to reason about, and the current `dest_folder` behavior is not explicit enough.

At the same time, the project file stores snapshots of project metadata that the runtime already knows how to recalculate, and Git URL handling does not yet normalize SSH and HTTPS forms, strip embedded credentials, or preserve template `?path=` and `#ref` semantics when converting between URL forms.

## What Changes

- Define one managed root concept: the project root folder selected by `--project-root`, Git-top-level discovery, or the current folder when Git is unavailable.
- Reject `--project-root` when it points inside a Git work tree but not at that work tree's top-level folder.
- Expose `project_git_mode` so templates can tell whether the resolved project root folder is backed by Git metadata.
- Keep `dest_folder` as the single canonical current-template path term.
- Define how omitted root and destination values are derived from the invocation folder:
  - the invocation folder is consulted only when `--project-root` or `--dest-folder` is omitted
  - in Git mode, the invocation folder yields both the Git top-level folder and the relative subfolder inside that Git work tree
  - if `--project-root` is omitted, the derived Git top-level folder becomes the project root folder
  - if `--dest-folder` is omitted, the derived relative subfolder becomes `dest_folder`
- Make project metadata fields runtime-derived instead of persisted in `.openplate.project.yaml`, including `project_folder_name`, `project_src_url`, `project_repo_org`, and `project_repo_name`.
- Add explicit Git repo metadata Liquid variables for project and template sources using `project_git_repo_*` and `template_git_repo_*` naming.
- Keep removed project Liquid variable names as deprecated compatibility aliases where they already existed, including `project_repo_org` and `project_repo_name`.
- Add scheme-specific Git URL variants so templates can choose the original sanitized URL, a canonical SSH form, or a canonical HTTPS form.
- Strip embedded user and password data from HTTPS Git URLs before exposing any runtime URL variable.
- Preserve template `?path=` and `#ref` semantics when exposing or converting full template source URLs.
- Leave `template_git_*` values empty when the template source is not a Git URL.
- Keep `project_src_url` as a runtime compatibility alias to the sanitized project Git repo URL, but stop persisting it in the project file.
- Populate `project_folder_name` from the resolved project root at runtime, using the Git repository name in Git mode when available, and stop persisting it in the project file.
- Add `docs/template-parameters.md` as the detailed template-parameter reference, and replace the inline built-in-parameters section in `docs/templates.md` with a meaningful link to that reference.
- **BREAKING** Rename the shared root-selection CLI option from `--project-folder` to `--project-root`.
- **BREAKING** Remove runtime support for populated `src_name`, `src_folder`, `template_src_folder`, `vcs_url`, and `template_prefix`; blank legacy values are ignored, populated legacy source values fail loudly, and legacy settings are ignored.
- Define deterministic template ref resolution, including alphabetical selection when multiple exact tags match the same commit.

## Capabilities

### New Capabilities
- `project-root-and-repo-metadata`: defines project root folder semantics, Git-mode-aware `dest_folder` resolution, runtime-only project metadata, and project or template Git repo metadata variables.

### Modified Capabilities
- `project-init-source-urls`: extend the URL-only source contract to persisted project template references and reject non-blank legacy name or folder source data at load time.
- `top-level-init-update-commands`: rename the shared root-selection option from `--project-folder` to `--project-root` across top-level and legacy command forms.
- `manual-tests-workflow`: update the documented coverage matrix and seeded cases for the renamed root option, Git-mode `dest_folder` behavior, project-file metadata omission, Git URL normalization, and legacy-source migration behavior.

## Impact

- Affected code: CLI argument parsing, project metadata resolution, Git helpers, template option compilation, project config loading and saving, and recursive init, update, and verify walkers.
- Affected user contracts: Liquid variable names, project root semantics, `dest_folder` resolution, `.openplate.project.yaml` persistence rules, and sanitized SSH or HTTPS Git URL behavior.
- Affected docs and tests: command docs, `docs/template-parameters.md`, `docs/templates.md`, README usage, manual test case 1 and case 4 guidance, and focused parser and runtime regressions for explicit invalid Git root overrides, project-file metadata omission, legacy field rejection, deprecated Liquid aliases, Git URL scrubbing and conversion, non-Git template-source behavior, and root or destination behavior.
