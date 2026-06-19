# Case 2: Interactive Init, Hidden Parameters, and Template Commands

## Purpose / Covered Commands

- `openplate init` interactive prompting
- Template-command authorization behavior
- Hidden parameter defaults and `--ask-hidden`
- `conditionally_hidden` behavior driven by earlier answers

Matrix facets covered by this case:

- `global --config-file`
- `global --project-folder`
- `global --ask-hidden`
- `config set --allow-template-commands`
- `init interactive prompting`
- `init template-command authorization guidance`
- `init hidden parameters`
- `init conditionally_hidden`

## Prerequisites

- Run from the repository root in `bash`.
- Ensure `bash`, `python`, and `git` are on `PATH`.

## Exact Commands To Run

```bash
bash ./manual-tests/cleanup-manual-tests.sh case-2
bash ./manual-tests/run-manual-tests.sh case-2
```

## Expected Scripted Outputs

- [manual-tests/artifacts/case-2/01-blocked-init-commands.log](manual-tests/artifacts/case-2/01-blocked-init-commands.log) contains the exact non-interactive safety guidance for template `init_commands` and exits with failure.
- [manual-tests/artifacts/case-2/02-config-allow-init-commands.log](manual-tests/artifacts/case-2/02-config-allow-init-commands.log) records the config toggle that permanently allows template commands for this case config file.
- [manual-tests/work/case-2/default-visibility-project/scaffold/interactive/default/managed/service.txt](manual-tests/work/case-2/default-visibility-project/scaffold/interactive/default/managed/service.txt) contains `deployment=lambda`, `instance=t3.small`, and `hidden=hidden-default`, proving hidden and conditionally hidden values fell back without prompting.
- [manual-tests/work/case-2/ask-hidden-project/scaffold/interactive/hidden/managed/service.txt](manual-tests/work/case-2/ask-hidden-project/scaffold/interactive/hidden/managed/service.txt) contains `deployment=ec2`, `instance=m5.large`, and `hidden=override-secret`, proving `--ask-hidden` exposed both the hidden parameter and the `conditionally_hidden` parameter once its condition evaluated to visible.

## Manual Validation Checklist

- Confirm the blocked init log recommends both the one-time `openplate init --allow-template-commands` override and the persistent `openplate config set --allow-template-commands` setting.
- Confirm both successful projects created [manual-tests/work/case-2/default-visibility-project/hooks/init-command.txt](manual-tests/work/case-2/default-visibility-project/hooks/init-command.txt) and [manual-tests/work/case-2/ask-hidden-project/hooks/init-command.txt](manual-tests/work/case-2/ask-hidden-project/hooks/init-command.txt).
- Confirm the default-visibility run never required an explicit `instance_type` or `hidden_token` answer, while the `--ask-hidden` run materialized the explicit values.

## Cleanup Notes

- The shared cleanup script removes only [manual-tests/work/case-2](manual-tests/work/case-2) and [manual-tests/artifacts/case-2](manual-tests/artifacts/case-2).