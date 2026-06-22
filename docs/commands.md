# openplate

## Command: config get

Set configuration for the tool (available in ~/.openplate)

```
openplate config get
```

## Command: config set

Set configuration for the tool (available in ~/.openplate)

```
openplate config set --parameter-default service_name=my-service
```

`config set` supports persistent parameter defaults and persistent trust/consent settings. Legacy source-resolution settings such as `--vcs-url` and `--template-prefix` are no longer supported runtime configuration.

### Persistent Settings

- `--parameter-default <name>=<value>` sets a default parameter value for later runs.

  ```
  openplate config set --parameter-default git_org=my-org
  ```

- `--allow-template-commands` allows template-provided init commands to run by default during later init runs.

  ```
  openplate config set --allow-template-commands
  ```

- `--allow-last-updater-email` allows templates that require `last_updater_email` during later init or update runs.

  ```
  openplate config set --allow-last-updater-email
  ```

## Command: init

Add a template to a project

```
openplate init https://github.com/my-org/ot-net-api.git#v1
openplate init git@github.com:my-org/ot-docker.git#v1
openplate init file:///C:/repos/template-catalog#main
```

### Supported Source URL Forms

`init` now uses URL-based sources only.

- Primary syntax: `openplate init <url>`
- Backward-compatible syntax: `openplate init -r <url>`
- Supported URL transports: HTTPS, SSH/scp-style Git URLs, and Git-compatible `file://` URLs
- Optional template sub-folder: append `?path=<relative-template-subdir>`
- Optional branch or tag: append `#<branch-or-tag>`

The legacy nested `project` variant still works for compatibility, but `openplate init` is the documented command.

### One-Time Init Overrides

- `--allow-template-commands` allows template-provided `init_commands` to run for this init invocation.

  ```
  openplate init --allow-template-commands https://github.com/my-org/ot-template.git#v1
  ```

- `--allow-last-updater-email` allows a template that requires `last_updater_email` to use it for this init invocation.

  ```
  openplate init --allow-last-updater-email https://github.com/my-org/ot-template.git#v1
  ```

### SSH Key Selection

If you need a non-default SSH key for an SSH template URL, export `GIT_SSH_COMMAND` before running OpenPlate so Git uses the expected identity:

```
export GIT_SSH_COMMAND='ssh -i ~/.ssh/special-openplate-key -o IdentitiesOnly=yes'
openplate init git@github.com:my-org/template-catalog.git?path=python/api#main
```

This applies only to SSH template URLs. HTTPS template URLs do not use SSH keys.

### Project Root Resolution

`init`, `update`, `verify`, `info`, and `project print-init-json` share the `--project-root` option.

- `--project-root <path>` sets the managed project root explicitly.
- if `--project-root` is omitted and the invocation folder is inside a Git work tree, OpenPlate uses the Git top-level folder as the project root and the invocation-relative path as the default `dest_folder`
- if `--project-root` is omitted outside Git, OpenPlate uses the invocation folder and defaults `dest_folder` to `.`
- `--project-folder` is no longer accepted; use `--project-root` instead

Project root examples:

```
openplate init --project-root C:/workspaces/my-repo https://github.com/my-org/ot-template.git#v1
openplate update --project-root C:/workspaces/my-repo --update-full
openplate verify --project-root C:/workspaces/my-repo
openplate info --project-root C:/workspaces/my-repo
```

Source URL examples:

```
openplate init https://github.com/my-org/ot-template.git#v1
openplate init git@github.com:my-org/template-catalog.git?path=python/api#main
openplate init file:///C:/repos/template-catalog#main

# deprecated format
openplate init -r https://github.com/my-org/ot-template.git#v1
```

### Dest Folder

Some templates take advantage of a "sub-folder" to init into.  This allows the template to access both the repo root and the sub-folder for it's files.

- Example:
  
  ```
  openplate init --dest-folder=src git@github.com:my-org/ot-docker.git#v1
  ```

If `--dest-folder` is omitted:

- with an explicit `--project-root`, it resolves to `.`
- inside Git without an explicit `--project-root`, it resolves to the relative path from the Git top-level folder to the invocation folder
- outside Git, it resolves to `.`

### Re-running Init

