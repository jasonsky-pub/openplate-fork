## MODIFIED Requirements

### Requirement: Top-level init is the primary initialization command
OpenPlate SHALL provide `openplate init` as a first-class top-level command for project initialization. `openplate init` MUST expose the init options and shared project-runtime options required to perform the same initialization workflow currently handled by the project init runtime path.

#### Scenario: Top-level init parses a template source
- **WHEN** a user runs `openplate init https://example.com/template.git#main`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-init execution flow

#### Scenario: Top-level init accepts shared project root option
- **WHEN** a user runs `openplate init --project-root ./workspace --ask-hidden https://example.com/template.git#main`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level init command

### Requirement: Top-level update is the primary update command
OpenPlate SHALL provide `openplate update` as a first-class top-level command for project updates. `openplate update` MUST expose the update options and shared project-runtime options required to perform the same update workflow currently handled by the project update runtime path.

#### Scenario: Top-level update parses successfully
- **WHEN** a user runs `openplate update`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-update execution flow

#### Scenario: Top-level update accepts shared project root option
- **WHEN** a user runs `openplate update --project-root ./workspace --ask-again`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level update command

### Requirement: Legacy project init and update commands remain supported
OpenPlate SHALL continue to accept `openplate project init` and `openplate project update` as backward-compatible command forms. The legacy commands MUST preserve the behavior and option set of the corresponding top-level commands.

#### Scenario: Legacy project init remains valid
- **WHEN** a user runs `openplate project init https://example.com/template.git#main`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same initialization behavior as `openplate init https://example.com/template.git#main`

#### Scenario: Legacy project init accepts project root option
- **WHEN** a user runs `openplate project init --project-root ./workspace https://example.com/template.git#main`
- **THEN** OpenPlate accepts the shared project root option on the legacy compatibility command

#### Scenario: Legacy project update remains valid
- **WHEN** a user runs `openplate project update --update-full`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same update behavior as `openplate update --update-full`

### Requirement: Documentation presents top-level init and update as the supported syntax
OpenPlate documentation SHALL show `openplate init` and `openplate update` in command examples and primary usage guidance. Documentation MAY mention `openplate project init` and `openplate project update` only as backward-compatible legacy forms.

#### Scenario: Command documentation uses top-level examples
- **WHEN** a user reads the command documentation or README examples for initialization and update
- **THEN** the examples use `openplate init` and `openplate update` as the primary syntax

#### Scenario: Command documentation uses project root terminology
- **WHEN** a user reads the shared project-runtime option documentation
- **THEN** the documentation names `--project-root` as the root-selection option for init and update

## ADDED Requirements

### Requirement: Legacy project-folder option is rejected with migration guidance
OpenPlate SHALL reject `--project-folder` on top-level and legacy init, update, and verify command paths. The rejection message MUST tell the user to use `--project-root` instead.

#### Scenario: Top-level init rejects project-folder
- **WHEN** a user runs `openplate init --project-folder ./workspace https://example.com/template.git#main`
- **THEN** OpenPlate rejects the command
- **THEN** the error message tells the user to use `--project-root`

#### Scenario: Top-level update rejects project-folder
- **WHEN** a user runs `openplate update --project-folder ./workspace`
- **THEN** OpenPlate rejects the command
- **THEN** the error message tells the user to use `--project-root`

#### Scenario: Legacy verify rejects project-folder
- **WHEN** a user runs `openplate project verify --project-folder ./workspace`
- **THEN** OpenPlate rejects the command
- **THEN** the error message tells the user to use `--project-root`## MODIFIED Requirements

### Requirement: Top-level init is the primary initialization command
OpenPlate SHALL provide `openplate init` as a first-class top-level command for project initialization. `openplate init` MUST expose the init options and shared project-runtime options required to perform the same initialization workflow currently handled by the project init runtime path.

The shared root-selection option for init SHALL be named `--project-root`.

#### Scenario: Top-level init parses a template source
- **WHEN** a user runs `openplate init https://example.com/template.git#main`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-init execution flow

#### Scenario: Top-level init accepts shared project options
- **WHEN** a user runs `openplate init --project-root ./workspace --ask-hidden https://example.com/template.git#main`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level init command

### Requirement: Top-level update is the primary update command
OpenPlate SHALL provide `openplate update` as a first-class top-level command for project updates. `openplate update` MUST expose the update options and shared project-runtime options required to perform the same update workflow currently handled by the project update runtime path.

The shared root-selection option for update SHALL be named `--project-root`.

#### Scenario: Top-level update parses successfully
- **WHEN** a user runs `openplate update`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate routes the invocation through the existing project-update execution flow

#### Scenario: Top-level update accepts shared project options
- **WHEN** a user runs `openplate update --project-root ./workspace --ask-again`
- **THEN** OpenPlate accepts the shared project-runtime options on the top-level update command

### Requirement: Legacy project init and update commands remain supported
OpenPlate SHALL continue to accept `openplate project init` and `openplate project update` as backward-compatible command forms. The legacy commands MUST preserve the behavior and option set of the corresponding top-level commands, including the renamed `--project-root` shared option.

#### Scenario: Legacy project init remains valid
- **WHEN** a user runs `openplate project init https://example.com/template.git#main`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same initialization behavior as `openplate init https://example.com/template.git#main`

#### Scenario: Legacy project update remains valid
- **WHEN** a user runs `openplate project update --update-full`
- **THEN** OpenPlate parses the command successfully
- **THEN** OpenPlate performs the same update behavior as `openplate update --update-full`

#### Scenario: Legacy command accepts the renamed root option
- **WHEN** a user runs `openplate project update --project-root ./workspace --update-full`
- **THEN** OpenPlate accepts the renamed shared root-selection option on the legacy command form

### Requirement: Documentation presents top-level init and update as the supported syntax
OpenPlate documentation SHALL show `openplate init` and `openplate update` in command examples and primary usage guidance. Documentation MAY mention `openplate project init` and `openplate project update` only as backward-compatible legacy forms.

Documentation SHALL use `--project-root` when showing the shared root-selection option.

#### Scenario: Command documentation uses top-level examples
- **WHEN** a user reads the command documentation or README examples for initialization and update
- **THEN** the examples use `openplate init` and `openplate update` as the primary syntax

#### Scenario: Command documentation uses the renamed root option
- **WHEN** a user reads documentation that shows the shared root-selection option
- **THEN** the documentation uses `--project-root` rather than `--project-folder`