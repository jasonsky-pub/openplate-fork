# Case 1: Config Persistence and URL-Source Init

## Purpose / Covered Commands

- `openplate --version`
- `openplate config set`
- `openplate config get`
- `openplate init` with `file://` sources, `?path=`, `#main`, `--allow-default-branch`, `--dest-folder`, `--no-cache`, `--ignore`, rerun rejection, `--overwrite`, and `--ignore-tool-version`

Matrix facets covered by this case:

- `global --version`
- `global --config-file`
- `global --project-folder`
- `global --ignore-tool-version`
- `config get`
- `config set --vcs-url`
- `config set --template-prefix`
- `config set --parameter-default add/remove`
- `config set --allow-template-commands`
- `init positional source URL`
- `init file:// transport`
- `init ?path= sub-folder selection`
- `init explicit #ref`
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
- [manual-tests/artifacts/case-1/04-config-get.log](manual-tests/artifacts/case-1/04-config-get.log) shows persisted `vcs_url`, `template_prefix`, and the retained `service_name` default while omitting the removed `owner_name` default.
- [manual-tests/artifacts/case-1/summary.txt](manual-tests/artifacts/case-1/summary.txt) lists the materialized local catalog repo and the source URLs used.
- [manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml](manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml) contains `dest_folder: bootstrap/app` and `no_cache: true`.
- [manual-tests/work/case-1/bootstrap-project/scaffold/bootstrap/app/managed/service.txt](manual-tests/work/case-1/bootstrap-project/scaffold/bootstrap/app/managed/service.txt) contains the config-default service name and defaulted lifecycle values.
- [manual-tests/artifacts/case-1/06-init-rerun-rejected.log](manual-tests/artifacts/case-1/06-init-rerun-rejected.log) records the rejected second plain `init` run against the same tracked template and dest-folder.
- [manual-tests/artifacts/case-1/07-init-overwrite.log](manual-tests/artifacts/case-1/07-init-overwrite.log) records the accepted `init --overwrite` rerun against the same tracked template.
- [manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/managed/service.txt](manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/managed/service.txt) proves the branchless `file://` source worked with `--allow-default-branch`.
- [manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/notes/runbook.md](manual-tests/work/case-1/default-branch-project/scaffold/branchless/app/notes/runbook.md) is intentionally absent because `--ignore` filtered it.
- [manual-tests/work/case-1/version-gated-project/gated/info.txt](manual-tests/work/case-1/version-gated-project/gated/info.txt) proves the version-gated fixture can be initialized only when `--ignore-tool-version` is supplied.

## Manual Validation Checklist

- Confirm the recorded source URLs in [manual-tests/artifacts/case-1/summary.txt](manual-tests/artifacts/case-1/summary.txt) are local `file://` URLs only.
- Confirm the bootstrap project created [manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt](manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt), showing the persisted `config set --allow-template-commands` setting took effect.
- Confirm the plain rerun log rejects the second `init` attempt for the same dest-folder and leaves the removed bootstrap files absent.
- Confirm the overwrite rerun restored the removed bootstrap files but did not recreate [manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt](manual-tests/work/case-1/bootstrap-project/hooks/init-command.txt), demonstrating that `init --overwrite` skips init-command reruns.
- Confirm [manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml](manual-tests/work/case-1/bootstrap-project/.openplate.project.yaml) still contains only one tracked template entry after the overwrite rerun.
- Confirm the default-branch project has no generated runbook file, and that the rest of the scaffold exists under the requested `bootstrap/app` or `branchless/app` dest-folder segments.
- Confirm no case output references network URLs, private repositories, or company-specific fixture names.

## Cleanup Notes

- The shared cleanup script removes only [manual-tests/work/case-1](manual-tests/work/case-1) and [manual-tests/artifacts/case-1](manual-tests/artifacts/case-1).