## ADDED Requirements

### Requirement: Repository-owned manual test workspace
OpenPlate SHALL keep a checked-in `manual-tests/` workspace that is the source of truth for end-to-end manual execution guidance. The workspace SHALL include an operator index, numbered case documents, a staged fixture area, and executable helper scripts needed to run or clean the manual test workflow.

#### Scenario: Repository exposes the manual test workspace
- **WHEN** a contributor inspects the repository
- **THEN** the repository contains a `manual-tests/` directory
- **THEN** that directory includes `index.md`, `run-manual-tests.sh`, `cleanup-manual-tests.sh`, one or more `case-X.md` files, and a `templates/` directory

### Requirement: Seeded manual cases cover the current documented command surface
The initial manual test suite SHALL define these numbered cases and their primary coverage areas:
- `manual-tests/case-1.md`: config persistence plus URL-source init behavior, including `config set`, `config get`, and the primary `openplate init` source-selection workflow
- `manual-tests/case-2.md`: interactive `openplate init` behavior, including hidden-parameter and `conditionally_hidden` behavior
- `manual-tests/case-3.md`: `openplate project print-init-json`, `openplate project print-init-json --verbose`, `openplate init --prompts-json-file`, and `openplate init --prompts-json-stdin`
- `manual-tests/case-4.md`: `openplate update` and `openplate project verify`, exercised against a project with an intentional drift or missing-file condition

The manual test index SHALL map those cases back to the current documented command surface.

The seeded case layout SHALL group commands by end-to-end operator workflow rather than by one-command-per-case isolation.

#### Scenario: Contributor checks which case covers config persistence
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-1.md` as the seeded case for config persistence behavior

#### Scenario: Contributor checks which case covers init behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-1.md` and `manual-tests/case-2.md` as the seeded cases for init behavior, split between source/bootstrap concerns and interactive runtime concerns

#### Scenario: Contributor checks which case covers prompt JSON behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-3.md` as the seeded case for prompt JSON compact export, verbose export, and import behavior

#### Scenario: Contributor checks which case covers update and verify behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-4.md` as the seeded case for update and verify behavior

#### Scenario: Seeded cases follow operator workflows
- **WHEN** a contributor reviews the seeded case layout
- **THEN** commands that are primarily setup for downstream workflows, such as config persistence, are grouped into the relevant end-to-end case instead of forced into a standalone command-only case

### Requirement: Manual test index defines process and coverage
`manual-tests/index.md` SHALL describe the end-to-end manual testing process, required prerequisites, shared workspace conventions, cleanup expectations, and the mapping between manual cases and the app features they cover.

#### Scenario: Contributor needs the full manual test process
- **WHEN** a contributor reads `manual-tests/index.md`
- **THEN** the document explains how to prepare the environment, which cases exist, how to execute them, where disposable work is created, and how to clean up afterwards

#### Scenario: Contributor needs shared script entrypoints
- **WHEN** a contributor reads `manual-tests/index.md`
- **THEN** the document names `manual-tests/run-manual-tests.sh` and `manual-tests/cleanup-manual-tests.sh` as the shared workflow entrypoints

#### Scenario: Contributor needs feature coverage guidance
- **WHEN** a contributor reads `manual-tests/index.md`
- **THEN** the document identifies which end-to-end features are covered by each numbered manual case

### Requirement: The manual test index accounts for all visible CLI facets
`manual-tests/index.md` SHALL include a coverage matrix that accounts for every current CLI feature or compatibility facet surfaced by `docs/commands.md`, `readme.md`, and `src/openplate/__main__.py`. Each listed facet SHALL be marked as one of:
- covered by a specific numbered manual case
- covered by automated tests only
- intentionally excluded, with a short rationale

At minimum, this matrix SHALL account for:
- global CLI facets such as `--version`, `--config-file`, `--project-folder`, `--ask-hidden`, `--ask-again`, `--ignore-tool-version`, `--debug`, and `--automation`
- config command facets including `config get` and `config set` options
- init source and runtime facets including local file URLs, `?path=` sub-folders, explicit refs, `--allow-default-branch`, deprecated `-r/--url`, `--dest-folder`, `--no-cache`, `--overwrite`, `--ignore`, and `--allow-template-commands`
- prompt JSON export and import facets
- update and verify facets
- legacy compatibility and removed-option parser behavior

#### Scenario: Contributor checks a manually covered facet
- **WHEN** a contributor looks up `--dest-folder` in the coverage matrix
- **THEN** the matrix identifies the numbered manual case that exercises it

