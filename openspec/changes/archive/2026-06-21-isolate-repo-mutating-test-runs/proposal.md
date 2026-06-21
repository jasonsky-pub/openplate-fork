## Why

OpenPlate's repo-owned manual test helpers currently create git repos, set repo-local git identity, and make seed commits without a hard safety boundary that guarantees those operations stay inside disposable fixture repos. That gap already caused real branch history and repo-local git author settings in the OpenPlate checkout to be overwritten, so the workflow needs an explicit safety contract before this happens again.

## What Changes

- Add a repo-safety contract for any checked-in test or manual-test helper that can change git config, branch state, or commit history.
- Require git-mutating test workflows to run only inside disposable temporary repos or disposable fixture roots, never against the contributor's live checkout.
- Make unsafe target detection fail fast before any helper can run `git init`, `git config`, `git branch`, `git add`, `git commit`, `git reset`, or comparable repo-mutating commands.
- Tighten the manual-test workflow requirements and operator guidance so manual cases that materialize git repos document and enforce their disposable workspace boundaries.

## Capabilities

### New Capabilities
- `repo-safe-test-execution`: Defines the safety guarantees for checked-in test helpers that mutate git state, including required temporary-repo isolation and fail-fast target validation.

### Modified Capabilities
- `manual-tests-workflow`: Manual test runners and documentation must guarantee that repo-mutating setup happens only inside disposable manual-test work roots and cannot affect the checked-out OpenPlate repo.

## Impact

- Affected code: `manual-tests/run-manual-tests.sh` and any other checked-in helper that seeds git repos for tests.
- Affected docs: `manual-tests/index.md`, relevant numbered case docs, and `AGENTS.md` guidance where manual execution safety expectations are described.
- Affected systems: local contributor workflows on Windows, macOS, and Linux where repo-owned test helpers run against git-backed fixture repos.
