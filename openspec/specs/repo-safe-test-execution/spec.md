# repo-safe-test-execution Specification

## Purpose
TBD - created by archiving change isolate-repo-mutating-test-runs. Update Purpose after archive.
## Requirements
### Requirement: Repo-mutating test helpers execute only inside disposable repos
Any checked-in OpenPlate test helper or manual-test helper that can change git repo state SHALL perform those mutations only inside a disposable repository created for that run. Repo-mutating commands include at minimum `git init`, `git config`, `git branch`, `git checkout`, `git switch`, `git add`, `git commit`, `git reset`, and `git remote add`.

The disposable repository SHALL be isolated from the contributor's live OpenPlate checkout and SHALL be created under a temporary or other explicitly disposable root dedicated to that run.

#### Scenario: Git-mutating helper runs in a temporary repo
- **WHEN** a checked-in helper needs to seed a git repo for a manual test or regression workflow
- **THEN** it creates or uses a disposable repository dedicated to that run
- **AND** it performs repo-mutating git commands only against that disposable repository
- **AND** it does not mutate git state in the contributor's live OpenPlate checkout

#### Scenario: Repo-local test identity stays scoped to the disposable repo
- **WHEN** a checked-in helper sets repo-local git user name or email for test setup
- **THEN** it writes that identity only inside the disposable repository used for that run
- **AND** it does not change git identity in any other repository

### Requirement: Unsafe repo targets are rejected before git mutation
Before issuing any repo-mutating git command, a checked-in OpenPlate test helper or manual-test helper SHALL resolve the candidate target repo path and verify that it is inside an approved disposable root for the current run.

The helper SHALL reject the target before any git mutation if the resolved path points at the checked-out OpenPlate repository, at another non-disposable repository, or at a path outside the approved disposable root.

#### Scenario: Helper rejects the live OpenPlate checkout as a target
- **WHEN** a repo-mutating helper resolves its candidate target path to the checked-out OpenPlate repository
- **THEN** the helper fails before running any repo-mutating git command
- **AND** it reports that the target is not a disposable repository

#### Scenario: Helper rejects a path outside the disposable root
- **WHEN** a repo-mutating helper resolves its candidate target path to a location outside the approved temporary or disposable root for the current run
- **THEN** the helper fails before running any repo-mutating git command
- **AND** it does not alter git config, branch state, index state, remotes, or commit history for that location

