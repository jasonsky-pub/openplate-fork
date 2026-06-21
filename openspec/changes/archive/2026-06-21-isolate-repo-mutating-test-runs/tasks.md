## 1. Sandbox And Safety Guards

- [x] 1.1 Add shared runner logic that materializes a temporary repo-shaped sandbox for manual-test flows that perform repo-mutating git setup.
- [x] 1.2 Update git-seeding helpers to resolve target paths canonically and reject any target outside the approved disposable root or equal to the checked-out OpenPlate repo.
- [x] 1.3 Scope repo-local git identity, branch changes, staging, and seed commits explicitly to the disposable target repo.

## 2. Manual Workflow Updates

- [x] 2.1 Update the manual-test workflow docs to explain when and why repo-mutating cases run inside a temporary sandbox.
- [x] 2.2 Update agent guidance and any other repo-owned execution guidance to point contributors at the sandboxed workflow and warn against live-checkout git mutation.

## 3. Validation

- [x] 3.1 Add or update focused tests for unsafe-target rejection and disposable-root validation in the shared manual-test helper logic.
- [x] 3.2 Re-run the relevant manual-test cases in the hardened sandboxed mode and confirm they no longer alter OpenPlate repo-local git config, branch state, or history.
- [x] 3.3 Verify the checked-out OpenPlate repo remains clean before and after the hardened workflow runs.
