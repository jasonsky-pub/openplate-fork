## ADDED Requirements

### Requirement: Persisted project template references use URL sources only
OpenPlate SHALL treat URL source references as the only supported persisted template source form in project configuration.

When loading `.openplate.project.yaml`, OpenPlate SHALL ignore `src_name`, `src_folder`, and `template_src_folder` when those values are missing, null, or blank.

When loading `.openplate.project.yaml`, OpenPlate MUST fail with a runtime error if `src_name`, `src_folder`, or `template_src_folder` contains a non-blank value. The error MUST explain that URL-backed template references are required.

OpenPlate runtime state MUST NOT retain populated `src_name`, `src_folder`, or `template_src_folder` values after load.

#### Scenario: Blank legacy template source fields are ignored
- **WHEN** a persisted project config includes `src_name: ""`, `src_folder: ""`, or `template_src_folder: ""`
- **THEN** OpenPlate loads the project config successfully
- **THEN** OpenPlate ignores those blank legacy fields

#### Scenario: Populated src_name is rejected on load
- **WHEN** a persisted project config includes `src_name: legacy-template`
- **THEN** OpenPlate fails to load the project config
- **THEN** the error explains that persisted template sources must use `src_url`

#### Scenario: Populated src_folder is rejected on load
- **WHEN** a persisted project config includes `src_folder: ./templates/example`
- **THEN** OpenPlate fails to load the project config
- **THEN** the error explains that local template repos must be referenced by URL instead

#### Scenario: Populated template_src_folder is rejected on load
- **WHEN** a persisted project config includes `template_src_folder: ./templates/example`
- **THEN** OpenPlate fails to load the project config
- **THEN** the error explains that URL-backed template references are required

### Requirement: Documentation omits legacy source-resolution configuration
OpenPlate documentation SHALL describe URL-backed template source references as the only supported source contract. Documentation MUST NOT present `vcs_url`, `template_prefix`, `src_name`, or `src_folder` as supported runtime configuration for project template resolution.

#### Scenario: Source configuration documentation uses URL-only guidance
- **WHEN** a user reads the command documentation or README guidance for template source selection
- **THEN** the documentation describes URL-backed template references only
- **THEN** the documentation does not describe legacy name-based or folder-based template source resolution as supported runtime behavior## ADDED Requirements

### Requirement: Persisted project template references remain URL-backed only
Project configuration data SHALL store and load template references through `src_url` only.

OpenPlate MUST reject non-blank legacy name- or folder-based source fields when loading persisted project configuration.

#### Scenario: Persisted blank legacy source fields are tolerated
- **WHEN** a tracked template entry contains blank `src_name` or `src_folder` values
- **THEN** OpenPlate ignores those blank fields and continues loading the template entry from `src_url`

#### Scenario: Persisted non-blank name source is rejected
- **WHEN** a tracked template entry contains a non-empty `src_name`
- **THEN** OpenPlate halts with a runtime error explaining that URL-backed template references are now required

#### Scenario: Persisted non-blank folder source is rejected
- **WHEN** a tracked template entry contains a non-empty `src_folder`
- **THEN** OpenPlate halts with a runtime error explaining that URL-backed template references are now required