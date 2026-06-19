## ADDED Requirements

### Requirement: OpenPlate resolves one project root folder and exposes Git mode
OpenPlate SHALL resolve one `project_root_folder` before performing init, update, verify, prompt export, or prompt import behavior.

The shared root-selection CLI option SHALL be named `--project-root`.

Project root resolution SHALL follow this precedence:
- if `--project-root` is supplied and its normalized absolute path is not inside a Git work tree, that path SHALL be the project root folder
- if `--project-root` is supplied and its normalized absolute path is inside a Git work tree and equals that work tree's top-level folder, that path SHALL be the project root folder
- if `--project-root` is supplied and its normalized absolute path is inside a Git work tree but does not equal that work tree's top-level folder, OpenPlate SHALL halt with an error explaining that explicit project roots inside Git must use the Git top-level folder
- otherwise, if the invocation folder is inside a Git work tree, the Git top-level folder SHALL be the project root folder
- otherwise, the invocation folder SHALL be the project root folder

When `--project-root` or `--dest-folder` is omitted and the invocation folder is inside a Git work tree, OpenPlate SHALL derive these values from the invocation folder:
- the Git top-level folder
- the normalized relative path from that Git top-level folder to the invocation folder

The derived Git top-level folder SHALL only be used to fill an omitted `project_root_folder`.

The derived invocation-relative path SHALL only be used to fill an omitted `dest_folder`.

OpenPlate SHALL expose `project_git_mode` to Liquid evaluation. `project_git_mode` SHALL be `true` when `project_root_folder` is inside a Git work tree and `false` otherwise.

OpenPlate SHALL anchor `.openplate.project.yaml`, project-level file operations, and project-level command working directories at the resolved project root folder.

#### Scenario: Git top-level becomes the project root folder
- **WHEN** a user runs `openplate init https://example.com/template.git#main` from a sub-folder inside a Git work tree
- **THEN** OpenPlate resolves the Git top-level folder as `project_root_folder`
- **THEN** `project_git_mode` is `true`

#### Scenario: Non-git invocation becomes the project root folder
- **WHEN** a user runs `openplate init https://example.com/template.git#main` from a folder that is not inside a Git work tree
- **THEN** OpenPlate resolves the invocation folder as `project_root_folder`
- **THEN** `project_git_mode` is `false`

#### Scenario: Explicit project root override wins
- **WHEN** a user runs `openplate init --project-root ./workspace https://example.com/template.git#main`
- **THEN** OpenPlate uses `workspace` as `project_root_folder`
- **THEN** OpenPlate does not infer the root from the invocation folder or Git top-level folder

#### Scenario: Explicit git top-level project root override is accepted
- **WHEN** a user runs `openplate init --project-root ./repo git@github.com:my-org/template-catalog.git#main`
- **AND** `./repo` is the Git top-level folder of that work tree
- **THEN** OpenPlate uses `./repo` as `project_root_folder`

#### Scenario: Explicit git subfolder project root override is rejected
- **WHEN** a user runs `openplate init --project-root ./repo/services/api git@github.com:my-org/template-catalog.git#main`
- **AND** `./repo/services/api` is inside a Git work tree rooted at `./repo`
- **THEN** OpenPlate halts with an error explaining that explicit project roots inside Git must use `./repo`

### Requirement: OpenPlate resolves dest_folder consistently
`dest_folder` SHALL remain the canonical current-template path concept.

Resolved `dest_folder` SHALL follow these rules:
- when `--dest-folder` is supplied, OpenPlate SHALL use that normalized value as the exact resolved `dest_folder` regardless of Git mode or invocation folder
- when `--project-root` is supplied explicitly and `--dest-folder` is omitted, OpenPlate SHALL resolve `dest_folder` to `.`
- when `--project-root` is omitted and the invocation folder is inside a Git work tree, OpenPlate SHALL resolve an omitted `dest_folder` to the normalized relative path from the inferred `project_root_folder` to the invocation folder
- when `--project-root` is omitted and the invocation folder is not inside a Git work tree, OpenPlate SHALL resolve an omitted `dest_folder` to `.`

