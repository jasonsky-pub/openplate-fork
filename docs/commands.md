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

## Command: project init

Add a template to a project

```
openplate project init https://github.com/my-org/ot-net-api.git#v1
openplate project init git@github.com:my-org/ot-docker.git#v1
openplate project init file:///C:/repos/template-catalog#main
```

### Supported Source URL Forms

`project init` now uses URL-based sources only.

- Primary syntax: `openplate project init <url>`
- Backward-compatible syntax: `openplate project init -r <url>`
- Supported URL transports: HTTPS, SSH/scp-style Git URLs, and Git-compatible `file://` URLs
- Optional template sub-folder: append `?path=<relative-template-subdir>`
- Optional branch or tag: append `#<branch-or-tag>`

Examples:

```
openplate project init https://github.com/my-org/ot-template.git#v1
openplate project init git@github.com:my-org/template-catalog.git?path=python/api#main
openplate project init file:///C:/repos/template-catalog#main

# deprecated format
openplate project init -r https://github.com/my-org/ot-template.git#v1
```

### Dest Folder

Some templates take advantage of a "sub-folder" to init into.  This allows the template to access both the repo root and the sub-folder for it's files.

- Example:
  
  ```
  openplate project init --dest-folder=src git@github.com:my-org/ot-docker.git#v1
  ```

## Command: project update

Update the current project with the latest versions of the template

```
openplate project update
```

## Command: project verify

Verify that the project has not drifted from the template. Exit with code -1 if so.

```
openplate project verify
```

## Ask Again

If you want to re-answer questions you can use

```
openplate project --ask-again update
```

## Answer "hidden" questions

The answer to some questions are usually assumed, but you have the ability to answer them by specifying the "--ask-hidden" option

```
openplate project --ask-hidden init git@github.com:my-org/ot-docker.git#v1
```

or

```
openplate project --ask-hidden update
```

# Template Branches

NOTE: to use a specific branch or tag of a template, append `#branchname` on init. If you omit `#branchname`, you must also pass `--allow-default-branch`.

Examples:

```
openplate project init https://github.com/my-org/ot-sometemplate#0.0.9
openplate project init --allow-default-branch https://github.com/my-org/ot-sometemplate
```

### Template Catalog Sub-Folders

If a repository stores templates in sub-folders, use `?path=` to select the template root inside the repository clone.

```
openplate project init https://github.com/my-org/template-catalog.git?path=templates/net-api#v1
```

## No cache

If you wish for a specific template to be added to this project but not "cached" in the "template cache", specify the `--no-cache` argument.

```
openplate project init --no-cache https://github.com/my-org/ot-sometemplate#0.0.9
```

This is useful when you have:

- a template which will use other templates in it's own files
- Needs to NOT send the files of some templates to the child project
- DOES need to pass on some of it's inherited files from particular templates to the child project 
