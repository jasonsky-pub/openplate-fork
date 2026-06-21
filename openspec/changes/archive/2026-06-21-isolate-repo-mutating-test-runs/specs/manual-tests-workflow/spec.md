## MODIFIED Requirements

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