The resolved `dest_folder` SHALL be the value exposed to Liquid for the current template instance and the value used to locate managed template output beneath `project_root_folder`.

#### Scenario: Git subfolder without dest-folder uses the invocation-relative path
- **WHEN** a user runs OpenPlate from `repo/services/api` inside a Git work tree rooted at `repo`
- **AND** the user does not supply `--dest-folder`
- **THEN** OpenPlate resolves `dest_folder` to `services/api`

#### Scenario: Git subfolder with dest-folder uses the explicit path
- **WHEN** a user runs OpenPlate from `repo/services/api` inside a Git work tree rooted at `repo`
- **AND** the user supplies `--dest-folder worker`
- **THEN** OpenPlate resolves `dest_folder` to `worker`
- **THEN** OpenPlate does not prepend `services/api`

#### Scenario: Non-git invocation defaults dest-folder to root
- **WHEN** a user runs OpenPlate from a folder that is not inside a Git work tree and does not supply `--dest-folder`
- **THEN** OpenPlate resolves `dest_folder` to `.`

#### Scenario: Explicit project root with no dest-folder uses root
- **WHEN** a user runs OpenPlate with `--project-root ./workspace` and does not supply `--dest-folder`
- **THEN** OpenPlate resolves `dest_folder` to `.`

### Requirement: Runtime-derived project metadata is not persisted in the project file
OpenPlate SHALL derive project metadata that depends on the current project root or current Git remote at runtime rather than storing it in `.openplate.project.yaml`.

At minimum, OpenPlate SHALL NOT persist these fields in `.openplate.project.yaml`:
- `project_folder_name`
- `project_src_url`
- `project_repo_org`
- `project_repo_name`
- `project_git_repo_url`
- `project_git_ssh_repo_url`
- `project_git_https_repo_url`
- `project_git_repo_org`
- `project_git_repo_name`

If older project files still contain those fields, OpenPlate SHALL ignore them as authoritative input and SHALL omit them the next time the project file is written.

#### Scenario: Legacy project metadata fields are ignored on load
- **WHEN** `.openplate.project.yaml` contains `project_folder_name`, `project_src_url`, `project_repo_org`, or `project_repo_name`
- **THEN** OpenPlate does not treat those fields as authoritative runtime input

#### Scenario: Legacy project metadata fields are removed on write
- **WHEN** OpenPlate rewrites a project file after init or update
- **THEN** `.openplate.project.yaml` does not contain runtime-derived project metadata snapshot fields

### Requirement: OpenPlate exposes project Git repository metadata variables
OpenPlate SHALL expose these project-scoped Liquid variables:
- `project_git_mode`
- `project_folder_name`
- `project_src_url`
- `project_git_repo_url`
- `project_git_ssh_repo_url`
- `project_git_https_repo_url`
- `project_git_repo_org`
- `project_git_repo_name`
- `project_repo_org`
- `project_repo_name`

`project_folder_name` SHALL always be populated from the resolved project root at runtime. When `project_git_mode` is `false`, `project_folder_name` SHALL equal the resolved project root folder name. When `project_git_mode` is `true`, `project_folder_name` SHALL equal the parsed Git repository name when one is available and SHALL otherwise fall back to the resolved Git root folder name.

`project_src_url` SHALL remain the runtime compatibility alias for the sanitized original project Git repo URL.

If the project remote URL is an HTTPS URL containing embedded username or password data, OpenPlate SHALL strip that userinfo before exposing `project_src_url`, `project_git_repo_url`, `project_git_https_repo_url`, `project_git_ssh_repo_url`, `project_git_repo_org`, or `project_git_repo_name`.

`project_git_repo_url` SHALL equal the sanitized original project remote URL when one is available.

`project_git_ssh_repo_url` SHALL equal the canonical SSH form of the sanitized project remote URL when the remote can be normalized to a supported SSH form.

