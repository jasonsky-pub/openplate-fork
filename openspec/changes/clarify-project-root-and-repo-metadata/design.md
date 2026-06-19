## Context

OpenPlate currently treats a selected project folder as both the filesystem root and the managed template destination, even though real behavior depends on three different inputs:

- the folder where the operator launched the command
- the root folder where project-level files should land
- the resolved destination path for the current template instance

That ambiguity is mostly hidden when the operator runs at the repo top level, but it breaks down when OpenPlate is launched from a Git subfolder and the template needs to manage repo-root-owned content such as `.github/`.

The runtime also persists project metadata snapshots into `.openplate.project.yaml` even though those values are recalculated before the current Liquid-rendering paths use them, and Git URL handling is incomplete: SSH and HTTPS forms are not normalized together, HTTPS credentials are not scrubbed, and template `?path=` and `#ref` semantics are not represented alongside converted URL forms.

## Goals / Non-Goals

**Goals:**
- Define one canonical filesystem root term: `project_root_folder`.
- Define one canonical current-template path term: `dest_folder`.
- Expose project Git mode and explicit Git repo metadata variables for project and template sources.
- Preserve previously available project Liquid variable names as deprecated aliases when they already have template-facing usage.
- Make `--dest-folder` semantics simple and deterministic in Git and non-Git modes.
- Reject explicit nested Git subfolder roots so OpenPlate does not need to track a second explicit relative path inside a Git repository.
- Stop persisting runtime-derived project metadata in `.openplate.project.yaml`.
- Expose sanitized original, SSH, and HTTPS Git URL variants while preserving template source `?path=` and `#ref` semantics.
- Move built-in template-parameter documentation into a dedicated reference page.

**Non-Goals:**
- Introduce a second canonical path term alongside `dest_folder`.
- Add a project-level Git ref variable.
- Preserve backward compatibility for populated `src_name`, `src_folder`, or `template_src_folder` data.
- Preserve embedded usernames or passwords from HTTPS Git URLs in runtime variables.

## Decisions

### 1. Use `project_root_folder` as the single filesystem root concept

OpenPlate resolves one project root folder before file operations, metadata resolution, prompt handling, update, or verify logic runs.

- The CLI option is renamed from `--project-folder` to `--project-root`.
- If `--project-root` is supplied and the resolved path is not inside Git, OpenPlate uses that path as the root.
- If `--project-root` is supplied and the resolved path is inside Git, that path must equal the Git top-level folder; otherwise OpenPlate fails with a usage error.
- Otherwise, if the invocation folder is inside a Git work tree, OpenPlate uses the Git top-level folder.
- Otherwise, OpenPlate uses the invocation folder.

The invocation folder is only consulted when `--project-root` or `--dest-folder` is omitted. When the invocation folder is inside Git, OpenPlate derives two values from it:

- the Git top-level folder
- the normalized relative path from the Git top-level folder to the invocation folder

This makes Git only a mode that influences root discovery and metadata availability, not a second root concept.

### 2. Keep `dest_folder` as the canonical current-template path

Do not introduce a separate `project_repo_path` model term. The canonical path under the project root remains `dest_folder`.

The resolved `dest_folder` rules are:

- If `--dest-folder` is supplied, it becomes the exact normalized `dest_folder` regardless of Git mode or invocation folder.
- If `--project-root` is supplied explicitly, omitted `--dest-folder` resolves to `.` because the explicit root override chooses the managed root directly.
- If `--project-root` is omitted and the invocation folder is inside Git, omitted `--dest-folder` resolves to the normalized relative path derived from the invocation folder.
- If `--project-root` is omitted and Git metadata is unavailable, omitted `--dest-folder` resolves to `.`.

This removes relative-path composition surprises while still making Git subfolder invocation useful by default, and it avoids tracking a second explicit nested project-root path inside Git.

### 3. Keep project metadata runtime-derived instead of persisting it

`project_folder_name`, `project_src_url`, `project_repo_org`, and `project_repo_name` are currently stored in `.openplate.project.yaml`, but the runtime already recalculates them from the resolved project root before the current Liquid-rendering paths use them.

After this change:

- project metadata that depends on the current project root or current Git remote is derived at runtime
- `.openplate.project.yaml` does not persist `project_folder_name`, `project_src_url`, `project_repo_org`, `project_repo_name`, or their new Git-scoped replacements
- older project files that still contain those fields are tolerated on read, ignored as authoritative input, and cleaned up on the next write

This keeps the project file focused on tracked template state rather than caching environment-derived metadata.

### 4. Expose explicit Git metadata variables and URL families

Project-scoped variables:

- `project_git_mode`
- `project_folder_name`
- `project_src_url`
- `project_git_repo_url`
- `project_git_ssh_repo_url`
- `project_git_https_repo_url`
- `project_git_repo_org`
- `project_git_repo_name`

Deprecated project-scoped aliases kept for compatibility:

- `project_repo_org` -> same value as `project_git_repo_org`
- `project_repo_name` -> same value as `project_git_repo_name`

Template-scoped variables:

- `template_src_url`
- `template_git_ssh_src_url`
- `template_git_https_src_url`
- `template_git_repo_url`
- `template_git_ssh_repo_url`
- `template_git_https_repo_url`
- `template_git_repo_org`
- `template_git_repo_name`
- `template_git_repo_path`
- `template_git_repo_ref`

Rules:

