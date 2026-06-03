## ADDED Requirements

### Requirement: Project init accepts exactly one URL source
The `openplate project init` command SHALL accept exactly one template source reference, supplied either as a positional URL argument or through `-r` / `--url`. The command MUST reject invocations that provide both forms at the same time. The command MUST continue to require an explicit branch or tag fragment in the source reference unless `--allow-default-branch` is supplied.

#### Scenario: Positional URL source
- **WHEN** a user runs `openplate project init <repo-url>#<ref>`
- **THEN** OpenPlate treats the positional argument as the template source reference

#### Scenario: Legacy URL flag
- **WHEN** a user runs `openplate project init -r <repo-url>#<ref>`
- **THEN** OpenPlate accepts the source reference and initializes from the same URL-based source flow as the positional form

#### Scenario: Conflicting URL inputs
- **WHEN** a user supplies both a positional source reference and `-r` / `--url`
- **THEN** OpenPlate rejects the command and reports that only one URL source may be provided

#### Scenario: Missing ref without override
- **WHEN** a user supplies a URL source reference without `#<ref>` and does not pass `--allow-default-branch`
- **THEN** OpenPlate rejects the command and reports that a branch or tag is required

### Requirement: Removed init source options are rejected with migration guidance
The `openplate project init` command MUST reject `-n` / `--name` and `-f` / `--folder` source options. The rejection message MUST direct users to the supported URL-based replacements.

#### Scenario: Removed name source option
- **WHEN** a user runs `openplate project init -n <template-name>#<ref>`
- **THEN** OpenPlate rejects the command and explains that explicit URL sources must be used instead

#### Scenario: Removed folder source option
- **WHEN** a user runs `openplate project init -f <folder>`
- **THEN** OpenPlate rejects the command and explains that local Git repositories must be referenced with `file://`

### Requirement: URL source references support optional template paths
OpenPlate SHALL support URL source references in the form `<repo-location>[?path=<relative-template-subdir>][#<ref>]`. When `path` is present, OpenPlate MUST normalize it as a relative path and MUST reject values that are empty, absolute, or resolve outside the cloned repository.

#### Scenario: Remote repository sub-folder
- **WHEN** a user runs `openplate project init "https://github.com/my-org/template-catalog.git?path=python/api#v1"`
- **THEN** OpenPlate clones the repository at `https://github.com/my-org/template-catalog.git`
- **THEN** OpenPlate uses `python/api` inside the clone as the template root

#### Scenario: Invalid template path
- **WHEN** a user supplies `?path=../outside`
- **THEN** OpenPlate rejects the source reference and reports that the template path must stay within the repository

### Requirement: URL source references support file URLs
OpenPlate SHALL accept Git-compatible `file://` URLs anywhere a URL source reference is accepted, including positional invocation and `-r` / `--url` invocation.

#### Scenario: File URL source
- **WHEN** a user runs `openplate project init "file:///C:/repos/template-catalog?path=python/api#main"`
- **THEN** OpenPlate clones the repository from the `file://` location
- **THEN** OpenPlate uses the selected template path inside that cloned repository

### Requirement: Documentation describes supported project init URL formats
OpenPlate documentation SHALL describe the supported `project init` URL forms, including positional URL usage, `-r` / `--url` compatibility, SSH and HTTPS Git URLs, `file://` URLs, optional `?path=` sub-folder selection, `#<ref>` selection, and `--allow-default-branch` behavior.

#### Scenario: Command documentation examples
- **WHEN** a user reads the `project init` command documentation
- **THEN** the documentation includes examples for remote Git URLs, `file://` URLs, positional URL invocation, and repository sub-folder selection with `?path=`