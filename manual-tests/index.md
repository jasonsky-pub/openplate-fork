# Manual Tests

This folder is the repo-owned source of truth for end-to-end manual execution of OpenPlate. It keeps the checked-in fixtures, exact runner entrypoints, case documents, and the current coverage matrix for the visible CLI surface.

## Prerequisites

- Run from the repository root in `bash`.
- Ensure `bash`, `python`, and `git` are on `PATH`.
- Use only the checked-in fixture catalog under [manual-tests/templates](manual-tests/templates).
- Treat [manual-tests/work](manual-tests/work) and [manual-tests/artifacts](manual-tests/artifacts) as disposable state. They are intentionally gitignored except for the placeholder files.

## Shared Entry Points

- Run one case: `bash ./manual-tests/run-manual-tests.sh case-1`
- Run the full seeded suite: `bash ./manual-tests/run-manual-tests.sh all`
- Clean one case: `bash ./manual-tests/cleanup-manual-tests.sh case-1`
- Clean all generated state: `bash ./manual-tests/cleanup-manual-tests.sh all`

The bash runner materializes local git-backed template repositories from the checked-in fixture directories, then executes OpenPlate only against local `file://` sources. No case depends on network access or private infrastructure.

## Workspace Conventions

- Checked-in fixture inputs live under [manual-tests/templates](manual-tests/templates).
- Generated local git repos, initialized projects, and mutated workspaces live under [manual-tests/work/<case-id>](manual-tests/work).
- Captured logs, prompt JSON files, and per-case summaries live under [manual-tests/artifacts/<case-id>](manual-tests/artifacts).
- Each case is independent. The runner bootstraps a fresh local catalog repo per case.

## Case Inventory

| Case | Operator workflow | Primary commands | Case document |
| --- | --- | --- | --- |
| `case-1` | Configure a local environment and initialize from URL-based local catalog sources | `--version`, `config set`, `config get`, `init` | [manual-tests/case-1.md](manual-tests/case-1.md) |
| `case-2` | Exercise prompt-driven init behavior and template-command safety gates | `init`, `config set --allow-template-commands`, `--ask-hidden` | [manual-tests/case-2.md](manual-tests/case-2.md) |
| `case-3` | Export prompt JSON, mutate only the answers that matter, and import via file and stdin | `project print-init-json`, `init --prompts-json-file`, `init --prompts-json-stdin` | [manual-tests/case-3.md](manual-tests/case-3.md) |
| `case-4` | Create drift, repair it with update modes, and verify the final state | `update`, `project verify` | [manual-tests/case-4.md](manual-tests/case-4.md) |

## Coverage Matrix

The matrix below accounts for the current visible CLI surface from [docs/commands.md](docs/commands.md), [readme.md](readme.md), and [src/openplate/__main__.py](src/openplate/__main__.py).

