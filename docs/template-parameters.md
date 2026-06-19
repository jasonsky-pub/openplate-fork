# Template Parameters

This document is the reference for OpenPlate's built-in template variables.

## General Rules

- `dest_folder` is the canonical current-template path beneath the resolved project root.
- Project metadata that depends on the current filesystem root or current Git remote is derived at runtime and is not persisted in `.openplate.project.yaml`.
- When an HTTPS Git URL includes embedded credentials, OpenPlate strips the userinfo before exposing any runtime URL variable.
- Template Git variables are populated only when the current template source is a Git URL. For non-Git sources such as `file://...`, the `template_git_*` variables are empty.

## Project Root And Path Variables

| Variable | Meaning | Notes |
| --- | --- | --- |
| `dest_folder` | Resolved destination path for the current template instance beneath the project root | Explicit `--dest-folder` wins; otherwise it is derived from `--project-root`, Git invocation context, or `.`. |
| `project_git_mode` | Whether the resolved project root is inside a Git work tree | `true` inside Git, `false` otherwise. |
| `project_folder_name` | Folder-like project name for the resolved project root | Outside Git mode this is the resolved root folder name. In Git mode it is the parsed Git repository name when available, otherwise the resolved Git root folder name. |

Example:

```liquid
Project mode: {{ project_git_mode }}
Template lives under: {{ dest_folder }}
```

## Project Git Metadata

| Variable | Meaning |
| --- | --- |
| `project_git_repo_url` | Sanitized original project remote URL |
| `project_git_ssh_repo_url` | Canonical SSH form of the project remote |
| `project_git_https_repo_url` | Canonical HTTPS form of the project remote |
| `project_git_repo_org` | Parsed organization or owner name from the project remote |
| `project_git_repo_name` | Parsed repository name from the project remote |
| `project_src_url` | Compatibility alias for `project_git_repo_url` |

Behavior notes:

- If the project has no Git remote, all project Git URL variables are empty strings.
- For an HTTPS remote such as `https://user:pass@github.com/my-org/my-repo.git`, OpenPlate exposes `https://github.com/my-org/my-repo.git` and derives the SSH form `git@github.com:my-org/my-repo.git`.

Example:

```liquid
Repo URL: {{ project_git_repo_url }}
Clone over SSH: {{ project_git_ssh_repo_url }}
Owner: {{ project_git_repo_org }}
```

## Template Source Metadata

| Variable | Meaning |
| --- | --- |
| `template_src_url` | Sanitized original template source reference, including `?path=` and `#ref` when present |
| `template_git_ssh_src_url` | Template source reference rewritten to canonical SSH form while preserving `?path=` and `#ref` |
| `template_git_https_src_url` | Template source reference rewritten to canonical HTTPS form while preserving `?path=` and `#ref` |
| `template_git_repo_url` | Sanitized original template repository URL without `?path=` or `#ref` |
| `template_git_ssh_repo_url` | Canonical SSH repository URL without `?path=` or `#ref` |
| `template_git_https_repo_url` | Canonical HTTPS repository URL without `?path=` or `#ref` |
| `template_git_repo_org` | Parsed organization or owner name from the template repository URL |
| `template_git_repo_name` | Parsed repository name from the template repository URL |
| `template_git_repo_path` | Parsed template sub-folder from `?path=` | 
| `template_git_repo_ref` | Explicit `#ref`, or the resolved branch/tag/SHA when a Git source omits the ref and default branches are allowed |
| `template_version` | Template version currently tracked for the project template entry |

Behavior notes:

- `template_git_repo_path` is `.` when the template root is the repository root.
- When the template source is not a Git URL, `template_src_url` still reflects the original source reference, but all `template_git_*` variables are empty strings.

Example:

```liquid
Template source: {{ template_src_url }}
Sibling repo URL: {{ template_git_https_repo_url }}?path=workers/job#{{ template_git_repo_ref }}
```

## Stable Project Metadata

| Variable | Meaning |
| --- | --- |
| `project_guid1` | Stable project GUID generated on first write |
| `project_guid2` | Stable project GUID generated on first write |
| `project_guid3` | Stable project GUID generated on first write |
| `last_updater_email` | Git user email captured from the project root when available and when not running in automation mode |

## Deprecated Aliases

The following names remain supported for compatibility, but new templates should use the Git-scoped names instead.

| Deprecated name | Preferred name | Notes |
| --- | --- | --- |
| `project_repo_org` | `project_git_repo_org` | Same runtime value |
| `project_repo_name` | `project_git_repo_name` | Same runtime value |
| `project_src_url` | `project_git_repo_url` | Compatibility alias for the sanitized original project remote URL |

## Persistence Notes

These built-in values are runtime-derived and are not stored in `.openplate.project.yaml`:

- `project_folder_name`
- `project_src_url`
- `project_repo_org`
- `project_repo_name`
- `project_git_repo_url`
- `project_git_ssh_repo_url`
- `project_git_https_repo_url`
- `project_git_repo_org`
- `project_git_repo_name`

Older project files may still contain legacy copies of those values, but OpenPlate ignores them as authoritative input and removes them on the next write.