`project_git_https_repo_url` SHALL equal the canonical HTTPS form of the sanitized project remote URL when the remote can be normalized to a supported HTTPS form.

`project_git_repo_org` and `project_git_repo_name` SHALL be derived from the sanitized project remote URL when they are parseable and SHALL be empty strings otherwise.

`project_repo_org` and `project_repo_name` SHALL remain available as deprecated compatibility aliases and SHALL equal `project_git_repo_org` and `project_git_repo_name` respectively.

When no project remote URL is available, `project_src_url`, `project_git_repo_url`, `project_git_ssh_repo_url`, `project_git_https_repo_url`, `project_git_repo_org`, and `project_git_repo_name` SHALL all be empty strings.

OpenPlate SHALL NOT expose a project-level Git ref variable as part of this change.

#### Scenario: Project HTTPS remote is sanitized and expanded into URL variants
- **WHEN** `project_root_folder` is inside a Git work tree with remote `origin` URL `https://user:pass@github.com/my-org/my-repo.git`
- **THEN** `project_src_url` is `https://github.com/my-org/my-repo.git`
- **THEN** `project_git_repo_url` is `https://github.com/my-org/my-repo.git`
- **THEN** `project_git_https_repo_url` is `https://github.com/my-org/my-repo.git`
- **THEN** `project_git_ssh_repo_url` is `git@github.com:my-org/my-repo.git`
- **THEN** `project_git_repo_org` is `my-org`
- **THEN** `project_git_repo_name` is `my-repo`

#### Scenario: Project SSH remote is expanded into URL variants
- **WHEN** `project_root_folder` is inside a Git work tree with remote `origin` URL `git@github.com:my-org/my-repo.git`
- **THEN** `project_src_url` is `git@github.com:my-org/my-repo.git`
- **THEN** `project_git_repo_url` is `git@github.com:my-org/my-repo.git`
- **THEN** `project_git_https_repo_url` is `https://github.com/my-org/my-repo.git`
- **THEN** `project_git_ssh_repo_url` is `git@github.com:my-org/my-repo.git`
- **THEN** `project_git_repo_org` is `my-org`
- **THEN** `project_git_repo_name` is `my-repo`

#### Scenario: Project Git metadata is empty without a remote
- **WHEN** `project_root_folder` is outside Git or inside Git without a configured remote URL
- **THEN** `project_src_url` is empty
- **THEN** `project_git_repo_url` is empty
- **THEN** `project_git_ssh_repo_url` is empty
- **THEN** `project_git_https_repo_url` is empty
- **THEN** `project_git_repo_org` is empty
- **THEN** `project_git_repo_name` is empty

#### Scenario: Deprecated project aliases match the Git-scoped values
- **WHEN** a project remote URL resolves to org `my-org` and repo `my-repo`
- **THEN** `project_repo_org` equals `project_git_repo_org`
- **THEN** `project_repo_name` equals `project_git_repo_name`

### Requirement: OpenPlate exposes template Git repository metadata variables
OpenPlate SHALL expose these template-scoped Liquid variables for the current template source:
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

`template_src_url` SHALL preserve the full original template source reference, including `?path=` and `#<ref>` when present.

If the underlying template repository URL is an HTTPS URL containing embedded username or password data, OpenPlate SHALL strip that userinfo before exposing `template_src_url`, `template_git_ssh_src_url`, `template_git_https_src_url`, `template_git_repo_url`, `template_git_ssh_repo_url`, `template_git_https_repo_url`, `template_git_repo_org`, `template_git_repo_name`, `template_git_repo_path`, or `template_git_repo_ref`.

`template_git_ssh_src_url` and `template_git_https_src_url` SHALL preserve the same `?path=` and `#<ref>` suffix as `template_src_url` while converting the repository location to the corresponding SSH or HTTPS form.

`template_git_repo_url` SHALL expose the sanitized original repository location with any `?path=` and `#<ref>` fragments removed.

