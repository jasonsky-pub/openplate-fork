## 1. Workspace structure and guidance

- [ ] 1.1 Add the `manual-tests/` directory skeleton with `index.md`, `run-manual-tests.sh`, `cleanup-manual-tests.sh`, `templates/`, `work/`, and `artifacts/`, then update root `.gitignore` so `manual-tests/work/<case-id>/` and `manual-tests/artifacts/<case-id>/` stay untracked.
- [ ] 1.2 Add `AGENTS.md` and point it to `manual-tests/index.md` plus the numbered case files as the source of truth for end-to-end manual execution guidance.
- [ ] 1.3 Define the shared manual-test process in `manual-tests/index.md`, including prerequisites, shared script entrypoints, workspace conventions, cleanup expectations, and the mapping from `case-1` through `case-4` to covered commands and features.
- [ ] 1.4 Add a feature/facet coverage matrix to `manual-tests/index.md` that accounts for every current CLI surface from `docs/commands.md`, `readme.md`, and `src/openplate/__main__.py`, marking each facet as `manual:<case-id>`, `automated-only`, or `excluded` with rationale.

## 2. Case inventory and staged fixtures

- [ ] 2.1 Define the seeded manual case inventory as `case-1` config persistence plus URL-source init, `case-2` interactive init with hidden and `conditionally_hidden`, `case-3` prompt JSON compact plus verbose export and import, and `case-4` update plus verify against intentional drift, and map those cases to the current documented command surface.
- [ ] 2.2 Stage public-safe fixture inputs under `manual-tests/templates/` for the seeded case set, including at least one lifecycle fixture and one prompt-JSON fixture, and ensure the checked-in content uses only generic names, local file-based sources, placeholder URLs where needed, and no company-specific references.
- [ ] 2.3 Author `manual-tests/case-1.md` through `manual-tests/case-4.md` with a stable structure covering the exact matrix facets each case satisfies, prerequisites, exact commands or script invocations, expected scripted outputs, explicit manual validations, and cleanup notes.

## 3. Execution scripts and workflow validation

- [ ] 3.1 Implement `manual-tests/run-manual-tests.sh` so it can run `case-1`, `case-2`, `case-3`, `case-4`, or `all`, materialize local git-backed template repos from `manual-tests/templates/`, write generated repos under `manual-tests/work/<case-id>/`, and write case outputs under `manual-tests/artifacts/<case-id>/`.
- [ ] 3.2 Implement `manual-tests/cleanup-manual-tests.sh` to remove only disposable state under `manual-tests/work/<case-id>/` and `manual-tests/artifacts/<case-id>/`, and add adjacent `manual-tests/case-X.sh` scripts only for cases whose command flow is too complex to keep inline.
- [ ] 3.3 Execute the seeded manual workflow using only the checked-in instructions and scripts, then update the docs, fixtures, helper scripts, and coverage matrix classifications to close any gaps found during that dry run.
