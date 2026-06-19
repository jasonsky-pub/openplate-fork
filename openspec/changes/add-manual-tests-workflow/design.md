## Context

OpenPlate has focused automated tests and some external trial-run material, but it does not currently keep a repo-owned manual-test workflow that contributors can run end to end from inside this repository. The missing pieces are a stable folder layout, exact checked-in commands, sanitized reusable fixtures, disposable working directories, and scripts that make manual verification reproducible instead of ad hoc.

This is a cross-cutting documentation-and-tooling change. It touches repository guidance, ignored workspace conventions, executable helper scripts, staged fixtures, and an explicit contract for how manual test cases are authored and maintained as features evolve.

## Goals / Non-Goals

**Goals:**
- Add a versioned `manual-tests/` directory that is the source of truth for end-to-end manual testing.
- Document every full executable manual case needed to cover the app's user-visible feature surface.
- Require each case document to include exact commands or exact script invocations instead of asking a future agent or contributor to reconstruct them.
- Keep reusable fixtures under `manual-tests/templates/` and keep disposable execution output in gitignored working folders.
- Provide repo-owned scripts for running manual cases and cleaning up their generated workspaces.
- Add an `AGENTS.md` entry that directs future agents to the manual-test workflow.
- Ensure all checked-in fixtures and references remain public, generic, and free of internal or company-specific content.
- Make the initial manual suite concrete by naming the first case files, the shared script entrypoints, and the exact disposable folder layout they use.
- Require a coverage matrix that explicitly accounts for visible CLI features that are manual-covered, automated-only, or intentionally excluded, so no command or meaningful flag silently falls through the cracks.

**Non-Goals:**
- Replace the automated pytest suite or the existing trial-run automation with manual tests.
- Encode every validation step as automation; manual cases may still require explicit human inspection steps.
- Introduce private fixture repositories, private URLs, or company-specific template content.
- Auto-discover feature coverage from code; the initial workflow may use a curated case list.

## Decisions

### 1. Use a dedicated `manual-tests/` workspace with stable authoring conventions

The implementation should add a repository-owned `manual-tests/` tree with these core roles:
- `manual-tests/index.md`: operator guide, prerequisites, execution order, case inventory, and feature-coverage map
- `manual-tests/case-X.md`: one checked-in document per manual case, numbered for stable references
- `manual-tests/case-X.sh`: optional adjacent script for any case whose command sequence is too long or stateful to keep inline in Markdown
- `manual-tests/templates/`: checked-in public fixtures and template inputs used by the cases
- `manual-tests/run-manual-tests.sh`: shared bash entrypoint for preparing and running one case or all seeded cases
- `manual-tests/cleanup-manual-tests.sh`: shared bash entrypoint for removing disposable manual-test state
- gitignored working folders `manual-tests/work/<case-id>/` and `manual-tests/artifacts/<case-id>/` for generated repos, temp directories, prompt JSON files, and captured outputs

Numbered case files keep references stable in docs, pull requests, and future agent instructions. The index should describe what each case covers and when it should be run.

The initial case inventory should be fixed up front so implementation does not invent coverage later:
- `case-1.md`: bootstrap and URL-source init covering config persistence plus the primary init source-selection workflow
- `case-2.md`: interactive init behavior covering prompt-driven init, hidden parameters, `conditionally_hidden`, and template-command authorization behavior
- `case-3.md`: prompt JSON workflow covering `openplate project print-init-json`, `openplate project print-init-json --verbose`, `openplate init --prompts-json-file`, and `openplate init --prompts-json-stdin`
- `case-4.md`: lifecycle maintenance covering `openplate update` and `openplate project verify`, including a deliberate drift or missing-file condition that makes verify meaningful before update repairs it

The index should explicitly map those four cases to the current documented command surface in `docs/commands.md`.

