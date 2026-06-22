## ADDED Requirements

### Requirement: Info prints human-readable project inspection from tracked templates
OpenPlate SHALL provide a human-readable project inspection command that reports tracked template state for the selected project root.

By default, `openplate info` SHALL load `.openplate.project.yaml`, inspect each tracked template source, and print a grouped report for each tracked template instance.

When template inspection succeeds, each tracked template group SHALL report:
- the tracked template source reference
- the tracked project-relative destination folder
- the tracked provenance when available
- saved template version information when available
- each in-scope non-hidden parameter currently exposed by the existing prompt-metadata collection path

For each reported parameter, the human-readable output SHALL include the parameter name and current answer value, and SHALL also include the prompt metadata available from template inspection such as description, default value, existing saved override, requiredness, and choice set when present.

The command SHALL print human-readable text rather than prompt JSON.

#### Scenario: Resolved info prints tracked templates with prompt details
- **WHEN** a user runs `openplate info` for a project whose tracked template sources can be inspected
- **THEN** OpenPlate prints one human-readable section per tracked template instance
- **AND** each section includes the template source reference, destination folder, and the visible parameters exposed by template inspection
- **AND** each reported parameter includes its current answer value and any available prompt description and default metadata

#### Scenario: Resolved info fails when a tracked template cannot be inspected
- **WHEN** a user runs `openplate info`
- **AND** one or more tracked template sources cannot be fully inspected
- **THEN** OpenPlate fails the command instead of printing partial resolved output

### Requirement: Offline info reports only persisted project-file data
`openplate info --offline` SHALL inspect only `.openplate.project.yaml` for the selected project root and SHALL NOT fetch, clone, or otherwise inspect tracked template sources.

Offline info SHALL report persisted tracked-template fields such as template source reference, destination folder, provenance when available, stored version, and saved parameter overrides.

Offline info SHALL NOT report prompt descriptions, defaults, choices, or other metadata that requires template inspection.

#### Scenario: Offline info skips template inspection
- **WHEN** a user runs `openplate info --offline`
- **THEN** OpenPlate reads the selected project's tracked template entries without fetching template sources
- **AND** the output is limited to data already persisted in `.openplate.project.yaml`

### Requirement: Info can include hidden parameters only during resolved inspection
`openplate info` SHALL omit hidden parameters by default using the same hidden-parameter inclusion behavior already used by the existing prompt-metadata collection path.

When a user runs `openplate info --show-hidden`, OpenPlate SHALL include the additional parameters that the existing prompt-metadata collection path exposes when hidden parameters are enabled.

`openplate info --offline --show-hidden` SHALL be rejected because offline inspection does not load the template metadata required to determine hidden parameter visibility.

#### Scenario: Default info omits hidden parameters
- **WHEN** a user runs `openplate info`
- **THEN** OpenPlate omits parameters that are not exposed by the normal hidden-parameter rules of the prompt-metadata collection path

#### Scenario: Show-hidden includes hidden parameters during resolved inspection
- **WHEN** a user runs `openplate info --show-hidden`
- **THEN** OpenPlate includes the additional parameters exposed when hidden prompt parameters are enabled for template inspection

#### Scenario: Show-hidden is rejected in offline mode
- **WHEN** a user runs `openplate info --offline --show-hidden`
- **THEN** OpenPlate rejects the command instead of attempting offline hidden-parameter reporting

### Requirement: OpenPlate persists template provenance for tracked project templates
OpenPlate SHALL persist tracked template provenance in `.openplate.project.yaml` when the command flow knows whether a tracked template was directly requested or inherited from a sibling declaration.

The persisted provenance values SHALL be `requested` and `inherited`.

Direct init of a template SHALL record that template as `requested`.

When recursive sibling processing adds a previously untracked sibling template to the project configuration, OpenPlate SHALL record that sibling as `inherited`.

If a later direct init targets a tracked template already marked `inherited`, OpenPlate SHALL promote that tracked template to `requested`.

Once a tracked template is marked `requested`, later sibling discovery SHALL NOT demote it back to `inherited`.

When provenance is absent from an older project file, OpenPlate SHALL continue to read the project file successfully and SHALL treat the provenance as unknown for display purposes.

#### Scenario: Direct init records requested provenance
- **WHEN** a user directly initializes a template into a project
- **THEN** the tracked template entry written to `.openplate.project.yaml` records provenance `requested`

#### Scenario: Sibling discovery records inherited provenance
- **WHEN** recursive processing adds a new sibling template to the tracked project configuration
- **THEN** the added tracked template entry records provenance `inherited`

#### Scenario: Direct init promotes inherited provenance
- **WHEN** a tracked template entry already exists with provenance `inherited`
- **AND** a later direct init targets that same tracked template identity
- **THEN** OpenPlate updates the tracked template entry to provenance `requested`

#### Scenario: Older project files remain readable without provenance
- **WHEN** `.openplate.project.yaml` contains tracked templates without a provenance field
- **THEN** OpenPlate reads the project file successfully
- **AND** info output does not mislabel the missing provenance as `requested` or `inherited`