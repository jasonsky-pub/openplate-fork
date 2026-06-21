## Context

The current manual-test runner seeds local git repos as part of its fixture setup. That helper changes branch names, writes repo-local git identity, stages files, and creates seed commits. Those actions are legitimate inside disposable fixture repos, but the runner does not currently enforce a hard boundary that guarantees the target path is disposable. Once the helper was accidentally aimed at the real OpenPlate checkout, it overwrote repo-local git author settings and created a `fixture init` commit on the active branch.

The immediate failure happened in `manual-tests/run-manual-tests.sh`, but the broader design concern is any checked-in helper that mutates git repo state. The safety model needs to be explicit and reusable: repo-mutating test helpers must run only inside disposable repos, and they must prove the target path is safe before issuing any git mutation commands.

## Goals / Non-Goals

**Goals:**
- Prevent repo-owned test helpers from mutating the checked-out OpenPlate repo's git config, branch state, index, or commit history.
- Require repo-mutating manual-test setup to run in a safe temporary repo-shaped workspace that is distinct from the source checkout.
- Add fail-fast validation so unsafe target paths are rejected before any `git init`, `git config`, `git branch`, `git add`, `git commit`, or comparable mutation occurs.
- Update manual-test requirements and operator guidance so the safety boundary is documented and testable.

**Non-Goals:**
- Change OpenPlate product behavior for normal `init`, `update`, `verify`, or prompt JSON execution.
- Introduce network-dependent test infrastructure.
- Automatically harden every adjacent or downstream test utility outside this repository.

## Decisions

### Use a temporary repo-shaped sandbox for repo-mutating manual tests
Any checked-in workflow that changes repo-level git settings or current branch state will materialize and operate inside a temporary repo-shaped sandbox rather than the live checkout.

Why this decision:
- It matches the user-visible failure mode: the live checkout was mutated because disposable fixture behavior ran too close to the source repo.
- A temporary repo provides a clean isolation boundary even when scripts need repo-relative layout, bash normalization, or copied fixtures.
- It gives one consistent rule for Windows, macOS, and Linux instead of relying on contributors to reason about which paths are safe.

Alternatives considered:
- Keep using `manual-tests/work/` under the live checkout with stronger path checks only. Rejected because repo-level git mutations can still leak into the source repo if a path variable is wrong.
- Rely on documentation alone. Rejected because the failure is destructive and needs executable guardrails.

### Validate target paths before any git mutation
Helpers that seed or mutate git repos will resolve the candidate repo path to a canonical absolute path and reject it unless it is under an approved disposable root for the current run. They will also explicitly reject the source checkout root and any path outside the temporary sandbox.

Why this decision:
- The root cause is not that the helper performs git setup; it is that it can perform that setup against the wrong repo.
- Canonical-path validation is a cheap, deterministic guard that fails before destructive commands run.

Alternatives considered:
- Trust the caller to pass the right path. Rejected because that is the current unsafe behavior.
- Validate only after `git init`. Rejected because repo-local config and branch state may already be changed by then.

### Keep git operations target-scoped and local to the disposable repo
Repo-mutating helpers should issue git commands against the resolved disposable repo path and keep any test identity local to that disposable repo. They should not depend on or modify the source repo's local config.

Why this decision:
- It makes the safety boundary auditable in code.
- It limits cleanup to disposable repos and prevents cross-repo identity leakage.

Alternatives considered:
- Continue relying on `cd` into the target and implicit local config writes. Rejected because it makes path mistakes harder to spot and review.

## Risks / Trade-offs

- [Temporary sandbox diverges from the live checkout layout] → Mitigation: materialize a repo-shaped sandbox that preserves the repo-relative layout required by the manual workflow and document any copied-back artifacts explicitly.
- [More setup complexity in manual-test scripts] → Mitigation: keep the sandbox creation centralized in shared helpers instead of repeating path checks in every case.
- [Contributors may assume the safety model applies beyond this repository] → Mitigation: document that this change hardens only OpenPlate's checked-in helpers.

## Migration Plan

1. Add the repo-safety requirements and manual-test requirement deltas.
2. Update the shared manual-test runner so git-mutating setup occurs only inside a temporary repo-shaped sandbox.
3. Add fail-fast validation for unsafe target paths before any git mutation.
4. Update manual-test docs and agent guidance to describe the sandbox requirement.
5. Re-run the relevant manual workflows in the hardened sandboxed mode.

Rollback strategy: revert the script and documentation changes if the sandbox approach proves unworkable, but retain the requirement to avoid reintroducing unsafe direct mutation of the live checkout.

## Open Questions

- Should OpenPlate also add a small reusable helper library or script for safe disposable git repo creation so future repo-owned test utilities do not re-implement the same checks?
