## ADDED Requirements

### Requirement: Templates declare whether they require last updater email
OpenPlate SHALL support a template configuration field named `requires_last_updater_email`.

If `requires_last_updater_email` is omitted or set to false, OpenPlate MUST treat the template as not requiring `last_updater_email` and MUST expose `last_updater_email` as an empty string when compiling runtime template options for that template.

If `requires_last_updater_email` is set to true, OpenPlate MUST treat the template as requiring operator consent before `last_updater_email` may be resolved or injected for that template.

#### Scenario: Template does not require last updater email
- **WHEN** a template configuration omits `requires_last_updater_email`
- **THEN** OpenPlate treats the template as not requiring `last_updater_email`
- **THEN** OpenPlate compiles `last_updater_email` as an empty string for that template

#### Scenario: Template requires last updater email
- **WHEN** a template configuration sets `requires_last_updater_email` to true
- **THEN** OpenPlate marks the template as requiring consent before resolving `last_updater_email`

### Requirement: Operators can pre-authorize last updater email usage
OpenPlate SHALL support persistent user configuration for `allow_last_updater_email` and a one-time `--allow-last-updater-email` CLI flag on init and update command forms.

When both are present, the CLI flag SHALL take precedence for the current run.

#### Scenario: Persistent user configuration allows email usage
- **WHEN** a user enables `allow_last_updater_email` in OpenPlate user configuration
- **THEN** a later requiring init or update run proceeds without prompting for consent

#### Scenario: One-time CLI flag allows email usage
- **WHEN** a user runs `openplate update --allow-last-updater-email`
- **THEN** a requiring template in that run proceeds without prompting for consent

### Requirement: Requiring templates prompt once or fail deterministically when consent is missing
When init or update encounters a template that requires `last_updater_email` and the current run is not already authorized, OpenPlate SHALL attempt to resolve consent exactly once for that run.

If the run is interactive, OpenPlate SHALL prompt the operator whether to allow `last_updater_email`.

If the operator approves, OpenPlate SHALL treat the run as authorized for the remainder of that init or update execution.

If the operator declines, OpenPlate SHALL fail the requiring template.

If the run is in automation mode or is consuming prompt JSON input, OpenPlate MUST NOT prompt and MUST instead treat consent as false and fail the requiring template.

#### Scenario: Interactive init approves consent
- **WHEN** a user runs an interactive `openplate init` for a template that requires `last_updater_email`
- **AND** no persistent or CLI allow setting is present
- **AND** the user answers yes to the consent prompt
- **THEN** OpenPlate resolves `last_updater_email`
- **THEN** OpenPlate continues the run without prompting again for later requiring templates in the same execution

#### Scenario: Interactive update declines consent
- **WHEN** a user runs an interactive `openplate update` and a tracked template requires `last_updater_email`
- **AND** no persistent or CLI allow setting is present
- **AND** the user answers no to the consent prompt
- **THEN** OpenPlate fails the requiring template

#### Scenario: Automation defaults consent to false
- **WHEN** a user runs `openplate init --automation` for a template that requires `last_updater_email`
- **AND** no persistent or CLI allow setting is present
- **THEN** OpenPlate does not prompt for consent
- **THEN** OpenPlate fails the requiring template

#### Scenario: Prompt JSON input defaults consent to false
- **WHEN** a user runs `openplate init <template> --prompts-json-file prompts.json`
- **AND** the template requires `last_updater_email`
- **AND** no persistent or CLI allow setting is present
- **THEN** OpenPlate does not prompt for consent
- **THEN** OpenPlate fails the requiring template

### Requirement: Project state persists last updater email only when tracked templates still require it
OpenPlate SHALL persist `last_updater_email` in `.openplate.project.yaml` only when at least one tracked template requires `last_updater_email` and the current project state has been authorized to use it.

If no tracked template requires `last_updater_email`, OpenPlate MUST clear `last_updater_email` when saving the project file.

#### Scenario: Requiring tracked template persists last updater email
- **WHEN** a project has at least one tracked template that requires `last_updater_email`
- **AND** consent has been granted for the run
- **THEN** OpenPlate saves `last_updater_email` in `.openplate.project.yaml`

#### Scenario: No tracked templates require last updater email
- **WHEN** a project save occurs and none of the tracked templates require `last_updater_email`
- **THEN** OpenPlate removes `last_updater_email` from `.openplate.project.yaml`