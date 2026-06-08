## 1. Parser refactor

- [x] 1.1 Extract the shared project-runtime arguments into reusable parser helpers so the same option set can be attached to both top-level and legacy command paths.
- [x] 1.2 Add top-level `init` and `update` parsers that dispatch to the existing `project-init` and `project-update` runtime flows.
- [x] 1.3 Keep `project init` and `project update` as hidden compatibility parsers that share the same option definitions and behavior as the new top-level commands.

## 2. Help and documentation

- [x] 2.1 Update top-level help behavior so `openplate --help` shows `init` and `update` but does not list the legacy `project` compatibility command.
- [x] 2.2 Rewrite command documentation and README examples to use `openplate init` and `openplate update` as the primary syntax, with legacy `project` forms mentioned only as compatibility notes if needed.

## 3. Validation

- [x] 3.1 Add or update focused parser tests for `openplate init`, `openplate update`, and the legacy `openplate project init/update` compatibility forms.
- [x] 3.2 Add or update help/documentation validation to ensure top-level help advertises only the new commands and the visible examples match the new syntax.