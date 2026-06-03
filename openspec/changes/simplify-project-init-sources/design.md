## Context

`openplate project init` currently exposes three mutually exclusive source entrypoints: URL, name, and folder. In practice, the command already centers most non-folder behavior on URL-backed sources: named templates are converted into a URL-shaped string before loading, and URL sources are cloned through the Git helper before the template walker reads files from the clone root.

This creates three problems. First, the CLI surface area is larger than the underlying model. Second, supported Git inputs such as `file://` are not treated as a documented first-class source form even though the Git transport layer can clone them. Third, URL sources always use the repository root as the template root, which blocks template catalogs that keep multiple templates in sub-folders of one repository.

## Goals / Non-Goals

**Goals:**
- Make URL-based sources the single source model for `project init`.
- Allow `openplate project init <url>` as the primary invocation form while preserving `-r/--url` for compatibility.
- Support `file://` URLs anywhere a URL source is accepted.
- Support selecting a template root inside a cloned repository with `?path=<relative-subdir>`.
- Document supported URL forms, ref selection, default-branch behavior, and migration from removed options.

**Non-Goals:**
- Preserve shorthand name-based source resolution.
- Preserve non-git local folder initialization through `-f/--folder`.
- Add support for arbitrary query parameters beyond `path`.
- Expand this change to unrelated template processing or update behavior beyond what is required by the new source syntax.

## Decisions

### 1. Use URL sources as the only `project init` source type

`project init` will accept a single URL source either positionally or through `-r/--url`. The positional form becomes the primary syntax, and `-r/--url` remains as a backward-compatible alias.

The `-n/--name` and `-f/--folder` options will be removed. The change intentionally narrows the CLI to one source concept instead of continuing to support multiple entrypoints that eventually converge or diverge in surprising ways.

Alternatives considered:
- Keep all three source types and add more documentation. Rejected because it preserves the current mental overhead and keeps future parsing work split across modes.
- Deprecate `-n` and `-f` without removing them. Rejected because the user explicitly wants the surface removed, and the simplification benefit is largest when help text and validation only describe one source model.

### 2. Represent repository sub-folder selection with `?path=`

URL references will use the following shape:

`<repo-location>[?path=<relative-template-subdir>][#<ref>]`

Examples:
- `https://github.com/my-org/template-catalog.git?path=python/api#v1`
- `git@github.com:my-org/template-catalog.git?path=python/api#main`
- `file:///C:/repos/template-catalog?path=python/api#main`

The `path` value will be normalized as a relative path and rejected if it is empty, absolute, or escapes the cloned repository root.

Alternatives considered:
- `repo//subdir#ref`. Rejected because the separator is less obvious and is harder to parse cleanly across URL schemes.
- `repo#ref:path` or similar delimiter-heavy forms. Rejected because they are harder to read and easier to confuse with SSH syntax.
- A separate `--source-path` flag. Rejected because the user prefers a self-contained source reference and the `?path=` form matches existing package ecosystem conventions.

### 3. Treat `file://` as a supported URL transport, not a separate source mode

`file://` references will flow through the same URL-source implementation as HTTPS and SSH references. OpenPlate will treat them as Git-backed sources that are cloned before template processing begins.

This keeps the implementation aligned with the existing Git-based URL flow and avoids reintroducing folder semantics through a second path.

Alternatives considered:
- Special-case `file://` as an alias for the removed folder mode. Rejected because that would support non-git behavior through a URL spellings and blur the source model again.
- Support plain local paths as part of this change. Rejected for now because the request specifically calls out `file://`, and raw local path parsing introduces separate ambiguity on Windows.

### 4. Resolve template sub-paths inside the URL source abstraction

The URL source implementation should parse the source reference into three parts: clone location, optional template sub-path, and optional Git ref. After cloning, the source object should expose the selected template directory as its `folder_path()` so the existing walker can keep loading the template config, template project config, and files from one root.

This keeps the rest of the pipeline largely unchanged and contains the new parsing logic at the source boundary.

Alternatives considered:
- Thread a separate template sub-path through the walker and template processor. Rejected because it would scatter path handling across multiple modules.
- Clone only the selected sub-folder. Rejected because Git does not provide that behavior directly for normal clones.

### 5. Make migration explicit in docs and errors

Because this change removes two init options, the CLI and documentation should point users toward the replacements:
- named templates must become explicit URLs
- local git templates should use `file://`
- repository catalogs should use `?path=`

Documentation should also explain that `#ref` remains the way to select a branch or tag, with `--allow-default-branch` preserving the existing escape hatch.

## Risks / Trade-offs

- [Breaking removal of `-n/--name` and `-f/--folder`] -> Provide targeted error messages and migration examples in docs and CLI help.
- [Query parsing edge cases for SSH and Windows `file://` URLs] -> Use a single parser with explicit coverage for optional query and fragment components.
- [Sub-path traversal or invalid roots] -> Normalize `path`, reject absolute paths, and reject values that resolve outside the clone root.
- [Users may expect `file://` to work for non-git folders] -> Document that URL sources are Git-backed and keep validation/error text explicit.

## Migration Plan

- Update command help and docs to show positional URL syntax as the primary form and `-r/--url` as legacy-compatible.
- Emit actionable errors for removed `-n/--name` and `-f/--folder` usage, including the replacement syntax.
- Document migration examples from name-based and folder-based init commands to explicit URL references.

## Open Questions

- Should a future change also accept plain local Git repository paths without `file://`, or should local repository usage stay explicit through the URI form only?