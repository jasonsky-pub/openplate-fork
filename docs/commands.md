# openplate

## Command: config get

Set configuration for the tool (available in ~/.openplate)

```
openplate config get
```

## Command: config set

Set configuration for the tool (available in ~/.openplate)

```
openplate config set --vcs-url https://github.com/my-org
```

### Default Parameters

You can also set default parameters which will override template defaults, example:

```
openplate config set --parameter-default git_org=my-org
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

Examples:

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

Common update modes:

```
openplate update --update-missing
openplate update --update-full
```

- `--update-missing` recreates missing non-readonly files without overwriting existing non-readonly files.
- `--update-full` is the overwrite-oriented maintenance mode. It recreates missing non-readonly files and overwrites existing non-readonly files.

## Prompt JSON Workflow

For machine-driven init runs, OpenPlate can export the prompt state as JSON, let you fill in only the answers you care about, and then consume that JSON during `init` without falling back to interactive prompting.

Export the init prompt tree:

```
openplate project print-init-json https://github.com/my-org/ot-template.git#v1
openplate project print-init-json https://github.com/my-org/ot-template.git#v1 --verbose
```

Import answers from a file or standard input:

```
openplate init https://github.com/my-org/ot-template.git#v1 --prompts-json-file prompts.json
type prompts.json | openplate init https://github.com/my-org/ot-template.git#v1 --prompts-json-stdin
```

`project print-init-json` is read-only. It does not update `.openplate.project.yaml` or write template output.

The compact export format is a top-level JSON array of prompt nodes:

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

The verbose export includes the same `node-id` and `answers` fields plus `info` metadata:

```json
[
  {
    "node-id": "15cff52",
    "answers": {
      "service_name": null
    },
    "info": {
      "template": "https://github.com/my-org/ot-template.git#v1",
      "dest_folder": ".",
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

Key semantics:

- `node-id` is the import/export identity for a reached init node.
- `answers` contains only the prompt answers used on import.
- compact export omits `info`.
- verbose export includes `info.template`, init-relative `info.dest_folder`, and prompt metadata.
- when present, verbose `info.require_sibling_templates` describes caller-side sibling declarations, including any sibling `condition` metadata.
- the init root from `openplate init --dest-folder ...` is not part of exported `node-id` values or exported `info.dest_folder` values.

Hidden parameters are included only when the command uses `--ask-hidden`. Without `--ask-hidden`, hidden parameters are omitted from prompt JSON export and ignored on prompt JSON import.

Answer semantics:

- `null` means do not answer this parameter from JSON; if the parameter is reached, OpenPlate uses the normal runtime fallback such as an existing value or template/default value
- `""` means an intentional blank string answer
- any other non-null string means an explicit supplied answer for that parameter
- omitting an answer key also means unresolved, so normal runtime fallback applies if that parameter is reached

Import semantics:

- OpenPlate matches imported prompt JSON by `node-id`.
- `info` is ignored on import.
- For parameters in scope for the command, any non-null answer is authoritative even if runtime fallback already has an existing or default value.
- `--ask-again` affects interactive prompting. It does not prevent a non-null prompt JSON answer from being applied.

Notes:

- `project print-init-json` is the only mode that walks the full declared sibling tree without applying sibling `condition` filters.
- `--prompts-json-file` and `--prompts-json-stdin` are supported for init only.
- `project update` does not expose prompt JSON flags.
- imported nodes that are not processed by the run are ignored and logged by `node-id`.
- OpenPlate warns when supplied prompt answers are left unused for a matched node.

## Command: project verify

Verify that the project has not drifted from the template. Exit with code -1 if so.

```
openplate project verify
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

The same flag controls prompt JSON scope. With `--ask-hidden`, hidden parameters are included in `project print-init-json` output and may be answered through `--prompts-json-file` or `--prompts-json-stdin` on `init`. Without it, hidden parameters are omitted from export and ignored on import.

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