- `project_src_url` remains the runtime compatibility alias for `project_git_repo_url`.
- `project_repo_org` and `project_repo_name` remain available as deprecated aliases for the new Git-scoped names.
- `project_folder_name` always remains available as a folder-like project identifier. Outside Git mode it is the resolved project root folder name. In Git mode it uses the parsed Git repository name when available and otherwise falls back to the Git root folder name.
- Project Git URL parsing must work for common HTTPS and SSH Git remote URL forms.
- Template Git URL parsing must work for common HTTPS and SSH Git URL forms.
- If an HTTPS Git URL contains embedded userinfo, OpenPlate strips the username and password before exposing any runtime URL variable derived from it.
- `project_git_repo_url` is the sanitized original project remote URL.
- `project_git_ssh_repo_url` and `project_git_https_repo_url` are the canonical SSH and HTTPS equivalents of the same sanitized project remote.
- `template_src_url` preserves the full sanitized original template source reference, including `?path=` and `#ref` when present.
- `template_git_ssh_src_url` and `template_git_https_src_url` preserve that same `?path=` and `#ref` suffix while converting the base repository location.
- `template_git_repo_url` is the sanitized original template repository location with `?path=` and `#ref` removed.
- `template_git_ssh_repo_url` and `template_git_https_repo_url` are the canonical SSH and HTTPS equivalents of that repository location, also without `?path=` and `#ref`.
- `template_git_repo_path` and `template_git_repo_ref` continue to expose the parsed `?path=` and `#ref` semantics separately.
- When the current template source is not a Git URL, `template_git_ssh_src_url`, `template_git_https_src_url`, `template_git_repo_url`, `template_git_ssh_repo_url`, `template_git_https_repo_url`, `template_git_repo_org`, `template_git_repo_name`, `template_git_repo_path`, and `template_git_repo_ref` are empty.

Alternative rejected: keep only one URL variable and force templates to rewrite Git URLs or scrub credentials manually. That makes same-repo sibling composition and security-sensitive output harder than necessary.

### 5. Document template parameters in a dedicated reference page

Implementation should add `docs/template-parameters.md` as the detailed reference for built-in template variables and related parameter rules.

- `docs/templates.md` should stop carrying the inline built-in-parameters list.
- `docs/templates.md` should instead link meaningfully to `docs/template-parameters.md` from the Parameters section.
- `docs/template-parameters.md` should explain each supported built-in variable, when it is populated, examples of typical usage, scheme or sanitization rules for Git URL variables, and a deprecated section for retained compatibility aliases.

Alternative rejected: keep the entire built-in variable reference inline inside `docs/templates.md`. That scatters the parameter story and makes the new compatibility and URL-family rules harder to maintain.

### 6. Resolve template refs deterministically

There is no project-level Git ref variable in this design.

For template sources, `template_git_repo_ref` resolves in this order when the ref is not already explicit:

1. current branch name
2. exact tags pointing at `HEAD`, sorted alphabetically and selecting the first tag
3. short commit SHA

That preserves deterministic sibling-template reuse even in detached or multiply tagged states.

### 7. Remove legacy source forms and ignore dead settings

- Blank or null `src_name`, `src_folder`, and `template_src_folder` values are ignored on load.
- Non-blank legacy source-form values are runtime errors with migration guidance.
- `vcs_url` and `template_prefix` are ignored on settings load whether blank or populated.
- Config command surfaces and docs stop advertising those settings as supported.

Alternative rejected: silently preserve old conversion behavior. That hides broken project state.

## Risks / Trade-offs

- [Changed Git subfolder defaults] Running from a Git subfolder with no `--dest-folder` now intentionally targets that subfolder path. Mitigation: specify the rule explicitly in specs, docs, and manual tests.
- [Explicit nested Git roots now error] Existing ad hoc workflows that pointed `--project-root` at a Git subfolder will stop working. Mitigation: make the restriction explicit and keep the error message focused on using the Git top-level folder or a non-Git root.
- [Metadata no longer cached in project file] Old debugging habits may expect project metadata snapshots to remain visible in `.openplate.project.yaml`. Mitigation: derive the values consistently at runtime and remove them predictably on write.
- [Deprecated alias drift] Compatibility aliases can diverge from the preferred Git-scoped names if they are not documented and tested together. Mitigation: keep them as direct aliases and list them in a deprecated section of the parameter reference doc.
- [Credential scrubbing changes observed values] Users who relied on embedded credentials appearing in rendered outputs will see sanitized URLs instead. Mitigation: treat credentials in runtime variables as unsupported and document the sanitized behavior explicitly.
- [Prompt identity churn] Changing how resolved `dest_folder` is derived may affect prompt identity. Mitigation: cover resolved `dest_folder` behavior directly in prompt-related tests during implementation.

## Migration Plan

1. Add helpers for root discovery, explicit Git-top-level validation, Git-mode detection, remote lookup, SSH and HTTPS org or repo parsing, HTTPS credential scrubbing, source-URL suffix preservation, and deterministic template ref resolution.
2. Route init, update, verify, and prompt flows through resolved `project_root_folder` and resolved `dest_folder`.
3. Expose the new Git metadata variables and URL families, handle non-Git template sources as empty Git metadata, and adjust `project_folder_name` population.
4. Stop persisting runtime-derived project metadata and remove legacy metadata snapshots from `.openplate.project.yaml` on write.
5. Remove runtime support for populated legacy source fields and stop using legacy name-resolution settings.
6. Update command docs, README examples, `docs/templates.md`, `docs/template-parameters.md`, and manual tests for `--project-root`, the new Git-mode `dest_folder` rules, deprecated aliases, project-file metadata omission, and sanitized SSH or HTTPS metadata examples.

## Open Questions

None. The remaining work is to encode the chosen naming and path rules consistently.
