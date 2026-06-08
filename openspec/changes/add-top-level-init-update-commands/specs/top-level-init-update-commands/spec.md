## ADDED Requirements

### Requirement: Top-level init is the primary initialization command
OpenPlate SHALL provide `openplate init` as a first-class top-level command for project initialization. `openplate init` MUST expose the init options and shared project-runtime options required to perform the same initialization workflow currently handled by the project init runtime path.

#### Scenario: Top-level init parses a template source
- **WHEN** a user runs `openplate init https://example.com/template.git#main`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-init execution flow

#### Scenario: Top-level init accepts shared project options
- **WHEN** a user runs `openplate init --project-folder ./workspace --ask-hidden https://example.com/template.git#main`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level init command

### Requirement: Top-level update is the primary update command
OpenPlate SHALL provide `openplate update` as a first-class top-level command for project updates. `openplate update` MUST expose the update options and shared project-runtime options required to perform the same update workflow currently handled by the project update runtime path.

#### Scenario: Top-level update parses successfully
- **WHEN** a user runs `openplate update`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-update execution flow

#### Scenario: Top-level update accepts shared project options
- **WHEN** a user runs `openplate update --project-folder ./workspace --ask-again`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level update command

### Requirement: Legacy project init and update commands remain supported
OpenPlate SHALL continue to accept `openplate project init` and `openplate project update` as backward-compatible command forms. The legacy commands MUST preserve the behavior and option set of the corresponding top-level commands.

#### Scenario: Legacy project init remains valid
- **WHEN** a user runs `openplate project init https://example.com/template.git#main`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same initialization behavior as `openplate init https://example.com/template.git#main`

#### Scenario: Legacy project update remains valid
- **WHEN** a user runs `openplate project update --update-full`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same update behavior as `openplate update --update-full`

### Requirement: Top-level help advertises only the new primary commands
OpenPlate top-level help SHALL advertise `init` and `update` as the supported project workflow commands. The legacy `project` command MUST remain functional but MUST NOT appear in top-level help output.

#### Scenario: Top-level help shows init and update
- **WHEN** a user runs `openplate --help`
- **THEN** the help output lists `init` and `update` as available commands

#### Scenario: Top-level help hides project compatibility command
- **WHEN** a user runs `openplate --help`
- **THEN** the help output does not list `project` as an available top-level command

### Requirement: Documentation presents top-level init and update as the supported syntax
OpenPlate documentation SHALL show `openplate init` and `openplate update` in command examples and primary usage guidance. Documentation MAY mention `openplate project init` and `openplate project update` only as backward-compatible legacy forms.

#### Scenario: Command documentation uses top-level examples
- **WHEN** a user reads the command documentation or README examples for initialization and update
- **THEN** the examples use `openplate init` and `openplate update` as the primary syntax