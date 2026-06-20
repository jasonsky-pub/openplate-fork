## ADDED Requirements

### Requirement: Top-level verify is the primary verification command
OpenPlate SHALL provide `openplate verify` as a first-class top-level command for project verification. `openplate verify` MUST expose the shared project-runtime options required to perform the same verification workflow currently handled by the existing project verify execution path.

#### Scenario: Top-level verify parses successfully
- **WHEN** a user runs `openplate verify`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-verify execution flow

#### Scenario: Top-level verify accepts shared project root option
- **WHEN** a user runs `openplate verify --project-root ./workspace`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level verify command

### Requirement: Legacy project verify command remains supported
OpenPlate SHALL continue to accept `openplate project verify` as a backward-compatible command form. The legacy command MUST preserve the behavior and option set of `openplate verify`.

#### Scenario: Legacy project verify remains valid
- **WHEN** a user runs `openplate project verify --project-root ./workspace`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same verification behavior as `openplate verify --project-root ./workspace`

## MODIFIED Requirements

### Requirement: Top-level help advertises only the new primary commands
OpenPlate top-level help SHALL advertise `init`, `update`, and `verify` as the supported project workflow commands. The legacy `project` command MUST remain functional but MUST NOT appear in top-level help output.

#### Scenario: Top-level help shows init, update, and verify
- **WHEN** a user runs `openplate --help`
- **THEN** the help output lists `init`, `update`, and `verify` as available commands

#### Scenario: Top-level help hides project compatibility command
- **WHEN** a user runs `openplate --help`
- **THEN** the help output does not list `project` as an available top-level command

### Requirement: Documentation presents top-level init and update as the supported syntax
OpenPlate documentation SHALL show `openplate init`, `openplate update`, and `openplate verify` in command examples and primary usage guidance. Documentation MAY mention `openplate project init`, `openplate project update`, and `openplate project verify` only as backward-compatible legacy forms.

Documentation SHALL explain that users who need a non-default SSH key for SSH template URLs can export `GIT_SSH_COMMAND` before running OpenPlate.

#### Scenario: Command documentation uses top-level examples
- **WHEN** a user reads the command documentation or README examples for initialization, update, and verification
- **THEN** the examples use `openplate init`, `openplate update`, and `openplate verify` as the primary syntax

#### Scenario: Command documentation explains special SSH key usage
- **WHEN** a user reads the command documentation for running OpenPlate against SSH template URLs
- **THEN** the documentation shows how to export `GIT_SSH_COMMAND` before invoking OpenPlate