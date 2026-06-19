## MODIFIED Requirements

### Requirement: Seeded manual cases cover the current documented command surface
The initial manual test suite SHALL define these numbered cases and their primary coverage areas:
- `manual-tests/case-1.md`: config persistence plus URL-source init behavior, including `config set`, `config get`, the primary `openplate init` source-selection workflow, `--project-root`, invalid explicit Git subfolder root overrides, Git-mode `dest_folder` defaults, explicit `--dest-folder` overrides, project-file metadata omission, SSH or HTTPS metadata handling, HTTPS credential scrubbing, template source `?path=` and `#ref` preservation, non-Git template-source metadata emptiness, and legacy-source migration behavior
- `manual-tests/case-2.md`: interactive `openplate init` behavior, including hidden-parameter and `conditionally_hidden` behavior
- `manual-tests/case-3.md`: `openplate project print-init-json`, `openplate project print-init-json --verbose`, `openplate init --prompts-json-file`, and `openplate init --prompts-json-stdin`
- `manual-tests/case-4.md`: `openplate update` and `openplate project verify`, exercised against a project with intentional drift while anchored at the resolved project root folder

The manual test index SHALL map those cases back to the current documented command surface.

The seeded case layout SHALL group commands by end-to-end operator workflow rather than by one-command-per-case isolation.

#### Scenario: Contributor checks which case covers config persistence
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-1.md` as the seeded case for config persistence behavior

#### Scenario: Contributor checks which case covers init behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-1.md` and `manual-tests/case-2.md` as the seeded cases for init behavior, split between source, root, and destination concerns versus interactive runtime concerns

#### Scenario: Contributor checks which case covers update and verify behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-4.md` as the seeded case for update and verify behavior

#### Scenario: Seeded cases follow operator workflows
- **WHEN** a contributor reviews the seeded case layout
- **THEN** commands that are primarily setup for downstream workflows, such as config persistence, are grouped into the relevant end-to-end case instead of forced into a standalone command-only case

### Requirement: The manual test index accounts for all visible CLI facets
`manual-tests/index.md` SHALL include a coverage matrix that accounts for every current CLI feature or compatibility facet surfaced by `docs/commands.md`, `readme.md`, and `src/openplate/__main__.py`. Each listed facet SHALL be marked as one of:
- covered by a specific numbered manual case
- covered by automated tests only
- intentionally excluded, with a short rationale

At minimum, this matrix SHALL account for:
- global CLI facets such as `--version`, `--config-file`, `--project-root`, `--ask-hidden`, `--ask-again`, `--ignore-tool-version`, `--debug`, and `--automation`
- config command facets including `config get`, `config set`, project-file omission of runtime-derived project metadata, and the omission of legacy name-resolution settings from supported behavior
- init source and runtime facets including local file URLs, SSH and HTTPS Git URLs, sanitized HTTPS Git URLs, non-Git template URLs, `?path=` sub-folders, explicit refs, preserved template `#ref` semantics, deprecated Liquid alias availability, `--allow-default-branch`, deprecated `-r/--url`, invalid explicit Git subfolder `--project-root` handling, Git-mode default `dest_folder` resolution, exact `--dest-folder` override behavior, `--no-cache`, `--overwrite`, `--ignore`, and `--allow-template-commands`
- prompt JSON export and import facets
- update and verify facets
- legacy compatibility and removed-option parser behavior

#### Scenario: Contributor checks a manually covered facet
- **WHEN** a contributor looks up `--project-root`, `--dest-folder`, or sanitized Git URL handling in the coverage matrix
- **THEN** the matrix identifies the numbered manual case that exercises it

#### Scenario: Contributor checks an automated-only facet
- **WHEN** a contributor looks up a parser-only compatibility behavior such as a removed flag rejection or legacy alias acceptance
- **THEN** the matrix either maps that behavior to a numbered manual case or marks it as `automated-only`

#### Scenario: Contributor checks an excluded facet
- **WHEN** a contributor looks up a facet that the repo intentionally does not exercise manually
- **THEN** the matrix marks it as excluded and records a short rationale instead of leaving it unmentioned
