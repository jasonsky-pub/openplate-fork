# Case 4: Update and Verify Against Drift

## Purpose / Covered Commands

- `openplate update`
- `openplate update --update-missing`
- `openplate update --update-full`
- `openplate verify`

Matrix facets covered by this case:

- `global --config-file`
- `global --project-root`
- `global --ask-again`
- `global --automation`
- `init --allow-template-commands`
- `update`
- `update --update-missing`
- `update --update-full`
- `verify`

## Prerequisites

- Run from the repository root in `bash`.
- Ensure `bash`, `python`, and `git` are on `PATH`.

## Exact Commands To Run

```bash
bash ./manual-tests/cleanup-manual-tests.sh case-4
bash ./manual-tests/run-manual-tests.sh case-4
```

## Expected Scripted Outputs

- [manual-tests/artifacts/case-4/02-verify-before-update.log](manual-tests/artifacts/case-4/02-verify-before-update.log) shows the human-mode verify banner and exits non-zero after the script intentionally drifts a readonly file.
- [manual-tests/artifacts/case-4/03-update-missing.log](manual-tests/artifacts/case-4/03-update-missing.log) corresponds to an `--ask-again --update-missing` run that restores the deleted non-readonly runbook and repairs the readonly managed file without overwriting the drifted non-readonly overview document.
- [manual-tests/artifacts/case-4/04-update-full.log](manual-tests/artifacts/case-4/04-update-full.log) corresponds to the follow-up `--update-full` run that restores the non-readonly overview content.
- [manual-tests/artifacts/case-4/05-verify-after-update.log](manual-tests/artifacts/case-4/05-verify-after-update.log) ends with `Done!`.
- [manual-tests/artifacts/case-4/06-verify-automation.log](manual-tests/artifacts/case-4/06-verify-automation.log) is the automation-mode verify output and omits the human-mode banner.
- [manual-tests/work/case-4/update-project/.openplate.project.yaml](manual-tests/work/case-4/update-project/.openplate.project.yaml) omits runtime-derived project metadata fields after init and both update passes.
- [manual-tests/work/case-4/update-project/scaffold/update/app/managed/service.txt](manual-tests/work/case-4/update-project/scaffold/update/app/managed/service.txt) ends in the expected generated state.
- [manual-tests/work/case-4/update-project/scaffold/update/app/docs/update-demo-overview.md](manual-tests/work/case-4/update-project/scaffold/update/app/docs/update-demo-overview.md) contains the template content again only after `--update-full`.

## Manual Validation Checklist

- Confirm the first verify run failed only after the script introduced drift, not during the initial init.
- Confirm `--update-missing` restored the missing runbook while preserving the drifted non-readonly overview file.
- Confirm `--update-full` finally overwrote the drifted overview file.
- Confirm the automation verify log contains only the automation-readable output and not the human banner.
- Confirm [manual-tests/work/case-4/update-project/.openplate.project.yaml](manual-tests/work/case-4/update-project/.openplate.project.yaml) omits runtime-derived project metadata fields throughout the update flow.

## Cleanup Notes

- The shared cleanup script removes only [manual-tests/work/case-4](manual-tests/work/case-4) and [manual-tests/artifacts/case-4](manual-tests/artifacts/case-4).