- A plain rerun of `openplate init` for the same tracked template and dest-folder is rejected.
- `openplate init --overwrite` reruns init for the same tracked template and dest-folder and overwrites tracked template output.
- `openplate init --overwrite` skips init-command reruns and reuses the existing tracked template entry in `.openplate.project.yaml`.

## Command: update

Update the current project with the latest versions of the template

```
openplate update
```

The legacy nested `project` variant still works for compatibility, but `openplate update` is the documented command.

### One-Time Update Overrides

- `--allow-last-updater-email` allows tracked templates that require `last_updater_email` to use it for this update invocation.

  ```
  openplate update --allow-last-updater-email
  ```

### Update Modes

- `--update-missing` recreates missing non-readonly files without overwriting existing non-readonly files.

  ```
  openplate update --update-missing
  ```

- `--update-full` is the overwrite-oriented maintenance mode. It recreates missing non-readonly files and overwrites existing non-readonly files.

  ```
  openplate update --update-full
  ```

## Command: info

Inspect the tracked template state for the current project.

```
openplate info
```

The legacy nested `project` variant still works for compatibility, but `openplate info` is the documented command.

By default, `info` reads `.openplate.project.yaml` and inspects each tracked template source so it can show the tracked template reference, destination folder, provenance, and prompt metadata such as current, default, and existing values.

### Offline Inspection

- `--offline` skips template inspection and shows only the data already persisted in `.openplate.project.yaml`.

  ```
  openplate info --offline
  ```

Use this mode when you want to inspect the tracked project state without fetching or cloning template sources.

### Hidden Parameters

- `--show-hidden` includes hidden parameters when `info` is inspecting live template metadata.

  ```
  openplate info --show-hidden
  ```

`--show-hidden` cannot be combined with `--offline` because offline mode does not inspect the template definitions needed to identify hidden parameters.

## Prompt JSON Workflow

OpenPlate supports a machine-driven prompt workflow for both init and update. The general pattern is:

1. Print the prompt document for the exact command context you plan to run.
2. Edit only the answers you want to change.
3. Re-run the matching command with `--prompts-json-file` or `--prompts-json-stdin`.

### Init Prompt JSON

For init, the prompt document is bound to the same `--dest-folder` placement context that the later init run must use.

Export the init prompt tree:

```
openplate project print-init-json https://github.com/my-org/ot-template.git#v1 --dest-folder generated/app
openplate project print-init-json https://github.com/my-org/ot-template.git#v1 --dest-folder generated/app --verbose
```

Import answers from a file or standard input using the same `--dest-folder`:

```
openplate init https://github.com/my-org/ot-template.git#v1 --dest-folder generated/app --prompts-json-file prompts.json
type prompts.json | openplate init https://github.com/my-org/ot-template.git#v1 --dest-folder generated/app --prompts-json-stdin
```

`project print-init-json` is read-only. It does not update `.openplate.project.yaml` or write template output.

The compact init export format is a top-level JSON array of prompt nodes:

```json
[
  {
    "node-id": "15cff52",
    "answers": {
      "service_name": null
    }
  }
]
```

The verbose init export includes the same `node-id` and `answers` fields plus `info` metadata:

```json
[
  {
    "node-id": "15cff52",
    "answers": {
      "service_name": null
    },
    "info": {
      "template": "https://github.com/my-org/ot-template.git#v1",
      "dest_folder": "generated/app",
      "parameters": {
        "service_name": {
          "default": null,
          "existing": null,
          "description": "Service Name",
          "choices": null,
          "hidden": null,
          "required": true
        }
      }
    }
  }
]
```

Init semantics:

- `node-id` is the import/export identity for a reached init node under the chosen `--dest-folder`.
- `answers` contains only the prompt answers used on import.
- compact export omits `info`.
- verbose export includes `info.template`, project-relative `info.dest_folder`, and prompt metadata.
- when present, verbose `info.require_sibling_templates` describes caller-side sibling declarations, including any sibling `condition` metadata.
- hidden parameters are included only when the command uses `--ask-hidden`.
- `null` means do not answer this parameter from JSON; normal runtime fallback still applies.
- `""` means an intentional blank string answer.
- any other non-null string means an explicit supplied answer for that parameter.
- omitting an answer key also means unresolved, so normal runtime fallback applies if that parameter is reached.

Important:

- `project print-init-json` and `init` must use the same resolved `--dest-folder` if you want the printed `node-id` values and prompt metadata to remain valid.
- if you print for one init placement and later run init with a different `--dest-folder`, the earlier prompt document no longer matches that later init run correctly.

### Update Prompt JSON

For update, the prompt document is bound to the same selected project context and tracked template state that the later update run must use.

Export the update prompt tree:

```
openplate project print-update-json --project-root C:/workspaces/my-repo
```

Import update answers from a file or standard input against the same project root and tracked state:

```
openplate update --project-root C:/workspaces/my-repo --prompts-json-file prompts.json
type prompts.json | openplate update --project-root C:/workspaces/my-repo --prompts-json-stdin
```

`project print-update-json` is read-only. It does not update `.openplate.project.yaml` or write template output.

The update export always includes verbose metadata and uses a structured answer shape:

```json
[
  {
    "node-id": "15cff52",
    "answers": {
      "service_name": {
        "supplied": false,
        "value": null
      }
    },
    "info": {
      "template": "https://github.com/my-org/ot-template.git#v1",
      "dest_folder": "services/api",
      "parameters": {
        "service_name": {
          "current": "existing-name",
          "default": "default-name",
          "existing": "existing-name",
          "description": "Service Name",
          "choices": null,
          "hidden": null,
          "required": false
        }
      }
    }
  }
]
```

Update semantics:

- `node-id` is the import/export identity for a reached update node in the selected project context.
- every update answer entry uses `supplied` plus `value`.
- `supplied: false` with `value: null` means leave the parameter untouched and use normal existing/default logic.
- `supplied: true` with a non-null string means an explicit supplied answer. `""` remains an explicit blank string.
- `supplied: true` with `value: null` means clear any persisted explicit override and continue with normal default logic.
- update prompt JSON always includes hidden parameters. `--ask-hidden` does not gate update prompt JSON scope.
- `info.parameters.current` shows the effective value update would use if the answer entry stays unsupplied.
- `info.parameters.existing` shows the persisted explicit project value, if any.
- `info.parameters.default` shows the processed template or global default, if any.

Important:

- `project print-update-json` and `update` must use the same selected project root and tracked template state if you want the printed `node-id` values and prompt metadata to remain valid.

Shared prompt JSON notes:

- `project print-init-json` and `project print-update-json` are the only modes that walk the full declared sibling tree without applying sibling `condition` filters.
- imported nodes that are not processed by the run are ignored and logged by `node-id`.
- OpenPlate warns when supplied prompt answers are left unused for a matched node.
- init and update both reject invalid choice values under the same rules as interactive prompting.

## Command: verify

Verify that the project has not drifted from the template. Exit with code -1 if so.

```
openplate verify
```

## Ask Again

If you want to re-answer questions you can use

```
openplate update --ask-again
```

## Answer "hidden" questions

The answer to some questions are usually assumed, but you have the ability to answer them by specifying the "--ask-hidden" option

```
openplate init --ask-hidden git@github.com:my-org/ot-docker.git#v1
```

or

```
openplate update --ask-hidden
```

The same flag controls init prompt JSON scope. With `--ask-hidden`, hidden parameters are included in `project print-init-json` output and may be answered through `--prompts-json-file` or `--prompts-json-stdin` on `init`. Without it, hidden parameters are omitted from init export and ignored on init import. Update prompt JSON is different: hidden parameters are always included in `project print-update-json` output and remain in scope on update prompt JSON import.

# Template Branches

NOTE: to use a specific branch or tag of a template, append `#branchname` on init. If you omit `#branchname`, you must also pass `--allow-default-branch`.

Examples:

```
openplate init https://github.com/my-org/ot-sometemplate#0.0.9
openplate init --allow-default-branch https://github.com/my-org/ot-sometemplate
```

### Template Catalog Sub-Folders

If a repository stores templates in sub-folders, use `?path=` to select the template root inside the repository clone.

```
openplate init https://github.com/my-org/template-catalog.git?path=templates/net-api#v1
```

## No cache

If you wish for a specific template to be added to this project but not "cached" in the "template cache", specify the `--no-cache` argument.

```
openplate init --no-cache https://github.com/my-org/ot-sometemplate#0.0.9
```

This is useful when you have:

- a template which will use other templates in it's own files
- Needs to NOT send the files of some templates to the child project
- DOES need to pass on some of it's inherited files from particular templates to the child project 
