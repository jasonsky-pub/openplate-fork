## 1. Project Root And Source Foundations

- [x] 1.1 Add git and filesystem helper APIs for resolving `project_root_folder`, detecting `project_git_mode`, rejecting explicit Git subfolder root overrides, parsing SSH and HTTPS Git URLs, scrubbing HTTPS credentials, deriving alternate SSH and HTTPS forms, preserving `?path=` and `#ref` on converted source URLs, and resolving template refs with alphabetical exact-tag selection.
- [x] 1.2 Extend project configuration load and save behavior to use the resolved project root folder, stop persisting runtime-derived project metadata, ignore legacy persisted `project_folder_name`, `project_src_url`, `project_repo_org`, and `project_repo_name` values as authoritative input, and reject non-blank legacy `src_name`, `src_folder`, and `template_src_folder` values while ignoring blank legacy values.
- [x] 1.3 Remove runtime `vcs_url` and `template_prefix` support from settings load, config get or set flows, and any remaining source-resolution paths while preserving safe loading of old files that still contain those keys.

## 2. Rooted Runtime Behavior

- [x] 2.1 Replace the shared `--project-folder` CLI option with `--project-root` on top-level and legacy init, update, and verify commands, and make `--project-folder` fail with migration guidance.
- [x] 2.2 Resolve `project_root_folder` and resolved `dest_folder` before init, update, verify, and prompt flows using the Git-mode and non-Git-mode rules defined in the specs, including invocation-folder-derived defaults only when root or destination was omitted.
- [x] 2.3 Update recursive walkers, init-command working-directory rendering, update and verify path resolution, and prompt identity helpers so file operations anchor at `project_root_folder` while template instance output uses the resolved `dest_folder`.

## 3. Liquid Variables And Git Metadata

- [x] 3.1 Extend template option compilation to expose `project_git_mode`, the runtime-only project metadata fields, `project_git_repo_url`, `project_git_ssh_repo_url`, `project_git_https_repo_url`, deprecated compatibility aliases such as `project_repo_org` and `project_repo_name`, and the corresponding template-side source and repo URL families.
- [x] 3.2 Populate project Git variables from the resolved project root folder, supporting both SSH and HTTPS remote URLs, leaving project remote variables empty when no remote exists, sanitizing HTTPS credentials, and making `project_folder_name` resolve to the Git repository name in Git mode with a root-folder fallback.
- [x] 3.3 Populate template Git variables from parsed URL source references and checked-out template repos, including normalized template paths, deterministic ref selection, SSH and HTTPS Git URL parsing, source-URL suffix preservation, sanitized credentials, alternate SSH and HTTPS source and repo forms, and empty Git metadata for non-Git template sources.

## 4. Validation And Documentation

- [x] 4.1 Add or update focused automated tests for `--project-root`, explicit invalid Git subfolder root overrides, Git-mode `dest_folder` defaults, exact `--dest-folder` override behavior, project-file metadata omission, legacy source-field rejection, ignored legacy settings, project and template Git metadata values for both SSH and HTTPS URLs, HTTPS credential scrubbing, alternate SSH and HTTPS URL generation, template `?path=` and `#ref` preservation, empty template Git metadata for non-Git sources, and alphabetical exact-tag ref selection.
- [x] 4.2 Add `docs/template-parameters.md` as the detailed template-parameter reference, update `docs/templates.md` to link to it instead of carrying the inline built-in-parameters section, and document `project_root_folder`, `project_git_mode`, resolved `dest_folder`, runtime-only project metadata, deprecated aliases, and the new project or template Git URL families.
- [x] 4.3 Update manual test docs, fixtures, and expected outputs for Case 1 and Case 4 so the coverage matrix and end-to-end steps validate `--project-root`, invalid explicit Git subfolder roots, Git-mode `dest_folder` behavior, project-file metadata omission, SSH or HTTPS metadata handling, credential scrubbing, and legacy-source migration failures.
- [x] 4.4 Run the updated manual test workflow with the checked-in runner and relevant case documents before considering the apply complete, including Case 1 and Case 4 for this change and any additional case coverage needed by the touched runtime surfaces.
