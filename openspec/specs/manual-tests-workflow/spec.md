# manual-tests-workflow Specification

## Purpose
TBD - created by archiving change add-manual-tests-workflow. Update Purpose after archive.
## Requirements
### Requirement: Repository-owned manual test workspace
OpenPlate SHALL keep a checked-in `manual-tests/` workspace that is the source of truth for end-to-end manual execution guidance. The workspace SHALL include an operator index, numbered case documents, a staged fixture area, and executable helper scripts needed to run or clean the manual test workflow.

#### Scenario: Repository exposes the manual test workspace
- **WHEN** a contributor inspects the repository
- **THEN** the repository contains a `manual-tests/` directory
- **THEN** that directory includes `index.md`, `run-manual-tests.sh`, `cleanup-manual-tests.sh`, one or more `case-X.md` files, and a `templates/` directory

### Requirement: Seeded manual cases cover the current documented command surface
The initial manual test suite SHALL define these numbered cases and their primary coverage areas:
- `manual-tests/case-1.md`: config persistence plus URL-source init behavior, including `config set`, `config get`, the primary `openplate init` source-selection workflow, `--project-root`, invalid explicit Git subfolder root overrides, Git-mode `dest_folder` defaults, explicit `--dest-folder` overrides, project-file metadata omission, SSH or HTTPS metadata handling, HTTPS credential scrubbing, template source `?path=` and `#ref` preservation, non-Git template-source metadata emptiness, and legacy-source migration behavior
- `manual-tests/case-2.md`: interactive `openplate init` behavior, including hidden-parameter and `conditionally_hidden` behavior
- `manual-tests/case-3.md`: prompt JSON round-trip behavior, including `openplate project print-init-json`, `openplate project print-init-json --verbose`, `openplate project print-init-json --dest-folder`, `openplate project print-update-json`, `openplate init --prompts-json-file`, `openplate init --prompts-json-stdin`, `openplate update --prompts-json-file`, and `openplate update --prompts-json-stdin`, plus init placement-consistency behavior, update hidden-parameter visibility, and prompt JSON invalid-choice rejection behavior
- `manual-tests/case-4.md`: `openplate update`, `openplate update --update-missing`, `openplate update --update-full`, and `openplate project verify`, exercised against a project with intentional drift while anchored at the resolved project root folder

The manual test index SHALL map those cases back to the current documented command surface.

The seeded case layout SHALL group commands by end-to-end operator workflow rather than by one-command-per-case isolation.

#### Scenario: Contributor checks which case covers config persistence
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-1.md` as the seeded case for config persistence behavior

#### Scenario: Contributor checks which case covers init behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-1.md` and `manual-tests/case-2.md` as the seeded cases for init behavior, split between source, root, and destination concerns versus interactive runtime concerns

#### Scenario: Contributor checks which case covers prompt JSON behavior
- **WHEN** a contributor reads the manual test inventory
- **THEN** the inventory identifies `manual-tests/case-3.md` as the seeded case for prompt JSON export, import, and validation behavior across init and update

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
- global CLI facets such as `--version`, `--config-file`, `--project-root`, `--ask-hidden`, `--ask-again`, `--ignore-tool-version`, `--debug`, and `--automation`
- config command facets including `config get`, `config set`, project-file omission of runtime-derived project metadata, and the omission of legacy name-resolution settings from supported behavior
- init source and runtime facets including local file URLs, SSH and HTTPS Git URLs, sanitized HTTPS Git URLs, non-Git template URLs, `?path=` sub-folders, explicit refs, preserved template `#ref` semantics, deprecated Liquid alias availability, `--allow-default-branch`, deprecated `-r/--url`, invalid explicit Git subfolder `--project-root` handling, Git-mode default `dest_folder` resolution, exact `--dest-folder` override behavior, `--no-cache`, `--overwrite`, `--ignore`, and `--allow-template-commands`
- prompt JSON export and import facets for init and update, including init print or import placement consistency, update project-context consistency, update hidden-parameter inclusion, explicit clear semantics, and invalid choice rejection
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
Checked-in manual test fixtures SHALL live under `manual-tests/templates/` and SHALL avoid internal or company-specific files, template references, URLs, names, or identifiers. Generated repositories, temporary workspaces, captured outputs, and other disposable manual-test state SHALL be kept in dedicated gitignored working folders or in a temporary repo-shaped sandbox created solely for the current run.

When a manual workflow needs to change repo-level git settings or current branch state, that mutation SHALL occur only inside a temporary repo-shaped sandbox or another explicitly disposable repo created for that run, never in the contributor's checked-out OpenPlate repository.

#### Scenario: Checked-in fixture content is reviewed
- **WHEN** a contributor reviews files under `manual-tests/templates/`
- **THEN** those files use public-safe, generic fixture content and do not reference internal or company-specific assets

#### Scenario: Manual workflow uses local template repos
- **WHEN** a contributor follows a numbered manual case
- **THEN** the case uses local git-backed template repos materialized from `manual-tests/templates/`
- **THEN** the case does not require network access or any private template source

#### Scenario: Manual test work products are disposable
- **WHEN** a contributor runs the manual test workflow
- **THEN** generated repos and temporary workspaces are created only under approved disposable roots for that case
- **AND** captured outputs such as logs or prompt JSON files are created only under disposable case-scoped locations

#### Scenario: Repo-mutating manual setup uses a temporary repo sandbox
- **WHEN** a manual-test helper needs to set repo-local git identity, change branch state, or create seed commits
- **THEN** it performs those actions only inside a temporary repo-shaped sandbox or another disposable repo dedicated to that run
- **AND** it does not apply those mutations to the checked-out OpenPlate repository

### Requirement: Manual test scripts support execution and cleanup
The repository SHALL provide checked-in scripts for running manual test cases and for cleaning up manual-test working folders after execution. These scripts SHALL operate only on the manual-test workflow's disposable state, SHALL preserve checked-in fixtures and documentation, and SHALL fail before any repo-mutating setup targets a non-disposable repository.

#### Scenario: Contributor runs a manual case through the repo scripts
- **WHEN** a contributor follows the documented manual-test workflow
- **THEN** the repository provides `manual-tests/run-manual-tests.sh` as the entrypoint for running one case or the seeded manual test suite

#### Scenario: Contributor cleans manual test state
- **WHEN** a contributor runs the documented cleanup script
- **THEN** the script removes disposable manual-test work products
- **THEN** the script does not remove checked-in files under `manual-tests/templates/` or the case documentation

#### Scenario: Manual-test runner rejects an unsafe git target
- **WHEN** the shared manual-test runner resolves a repo target outside its approved disposable roots or to the checked-out OpenPlate repository
- **THEN** the runner fails before issuing repo-mutating git commands for that target
- **AND** it reports that the target is unsafe for manual-test git setup

### Requirement: Agent guidance points to the manual test workflow
The repository SHALL include an `AGENTS.md` file that tells future agents where the manual test workflow lives and directs them to use the checked-in `manual-tests/` guidance instead of reconstructing end-to-end commands from memory.

#### Scenario: Agent looks for manual execution guidance
- **WHEN** an agent reads `AGENTS.md`
- **THEN** the file points the agent to `manual-tests/` as the source of truth for end-to-end manual test execution guidance
- **THEN** the file tells the agent to read `manual-tests/index.md` and the relevant numbered case document before proposing or running manual commands