| Facet | Classification | Rationale |
| --- | --- | --- |
| Global `--version` | `manual:case-1` | The runner records CLI version output before any case-specific setup. |
| Global `--config-file` | `manual:case-1` | Every case uses a case-local config file so global settings stay isolated. |
| Global `--project-root` | `manual:case-1` | The runner uses explicit project roots for init, update, and verify, and Case 1 also validates the Git-top-level restriction for explicit roots. |
| Global `--ask-hidden` | `manual:case-2` | Case 2 compares default hidden behavior with an explicit `--ask-hidden` run. |
| Global `--ask-again` | `manual:case-4` | Case 4 reruns update with `--ask-again` to force parameter prompting during maintenance. |
| Global `--ignore-tool-version` | `manual:case-1` | Case 1 initializes a fixture that requires `--ignore-tool-version` to bypass a synthetic tool gate. |
| Global `--debug` | `manual:case-3` | Case 3 enables debug logging on file import so ignored-node and unused-answer warnings are captured. |
| Global `--automation` | `manual:case-4` | Case 4 runs `project verify` in automation mode after repair and validates the machine-readable output shape. |
| `config get` | `manual:case-1` | Case 1 captures config output and validates that removed source-resolution settings are omitted. |
| `config set` removed source-resolution settings | `manual:case-1` | Case 1 explicitly proves `--vcs-url` and `--template-prefix` are rejected. |
| `config set --parameter-default` add | `manual:case-1` | Case 1 adds a `service_name` default and uses it during init. |
| `config set --parameter-default` remove | `manual:case-1` | Case 1 removes an `owner_name` default and validates that it disappears from config output. |
| `config set --allow-template-commands` | `manual:case-2` | Case 2 toggles the persistent template-command setting after first showing the blocked behavior. |
| Project-file omission of runtime-derived project metadata | `manual:case-1` | Case 1 and Case 4 validate that project config writes omit runtime-only project metadata fields. |
| `init` top-level command | `manual:case-1` | Case 1 uses the documented top-level init entrypoint throughout. |
| `init` positional source URL | `manual:case-1` | All init runs use the positional source form. |
| `init` `file://` transport | `manual:case-1` | The full seeded suite uses only local file-backed git repos. |
| `init` HTTPS transport syntax | `excluded` | Repo-owned manual cases are intentionally offline and local-only. Network template URLs stay documented but are not fetched here. |
| `init` SSH/scp transport syntax | `excluded` | Repo-owned manual cases are intentionally offline and local-only. Network URL syntax stays documented but not executed here. |
| Sanitized HTTPS project metadata | `manual:case-1` | Case 1 seeds a local Git project root with an HTTPS remote containing credentials and validates the sanitized runtime values and alternate SSH form. |
| `init` `?path=` template sub-folder selection | `manual:case-1` | Case 1 selects templates from a local catalog repo by sub-folder. |
| `init` explicit `#branch-or-tag` ref | `manual:case-1` | Case 1 uses `#main` on local catalog sources. |
| Preserved template `#ref` semantics | `manual:case-1` | Case 1 validates that the rendered template source reference still includes the explicit `#main` suffix. |
| Non-Git template URL metadata emptiness | `manual:case-1` | Case 1 validates that local `file://` template sources leave all `template_git_*` values empty. |
| Deprecated Liquid alias availability | `manual:case-1` | Case 1 validates that `project_repo_org` and `project_repo_name` still mirror the new Git-scoped values. |
| `init --allow-default-branch` | `manual:case-1` | Case 1 initializes a branchless local source successfully only when the flag is supplied. |
| Invalid explicit Git subfolder `--project-root` handling | `manual:case-1` | Case 1 asserts the focused migration error for explicit project roots that point at a Git subfolder rather than the Git top-level folder. |
| Git-mode default `dest_folder` resolution | `manual:case-1` | Case 1 runs init from a Git subfolder without `--dest-folder` and validates output under the invocation-relative path. |
| `init --dest-folder` | `manual:case-1` | Case 1 and Case 3 both materialize generated files under dest-folder-dependent scaffold segments. |
| `init --no-cache` | `manual:case-1` | Case 1 validates `no_cache: true` in the generated project config. |
| `init --ignore` | `manual:case-1` | Case 1 filters the runbook file and validates that it is absent. |
| `init --overwrite` | `manual:case-1` | Case 1 first proves a plain rerun of init is rejected for the same tracked template and dest-folder, then reruns with overwrite to verify files are restored, init commands do not rerun, and the project config does not gain a duplicate template entry. |
| `init --allow-template-commands` | `manual:case-4` | Case 4 uses the one-time override on init, while Case 2 covers the persistent config toggle. |
| `init hidden prompts` | `manual:case-2` | Case 2 validates hidden fallback and `--ask-hidden` behavior directly. |
| `init conditionally_hidden` | `manual:case-2` | Case 2 demonstrates the parameter becoming visible only after the controlling answer changes. |
| `init -r/--url` legacy alias | `automated-only` | Compatibility syntax remains covered by focused parser/runtime tests instead of manual cases. |
| `project print-init-json` compact export | `manual:case-3` | Case 3 captures the compact JSON artifact. |
| `project print-init-json --verbose` | `manual:case-3` | Case 3 captures and validates the verbose JSON artifact. |
| Prompt JSON file import | `manual:case-3` | Case 3 imports prompt data from a generated file artifact. |
| Prompt JSON stdin import | `manual:case-3` | Case 3 imports prompt data by piping a JSON document to stdin. |
| Prompt JSON hidden-scope behavior | `manual:case-3` | Case 3 contrasts non-hidden compact export with hidden-aware verbose export and import. |
| Prompt JSON dest-folder-independent node identity | `manual:case-3` | Case 3 exports from `.` and imports into a different init dest-folder while keeping the same node IDs. |
| Prompt JSON ignored extra nodes | `manual:case-3` | Case 3 injects an unmatched prompt node and validates the warning. |
| Prompt JSON ignored extra answers | `manual:case-3` | Case 3 injects an unused answer on a matched node and validates the warning. |
| Prompt JSON on `update` | `automated-only` | The CLI intentionally rejects removed prompt JSON flags on update, and focused parser tests already cover that contract. |
| `update` top-level command | `manual:case-4` | Case 4 uses the documented top-level update entrypoint. |
| `update --update-missing` | `manual:case-4` | Case 4 restores a deleted non-readonly file with this mode. |
| `update --update-full` | `manual:case-4` | Case 4 overwrites a drifted non-readonly file with this mode. |
| `project verify` | `manual:case-4` | Case 4 validates both failing and passing verify runs. |
| Legacy `project init` command path | `automated-only` | Compatibility entrypoints remain covered by focused parser/runtime tests. |
| Legacy `project update` command path | `automated-only` | Compatibility entrypoints remain covered by focused parser/runtime tests. |
| Removed `--project-folder` parser behavior | `automated-only` | Focused parser tests cover the rejection message for the renamed root flag. |
| Legacy or removed init flags such as `-n/--name` and `-f/--folder` | `automated-only` | Rejection behavior is a parser contract that is already covered by targeted tests. |
| Removed init print flag and removed update prompt JSON flags | `automated-only` | Rejection behavior is covered by targeted parser tests and is not a meaningful manual operator workflow. |

## Case Order

- Run [manual-tests/case-1.md](manual-tests/case-1.md) first when you need a quick confidence pass on config and source resolution.
- Run [manual-tests/case-2.md](manual-tests/case-2.md) when changing prompt logic, hidden behavior, or template-command safety behavior.
- Run [manual-tests/case-3.md](manual-tests/case-3.md) when changing prompt JSON export, import, sibling discovery, or node identity behavior.
- Run [manual-tests/case-4.md](manual-tests/case-4.md) when changing update or verify walkers.

## Public-Safety Rules

- Do not replace the checked-in fixtures with internal or company-specific templates.
- Do not point the runner at external repositories for baseline execution.
- Keep fixture names, placeholder values, and generated summaries generic.