`template_git_ssh_repo_url` and `template_git_https_repo_url` SHALL expose the corresponding SSH and HTTPS repository locations with `?path=` and `#<ref>` fragments removed.

`template_git_repo_path` SHALL expose the normalized repo-relative template path from `?path=`. When the template root is the repository root, `template_git_repo_path` SHALL be `.`.

`template_git_repo_ref` SHALL expose the explicit `#<ref>` value when one was provided. When a template source is allowed to omit an explicit ref, OpenPlate SHALL resolve `template_git_repo_ref` from the checked-out template repository using this precedence:
- current branch name when `HEAD` is attached to a branch
- otherwise, exact-match tags for `HEAD`, sorted alphabetically and selecting the first tag in that sorted list
- otherwise, the short `HEAD` SHA

`template_git_repo_org` and `template_git_repo_name` SHALL be derived from the sanitized template repository location when they are parseable and SHALL be empty strings otherwise.

When the current template source is not a Git URL, `template_git_ssh_src_url`, `template_git_https_src_url`, `template_git_repo_url`, `template_git_ssh_repo_url`, `template_git_https_repo_url`, `template_git_repo_org`, `template_git_repo_name`, `template_git_repo_path`, and `template_git_repo_ref` SHALL all be empty strings.

#### Scenario: Template HTTPS source is sanitized and preserves path and ref across variants
- **WHEN** a template source reference is `https://user:pass@github.com/my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_src_url` is `https://github.com/my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_git_https_src_url` is `https://github.com/my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_git_ssh_src_url` is `git@github.com:my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_git_repo_url` is `https://github.com/my-org/template-catalog.git`
- **THEN** `template_git_https_repo_url` is `https://github.com/my-org/template-catalog.git`
- **THEN** `template_git_ssh_repo_url` is `git@github.com:my-org/template-catalog.git`
- **THEN** `template_git_repo_org` is `my-org`
- **THEN** `template_git_repo_name` is `template-catalog`
- **THEN** `template_git_repo_path` is `python/api`
- **THEN** `template_git_repo_ref` is `v1`

#### Scenario: Template SSH source is expanded into URL variants
- **WHEN** a template source reference is `git@github.com:my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_src_url` is `git@github.com:my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_git_https_src_url` is `https://github.com/my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_git_ssh_src_url` is `git@github.com:my-org/template-catalog.git?path=python/api#v1`
- **THEN** `template_git_repo_url` is `git@github.com:my-org/template-catalog.git`
- **THEN** `template_git_https_repo_url` is `https://github.com/my-org/template-catalog.git`
- **THEN** `template_git_ssh_repo_url` is `git@github.com:my-org/template-catalog.git`
- **THEN** `template_git_repo_org` is `my-org`
- **THEN** `template_git_repo_name` is `template-catalog`
- **THEN** `template_git_repo_path` is `python/api`
- **THEN** `template_git_repo_ref` is `v1`

#### Scenario: Non-git template sources leave template Git metadata empty
- **WHEN** a template source reference is `file:///c:/templates/python-api`
- **THEN** `template_src_url` is `file:///c:/templates/python-api`
- **THEN** `template_git_ssh_src_url` is empty
- **THEN** `template_git_https_src_url` is empty
- **THEN** `template_git_repo_url` is empty
- **THEN** `template_git_ssh_repo_url` is empty
- **THEN** `template_git_https_repo_url` is empty
- **THEN** `template_git_repo_org` is empty
- **THEN** `template_git_repo_name` is empty
- **THEN** `template_git_repo_path` is empty
- **THEN** `template_git_repo_ref` is empty

#### Scenario: Multiple exact tags are resolved alphabetically for template ref
- **WHEN** a template repository is checked out without an explicit ref and the current commit has exact tags `v2` and `release-1`
- **THEN** OpenPlate sorts the exact tag names alphabetically
- **THEN** `template_git_repo_ref` is `release-1`