This split is intentional:
- `config set` and `config get` are folded into `case-1` because config is primarily valuable as persisted setup for downstream init behavior rather than as an isolated end-to-end workflow
- prompt JSON remains its own case because it is an alternate init interaction model with a different operator flow and different artifacts
- update and verify remain together because verify is most meaningful against drift that update may later repair

The index should also include a facet coverage matrix derived from:
- `docs/commands.md`
- `readme.md`
- the visible parser surface in `src/openplate/__main__.py`
- the current focused parser/runtime regression tests for compatibility-only behaviors

For each facet, the matrix should assign one of three dispositions:
- `manual:<case-id>` when the facet is exercised by a numbered manual case
- `automated-only` when the facet is intentionally left to parser/runtime tests instead of manual runs
- `excluded` only when the repo intentionally does not cover it, with a short rationale

At minimum, the matrix should account for these feature groups:
- global CLI facets: `--version`, `--config-file`, `--project-folder`, `--ask-hidden`, `--ask-again`, `--ignore-tool-version`, `--debug`, `--automation`
- config facets: `config get`; `config set` with `--vcs-url`, `--template-prefix`, `--parameter-default` add/remove, and `--allow-template-commands`
- init facets: file-based source URLs, `?path=` sub-folder selection, explicit refs, `--allow-default-branch`, deprecated `-r/--url`, `--dest-folder`, `--no-cache`, `--overwrite`, `--ignore`, `--allow-template-commands`, hidden prompts, and `conditionally_hidden`
- prompt JSON facets: compact export, verbose export, file import, stdin import, hidden-scope behavior, dest-folder-independent node identity, and ignored extra node/answer behavior
- update and verify facets: `update`, `--update-missing`, `--update-full`, `--ask-again`, and `project verify`
- compatibility facets: legacy `project init/update` command paths and parser rejection of removed options such as old init source flags or removed prompt JSON flags on update

The goal is not to force every facet into a manual case. The goal is to ensure every facet has an explicit home or rationale.

The seeded case inventory should favor operator journeys over one-command-per-case decomposition. A command belongs in its own case only when it creates a materially different end-to-end workflow, fixture shape, or validation surface.

Alternatives considered:
- Reusing `docs/` for manual cases. Rejected because the workflow also needs fixtures and executable helper scripts, not just prose.
- Keeping manual cases in an external sibling repo. Rejected because the request is to make the repo self-contained and reviewable.

### 2. Case documents are the canonical execution contract

Each `manual-tests/case-X.md` should be written so a contributor can execute the case without inventing commands. The file should include:
- the feature areas covered by the case
- prerequisites specific to that case
- the exact commands to run, or the exact checked-in script path to invoke
- the expected automated outputs or exit conditions
- the explicit human validations that remain required after the script finishes
- cleanup notes when a case has special state beyond the shared cleanup script

If a case needs more than a short command block, the Markdown should point to an adjacent `case-X.sh` script and treat that script as the executable source of truth. The Markdown still owns the human validation checklist.

Each case document should follow a stable section structure so contributors and agents can scan them quickly:
- purpose / covered commands
- prerequisites
- exact commands to run
- expected scripted outputs
- manual validation checklist
- cleanup notes

Each case document should also name the specific matrix facets it satisfies so the coverage map stays traceable as features evolve.

Alternatives considered:
- Letting future agents reconstruct commands from general repo docs. Rejected because that recreates the current ambiguity.
- Keeping only scripts with no Markdown narrative. Rejected because manual validation steps and rationale still need prose.

### 3. Orchestration scripts should automate setup and cleanup, not hide validation

The manual-test workflow should include repo-owned scripts under `manual-tests/` for two shared jobs:
- running selected manual cases or preparing their workspaces
- cleaning up generated working folders and repos after a run

Because the repo ships and validates the manual workflow through bash, the shared orchestration scripts should use that convention. Case-specific `.sh` scripts remain allowed when a case needs a portable command bundle or a long linear shell flow, but the case document must show the exact invocation.

