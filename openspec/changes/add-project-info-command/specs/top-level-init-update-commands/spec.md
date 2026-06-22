## ADDED Requirements

### Requirement: Top-level info is the primary inspection command
OpenPlate SHALL provide `openplate info` as a first-class top-level command for project inspection. `openplate info` MUST expose the shared project-runtime options required to inspect a project.

The shared root-selection option for info SHALL be named `--project-root`.

#### Scenario: Top-level info parses successfully
- **WHEN** a user runs `openplate info`
- **THEN** OpenPlate parses the command successfully
- **AND** OpenPlate routes the invocation through the project-info execution flow

#### Scenario: Top-level info accepts the shared root option
- **WHEN** a user runs `openplate info --project-root ./workspace`
- **THEN** OpenPlate accepts the shared project-runtime option on the top-level info command

### Requirement: Legacy project info command remains supported
OpenPlate SHALL continue to accept `openplate project info` as a backward-compatible command form. The legacy command MUST preserve the behavior and option set of `openplate info`, including the shared `--project-root` option.

#### Scenario: Legacy project info remains valid
- **WHEN** a user runs `openplate project info --project-root ./workspace`
- **THEN** OpenPlate parses the command successfully
- **AND** OpenPlate performs the same inspection behavior as `openplate info --project-root ./workspace`

## MODIFIED Requirements

### Requirement: Top-level help advertises only the new primary commands
OpenPlate top-level help SHALL advertise `init`, `update`, `verify`, and `info` as the supported project workflow commands. The legacy `project` command MUST remain functional but MUST NOT appear in top-level help output.

#### Scenario: Top-level help shows init, update, verify, and info
- **WHEN** a user runs `openplate --help`
- **THEN** the help output lists `init`, `update`, `verify`, and `info` as available commands

#### Scenario: Top-level help hides project compatibility command
- **WHEN** a user runs `openplate --help`
- **THEN** the help output does not list `project` as an available top-level command