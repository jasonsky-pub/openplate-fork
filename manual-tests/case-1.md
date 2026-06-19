# Case 1: Config Persistence and URL-Source Init

## Purpose / Covered Commands

- `openplate --version`
- `openplate config set`
- `openplate config get`
- `openplate init` with `file://` sources, `?path=`, `#main`, `--project-root`, inferred Git-mode `dest_folder`, `--allow-default-branch`, `--dest-folder`, `--no-cache`, `--ignore`, rerun rejection, `--overwrite`, and `--ignore-tool-version`

Matrix facets covered by this case:

- `global --version`
- `global --config-file`
- `global --project-root`
- `global --ignore-tool-version`
- `config get`
- `config set --parameter-default add/remove`
- `config set --allow-template-commands`
- `config set` rejects removed `--vcs-url` and `--template-prefix`
- `init positional source URL`
- `init file:// transport`
- `init ?path= sub-folder selection`
- `init explicit #ref`
- `init invalid explicit Git subfolder root override`
- `init Git-mode default dest-folder inference`
- `init project-file runtime metadata omission`
- `init sanitized HTTPS project metadata`
- `init non-Git template metadata emptiness`
- `init --allow-default-branch`
- `init --dest-folder`
- `init --no-cache`
- `init --ignore`
- `init rerun rejection without --overwrite`
- `init --overwrite`

## Prerequisites

- Run from the repository root in `bash`.
- Ensure `bash`, `python`, and `git` are on `PATH`.
- Do not replace the checked-in fixture catalog with external or private templates.

## Exact Commands To Run

```bash
bash ./manual-tests/cleanup-manual-tests.sh case-1
bash ./manual-tests/run-manual-tests.sh case-1
```

## Expected Scripted Outputs

- [manual-tests/artifacts/case-1/01-version.log](manual-tests/artifacts/case-1/01-version.log) records the CLI version output.
- [manual-tests/artifacts/case-1/04-config-get.log](manual-tests/artifacts/case-1/04-config-get.log) shows the retained `service_name` default and `allow_template_commands: true` while omitting removed source-resolution settings.
- [manual-tests/artifacts/case-1/04b-config-set-legacy-source-settings-rejected.log](manual-tests/artifacts/case-1/04b-config-set-legacy-source-settings-rejected.log) records that `config set --vcs-url` and `config set --template-prefix` are rejected as unsupported arguments.
- [manual-tests/artifacts/case-1/summary.txt](manual-tests/artifacts/case-1/summary.txt) lists the materialized local catalog repo and the source URLs used.
- [manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml](manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml) contains `dest_folder: bootstrap/app` and `no_cache: true` while omitting runtime-derived project metadata fields.
- [manual-tests/work/case-1/bootstrap-project/scaffold/bootstrap/app/managed/service.txt](manual-tests/work/case-1/bootstrap-project/scaffold/bootstrap/app/managed/service.txt) contains the config-default service name, defaulted lifecycle values, and empty project-remote metadata because the explicit Git project root has no remote configured.
- [manual-tests/artifacts/case-1/06-init-rerun-rejected.log](manual-tests/artifacts/case-1/06-init-rerun-rejected.log) records the rejected second plain `init` run against the same tracked template and dest-folder.
- [manual-tests/artifacts/case-1/07-init-overwrite.log](manual-tests/artifacts/case-1/07-init-overwrite.log) records the accepted `init --overwrite` rerun against the same tracked template.
- [manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/managed/service.txt](manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/managed/service.txt) proves the branchless `file://` source worked with `--allow-default-branch`.
- [manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/notes/runbook.md](manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/notes/runbook.md) is intentionally absent because `--ignore` filtered it.
- [manual-tests/work/case-1/version-gated-project/gated/info.txt](manual-tests/work/case-1/version-gated-project/gated/info.txt) proves the version-gated fixture can be initialized only when `--ignore-tool-version` is supplied.
- [manual-tests/work/case-1/git-mode-project/scaffold/services/api/managed/service.txt](manual-tests/work/case-1/git-mode-project/scaffold/services/api/managed/service.txt) proves omitted `--dest-folder` resolves from the Git invocation subfolder and that HTTPS project remotes are sanitized while deprecated aliases still match the Git-scoped values.
- [manual-tests/artifacts/case-1/11-init-invalid-git-subroot.log](manual-tests/artifacts/case-1/11-init-invalid-git-subroot.log) records the explicit invalid Git subfolder `--project-root` rejection.

## Manual Validation Checklist

- Confirm the recorded source URLs in [manual-tests/artifacts/case-1/summary.txt](manual-tests/artifacts/case-1/summary.txt) are local `file://` URLs only.
- Confirm [manual-tests/work/case-1/openplate-config.yaml](manual-tests/work/case-1/openplate-config.yaml) and [manual-tests/artifacts/case-1/04-config-get.log](manual-tests/artifacts/case-1/04-config-get.log) omit `vcs_url` and `template_prefix` while retaining the parameter default and template-command setting.
- Confirm the bootstrap project created [manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt](manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt), showing the persisted `config set --allow-template-commands` setting took effect.
- Confirm the plain rerun log rejects the second `init` attempt for the same dest-folder and leaves the removed bootstrap files absent.
- Confirm the overwrite rerun restored the removed bootstrap files but did not recreate [manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt](manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt), demonstrating that `init --overwrite` skips init-command reruns.
- Confirm [manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml](manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml) and [manual-tests/work/case-1/git-mode-project/.openplate.project.yaml](manual-tests/work/case-1/git-mode-project/.openplate.project.yaml) still contain only tracked template state and omit runtime-derived project metadata fields.
- Confirm the default-branch project has no generated runbook file, and that the rest of the scaffold exists under the requested `bootstrap/app` or `branchless/app` dest-folder segments.
- Confirm the Git-mode project renders into [manual-tests/work/case-1/git-mode-project/scaffold/services/api](manual-tests/work/case-1/git-mode-project/scaffold/services/api), proving omitted `--dest-folder` defaulted from the invocation folder beneath the inferred Git root.
- Confirm [manual-tests/work/case-1/git-mode-project/scaffold/services/api/managed/service.txt](manual-tests/work/case-1/git-mode-project/scaffold/services/api/managed/service.txt) contains `project_src_url=https://github.com/manual-org/manual-service.git`, the corresponding SSH and HTTPS forms, and matching deprecated aliases without embedded credentials.
- Confirm [manual-tests/work/case-1/bootstrap-project/scaffold/bootstrap/app/managed/service.txt](manual-tests/work/case-1/bootstrap-project/scaffold/bootstrap/app/managed/service.txt) leaves all `template_git_*` variables empty for the local `file://` template source.
- Confirm [manual-tests/artifacts/case-1/11-init-invalid-git-subroot.log](manual-tests/artifacts/case-1/11-init-invalid-git-subroot.log) tells the operator that explicit project roots inside Git must use the Git top-level folder.
- Confirm no case output references network URLs, private repositories, or company-specific fixture names.

## Cleanup Notes

- The shared cleanup script removes only [manual-tests/work/case-1](manual-tests/work/case-1) and [manual-tests/artifacts/case-1](manual-tests/artifacts/case-1).