The run script should make it easy to execute one case or the full manual suite in a consistent location. It should accept a concrete case selector such as `-Case case-1`, `-Case case-2`, `-Case case-3`, `-Case case-4`, or `-Case all`, and it should write per-case outputs beneath `manual-tests/artifacts/<case-id>/` while keeping generated repos and workspaces beneath `manual-tests/work/<case-id>/`.

The cleanup script should remove only generated manual-test state beneath `manual-tests/work/<case-id>/` and `manual-tests/artifacts/<case-id>/` and must not touch checked-in fixtures.

Alternatives considered:
- One giant shell script for all cases. Rejected because it obscures per-case intent and makes targeted reruns harder.
- Cleanup by hand only. Rejected because disposable repos and temp folders will drift quickly.

### 4. Fixtures must be sanitized and separated from disposable state

All checked-in fixtures used by manual cases should live under `manual-tests/templates/` and must use generic names, public-safe placeholder URLs, and non-company-specific content. Generated repositories, transient clones, logs, and produced outputs should live in dedicated gitignored working folders outside `templates/`.

The manual workflow should not depend on network access or external template repositories. Instead, `manual-tests/run-manual-tests.sh` should materialize local git-backed template repos from the checked-in fixture directories, using local file URLs such as `file:///...#main` for the actual OpenPlate commands that the case documents record.

This separation keeps reviews clear:
- checked-in fixture inputs remain deterministic and reusable
- generated work products remain disposable and are easy to clean
- no manual case depends on private infrastructure or non-public template references

At minimum, the seeded fixtures should include:
- one config/init/update/verify fixture set that can initialize a project and later exercise update and verify against predictable files
- one prompt-JSON-oriented fixture set that includes hidden and `conditionally_hidden` parameters so prompt export/import and hidden-parameter scope can be checked end to end

Alternatives considered:
- Storing generated work products next to fixtures. Rejected because it makes cleanup and review noisy.
- Reusing existing checked-in examples with internal references. Rejected because the workflow must stay public-safe.

### 5. `AGENTS.md` should point future automation to the manual test source of truth

The repo currently has no `AGENTS.md`. This change should add one with a concise reference telling future agents that end-to-end manual execution guidance lives under `manual-tests/`, and that agents should prefer those checked-in commands and fixtures over reconstructing workflows from memory.

This keeps future edits and manual runs aligned with the repo-owned process instead of drifting into ad hoc instructions.

`AGENTS.md` should also tell agents to read `manual-tests/index.md` and the relevant `manual-tests/case-X.md` file before proposing or running end-to-end manual commands.

## Risks / Trade-offs

- [Manual cases can drift from the real CLI or fixture surface] -> Keep exact commands checked in and make the index the obvious review surface when features change.
- [A public fixture requirement may limit how closely fixtures mirror internal usage] -> Prefer generic fixtures that still exercise the same CLI behaviors and branching paths.
- [Bash orchestration on Windows requires careful path handling when launching Windows Python] -> Keep the shared workflow in checked-in `.sh` scripts and validate launcher/path conversion in the seeded cases.
- [Manual validation still requires human effort] -> Make each case explicit about what the scripts verify automatically versus what a human must inspect.

## Migration Plan

1. Add the `manual-tests/` directory structure, case authoring conventions, and index document.
2. Add public-safe fixture content under `manual-tests/templates/` and define gitignored working folders for generated state.
3. Add shared run and cleanup scripts plus any case-local scripts required by the initial case set.
4. Add numbered case documents for `case-1` through `case-4` that cover the current documented command surface with exact commands and validation checklists.
5. Add the coverage matrix to `manual-tests/index.md` and classify each visible command/flag/compatibility facet as manual-covered, automated-only, or excluded with rationale.
6. Add `AGENTS.md` guidance that points future agents to the manual-test workflow.
7. Validate the initial workflow by executing at least the seeded manual cases using only the checked-in instructions.

## Open Questions

None at this time.
