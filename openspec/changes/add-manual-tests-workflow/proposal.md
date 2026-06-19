## Why

OpenPlate has end-to-end behaviors that are exercised by real executable runs, but the repository does not yet provide a single, repeatable manual-test workflow that tells contributors exactly what to run, what fixtures to use, what output to inspect, and how to clean up afterwards. That gap makes manual verification ad hoc, increases the chance that feature coverage drifts, and leaves too much command construction to whoever is testing the branch.

## What Changes

- Add a repo-owned `manual-tests/` workspace that documents every full executable manual test case needed to cover the app's end-to-end feature surface.
- Add `manual-tests/index.md` as the operator guide for prerequisites, execution order, artifact locations, cleanup expectations, and validation responsibilities.
- Add numbered per-case documents at `manual-tests/case-X.md` that contain the exact commands or scripts to run and the exact outcomes that still require human validation.
- Seed the initial suite with concrete numbered cases organized around real operator workflows rather than isolated commands: bootstrap plus URL-source init, interactive init behavior, prompt JSON init behavior, and update/verify lifecycle behavior.
- Require `manual-tests/index.md` to include a coverage matrix that accounts for every current CLI command and facet surfaced by `docs/commands.md`, `readme.md`, and `src/openplate/__main__.py`, marking each item as covered by a manual case, covered by automated tests only, or intentionally excluded with rationale.
- Add `manual-tests/templates/` for staged public test fixtures and require the run workflow to materialize local git-backed template repos from those checked-in fixture directories instead of depending on network or private sources.
- Add runnable helper scripts named `manual-tests/run-manual-tests.sh` and `manual-tests/cleanup-manual-tests.sh`, plus per-case `manual-tests/case-X.sh` scripts only when a case is too complex to express inline in Markdown.
- Add gitignore coverage for the disposable working directories `manual-tests/work/<case-id>/` and `manual-tests/artifacts/<case-id>/`, which hold generated repos, logs, prompt JSON files, and other manual-test outputs without cross-case collisions.
- Add an `AGENTS.md` reference that points contributors and agents to `manual-tests/` as the source of truth for end-to-end manual execution coverage.

## Capabilities

### New Capabilities
- `manual-tests-workflow`: Defines the repository structure, documentation contract, fixture constraints, script expectations, and cleanup rules for repeatable end-to-end manual tests.

### Modified Capabilities

## Impact

Affected areas include a new `manual-tests/` directory tree, root `.gitignore`, new helper scripts for running and cleaning manual-test workspaces, repository guidance in `AGENTS.md`, staged public fixture templates that can be turned into local git-backed template repos for execution, the initial manual case set covering the current documented CLI workflow, and an explicit feature/facet coverage matrix that prevents silent omissions.