#### Scenario: Contributor checks an automated-only facet
- **WHEN** a contributor looks up a parser-only compatibility behavior such as a removed flag rejection or legacy alias acceptance
- **THEN** the matrix either maps that behavior to a numbered manual case or marks it as `automated-only`

#### Scenario: Contributor checks an excluded facet
- **WHEN** a contributor looks up a facet that the repo intentionally does not exercise manually
- **THEN** the matrix marks it as excluded and records a short rationale instead of leaving it unmentioned

### Requirement: Each manual case provides exact execution and validation steps
Every full executable end-to-end manual test case that the repository tracks for feature coverage SHALL have a numbered `manual-tests/case-X.md` document. Each case document SHALL include the exact commands to run or the exact checked-in script to invoke, and SHALL list any validations that still require human confirmation after automated steps complete.

#### Scenario: Case document provides exact commands
- **WHEN** a contributor opens a numbered `manual-tests/case-X.md` file
- **THEN** the file shows the exact command lines to execute or the exact repo-relative script path to run for that case

#### Scenario: Case document uses a stable structure
- **WHEN** a contributor opens a numbered `manual-tests/case-X.md` file
- **THEN** the file includes the covered commands, prerequisites, exact commands, expected scripted outputs, manual validation checklist, and cleanup notes

#### Scenario: Case document identifies covered facets
- **WHEN** a contributor opens a numbered `manual-tests/case-X.md` file
- **THEN** the file identifies which coverage-matrix facets the case satisfies

#### Scenario: Complex case delegates to a checked-in script
- **WHEN** a manual case needs a longer or stateful command sequence
- **THEN** the repository may provide an adjacent `manual-tests/case-X.sh` script
- **THEN** the corresponding `manual-tests/case-X.md` file names that exact script and the exact way to invoke it

#### Scenario: Case document preserves human validation steps
- **WHEN** a case run finishes its scripted steps
- **THEN** the corresponding `manual-tests/case-X.md` file identifies any output, files, prompts, or behavioral results that a human still must verify

### Requirement: Manual test fixtures remain public-safe and generated state stays ignored
Checked-in manual test fixtures SHALL live under `manual-tests/templates/` and SHALL avoid internal or company-specific files, template references, URLs, names, or identifiers. Generated repositories, temporary workspaces, captured outputs, and other disposable manual-test state SHALL be kept in dedicated gitignored working folders.

#### Scenario: Checked-in fixture content is reviewed
- **WHEN** a contributor reviews files under `manual-tests/templates/`
- **THEN** those files use public-safe, generic fixture content and do not reference internal or company-specific assets

#### Scenario: Manual workflow uses local template repos
- **WHEN** a contributor follows a numbered manual case
- **THEN** the case uses local git-backed template repos materialized from `manual-tests/templates/`
- **THEN** the case does not require network access or any private template source

#### Scenario: Manual test work products are disposable
- **WHEN** a contributor runs the manual test workflow
- **THEN** generated repos and temporary workspaces are created only under `manual-tests/work/<case-id>/`
- **THEN** captured outputs such as logs or prompt JSON files are created only under `manual-tests/artifacts/<case-id>/`

### Requirement: Manual test scripts support execution and cleanup
The repository SHALL provide checked-in scripts for running manual test cases and for cleaning up manual-test working folders after execution. These scripts SHALL operate only on the manual-test workflow's disposable state and SHALL preserve checked-in fixtures and documentation.

#### Scenario: Contributor runs a manual case through the repo scripts
- **WHEN** a contributor follows the documented manual-test workflow
- **THEN** the repository provides `manual-tests/run-manual-tests.sh` as the entrypoint for running one case or the seeded manual test suite

#### Scenario: Contributor cleans manual test state
- **WHEN** a contributor runs the documented cleanup script
- **THEN** the script removes disposable manual-test work products
- **THEN** the script does not remove checked-in files under `manual-tests/templates/` or the case documentation

### Requirement: Agent guidance points to the manual test workflow
The repository SHALL include an `AGENTS.md` file that tells future agents where the manual test workflow lives and directs them to use the checked-in `manual-tests/` guidance instead of reconstructing end-to-end commands from memory.

#### Scenario: Agent looks for manual execution guidance
- **WHEN** an agent reads `AGENTS.md`
- **THEN** the file points the agent to `manual-tests/` as the source of truth for end-to-end manual test execution guidance
- **THEN** the file tells the agent to read `manual-tests/index.md` and the relevant numbered case document before proposing or running manual commands