#### Scenario: Sibling template URL can reuse same repo metadata in either scheme
- **WHEN** a template declares a sibling URL using `{{ template_git_https_repo_url }}?path=workers/job#{{ template_git_repo_ref }}`
- **THEN** OpenPlate resolves the sibling template URL using the current template repository metadata without hardcoding org or repo names

### Requirement: Template parameter documentation lives in a dedicated reference page
OpenPlate documentation SHALL provide `docs/template-parameters.md` as the detailed reference for built-in template variables and related parameter rules.

`docs/templates.md` SHALL link to `docs/template-parameters.md` from the Parameters section instead of carrying the inline built-in-parameters list.

`docs/template-parameters.md` SHALL document:
- each supported built-in template variable and when it is populated
- examples of typical usage
- Git URL sanitization and SSH or HTTPS variant rules
- runtime-only versus persisted behavior where it matters for template authors
- a deprecated section that lists retained compatibility aliases such as `project_repo_org` and `project_repo_name`

#### Scenario: Templates doc points to the dedicated parameter reference
- **WHEN** a user reads `docs/templates.md`
- **THEN** the Parameters section links to `docs/template-parameters.md` for the full built-in variable reference
- **THEN** `docs/templates.md` does not duplicate the inline built-in-parameters list

#### Scenario: Dedicated parameter reference documents deprecated aliases
- **WHEN** a user reads `docs/template-parameters.md`
- **THEN** the document includes a deprecated section for retained compatibility aliases
- **THEN** the document identifies the preferred replacement names for those aliases

### Requirement: OpenPlate anchors file operations at project_root_folder
OpenPlate SHALL treat `project_root_folder` as the filesystem root for template walking, init command working directories, update behavior, verify behavior, and prompt-related path identity.

The resolved `dest_folder` SHALL select where the current template instance lives beneath `project_root_folder`.

#### Scenario: Repo-root-owned files are created from a Git subfolder invocation
- **WHEN** a user runs OpenPlate from a subfolder inside a Git work tree
- **AND** a template materializes a file under `.github/workflows/ci.yml`
- **THEN** OpenPlate writes that file beneath `project_root_folder`
- **THEN** the file path is not incorrectly nested beneath the invocation folder

#### Scenario: Update and verify use project_root_folder plus dest_folder
- **WHEN** a tracked template instance has resolved `dest_folder` `services/api`
- **THEN** update and verify treat `services/api` as the template instance root beneath `project_root_folder`

### Requirement: Legacy template source fields fail loudly and legacy name-resolution settings are ignored
OpenPlate MUST NOT accept non-blank legacy template source fields in project configuration data.

When loading project configuration:
- blank or null `src_name`, `src_folder`, and `template_src_folder` values SHALL be ignored
- non-blank `src_name`, `src_folder`, and `template_src_folder` values SHALL halt the command with a runtime error that explains URL-backed template references are now required

When loading tool settings:
- `vcs_url` and `template_prefix` SHALL be ignored whether blank or populated
- those settings SHALL NOT participate in runtime source resolution
- those settings SHALL NOT appear in config get output or config set options after this change

#### Scenario: Blank legacy template source fields are ignored
- **WHEN** a project configuration contains `src_name`, `src_folder`, or `template_src_folder` with blank or null values
- **THEN** OpenPlate ignores those fields and continues loading the configuration

#### Scenario: Non-blank legacy src-name fails loudly
- **WHEN** a project configuration contains a non-empty `src_name`
- **THEN** OpenPlate halts with a runtime error explaining that explicit URL-backed template references are required

#### Scenario: Non-blank legacy folder source fails loudly
- **WHEN** a project configuration contains a non-empty `src_folder` or `template_src_folder`
- **THEN** OpenPlate halts with a runtime error explaining that explicit URL-backed template references are required

#### Scenario: Legacy name-resolution settings are ignored
- **WHEN** a settings file contains `vcs_url` or `template_prefix`
- **THEN** OpenPlate ignores those values
- **THEN** OpenPlate does not use them for runtime source resolution or config command output
