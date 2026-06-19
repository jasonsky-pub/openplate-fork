# Templates

In contrast to some template tools, in openplate, templates are NOT code (although they can use code).
Instead, templates are:

- Simple files in the format they will be used
- Dynamic data is handled by using the Liquid template format
- Renaming files and rules are handled with regular expressions
- Templates are able to ask questions of the user and use the answers in the templates

# Template format

All templates are a git repository, the openplate tool will handle downloading and applying them.

# Template Config file

All templates should have a file ```openplate.template.yaml``` to describe the template to the openplate tool

# Sections

Inside this yaml file, there are different sections.

## Default Dest folder

Every template must specify a default folder to use for it's "dest_folder".  If one is not specified, it defaults to the root of the project.

- Example:
  
  ```yaml
  default_dest_folder: "src"
  ```
  
  Within the project, this value is available as the variable ```dest_folder```
  This value is overridable per project when doing an init by passing ```--dest-folder=src```, or in a sibling reference.

## Parameters

In this section, questions to be asked to the user should be present, these are then saved with the destination project.

- Example:
  
  ```yaml
  parameters:
      - name: "project_namespace"
        description: "Namespace For The Project, (Example: Org.Service.Name)"
  ```
  
  This parameter will be asked repeatedly until the user provides an answer (required).

To use these values in a template, make sure the file is a "replacement path" and use liquid format
ex:

```
    This is the project namespace: {{ project_namespace }}
```

### Built-in Template Variables

Built-in template variables, Git URL variants, runtime-only metadata rules, and deprecated compatibility aliases are documented in [docs/template-parameters.md](template-parameters.md).

### Default

Parameters can have a default value:

```yaml
parameters:
    - name: "data_retention_days"
      description: "Days to Keep Data Before auto-expiration (0 is disabled, NOT RECOMMENDED)"
      default: 90
```

In the above case, the question will only be asked once, and the default value will be used if the user does not specify a value.

You can use liquid syntax and **SOME** variables in this property. Only the built-in properties will be resolvable, such as:

- dest_folder
- project_folder_name
- project_git_mode

For the full built-in variable reference, including Git-scoped variables and deprecated aliases, see [docs/template-parameters.md](template-parameters.md).
- Example:
  
  ```yaml
  parameters:
      - name: "solution_name"
        type: string
        prompt: "Solution file name"
        default: "{{{ project_folder_name }}}"
        hidden: True
  ```

### "Hidden"

When we have a question that ordinarily a user will not want to answer, but we still want to provide a way to override it, the hidden attribute may be specified:

```yaml
parameters:
    - name: "data_retention_days"
      description: "Days to Keep Data Before auto-expiration (0 is disabled, NOT RECOMMENDED)"
      default: 90
      hidden: True
```

In order for a user to specify it interactively, they need to pass "--ask-hidden" to their command and possibly "--ask-again".

The same `--ask-hidden` flag also controls prompt JSON scope. Hidden parameters are included in `openplate project print-init-json` output only when `--ask-hidden` is used, and hidden values from `openplate init --prompts-json-file` or `openplate init --prompts-json-stdin` are applied only when `--ask-hidden` is active for that command.

### "Conditionally Hidden"

When a parameter should become hidden or visible based on project liquid logic, the `conditionally_hidden` attribute may be specified:

```yaml
parameters:
    - name: "deployment_type"
      description: "Type of Deployment to use"
      default: "lambda"

    - name: "instance_type"
      description: "EC2 instance type"
      default: "t3.small"
      conditionally_hidden: "{{% if deployment_type == 'ec2' %}}true{{% else %}}false{{% endif %}}"
```

- This property uses the project's liquid syntax, just like conditional sibling templates.
- It can use the same built-in values as `default`, plus parameter answers from earlier parameters in the file.
- Parameters are processed in order, so only parameters listed earlier in the file are guaranteed to be available.
- The rendered value must be `true` or `false`.
- If the rendered value is `false`, the parameter is treated as hidden.
- If the rendered value is `true`, the parameter remains visible.
- You cannot specify `hidden` and `conditionally_hidden` on the same parameter.
- If `conditionally_hidden` is specified, `default` is required and may be blank.
- `--ask-hidden` still allows the user to answer a conditionally hidden parameter because this feature changes hiddenness, not the existence of the parameter.

### Choices (v1.0.94)

Some parameters may have a set of choices, in this case, the user will be prompted to select one of the choices:

```yaml
parameters:
    - name: "deployment_type"
      description: "Type of Deployment to use"
      choices:
        - "Docker"
        - "Kubernetes" 
        - "None"
```

If a user enters a value other than the ones listed, they will be re-prompted until they enter a valid value.  If a parameter has a choices list and has a default which is not in that list, an error will occur while trying to use the template. 

## Replacement paths

This section is where we describe files which should be processed with the liquid template engine.  Anything not matching these paths will simply be copied

- Example:
  
  ```yaml
  replacement_paths:
      - "\\.embark"
      - ".*\\.yaml"
  ```
- Example with "*.yml" but "except static.template.yml"
  
  ```yaml
  replacement_paths:
      - ".*(?<!\\.static\\.template)\\.yml"
  ```

Openplate uses the Liquid Template language,
For more information on how to use liquid template format in a replacement file:
[See Docs](https://shopify.github.io/liquid/basics/introduction/)

** Note: File names are also replaceable **

## Readonly paths

These paths are "owned by the template" in the destination project.

- This means the "update" feature will overwrite them even if the file has been manually changed by a developer in the destination.
- The files will also be marked readonly in the destination project folder
- Example:
  
  ```yaml
  readonly_paths:
      - ".*/Template/.*"
      - ".*\\.template\\.md"
      - ".*\\.template\\.md"
      - ".*\\.template\\.yaml"
      - "nuget.config"
  ```
  
  Note: You can now use liquid (ex: variable replacements) in this property

## Optional paths

These paths are ignored if the file already exists in the destinatiojn project at init or update time.  This is especially useful for files where templates might overlap, but don't need to be merged. 

- Example:
  
  ```yaml
  optional_paths:
      - "\\.gitignore"
  ```
  
  Note: You can now use liquid (ex: variable replacements) in this property

## Rename rules

These rules rename a file from one name in the template repo to another name in the destination project
A common example which allows both template and destination project to have a readme.md:

```yaml
rename_rules:
    "readme.project.md": "readme.md"
```

Note: You can now use liquid (ex: variable replacements) in this property

## Ignore paths

These paths are ignored by openplate, they are files in the template repo which are not to be copied to the destination project
Example:

```yaml
ignore_paths:
    - "^readme\\.md$"
    - openplate.template.yaml
    - "old_files"
    - "\\.concourse/old_files.*"
```

Note: You can now use liquid (ex: variable replacements) in this property

## Remove Files:

If you want the template to remove files (On update), you can add those files to a list named remove_files

```yaml
remove_files:
    - file1.txt
    - .concourse/file2.csv
```

Note: You can now use liquid (ex: variable replacements) in this property

## Other Options:

The following may be overridden to change the escape characters used by the template replacement:

```yaml
    override_tag_start: "{%"
    override_tag_end: "%}"
    override_statement_start: "{{"
    override_statement_end: "}}"
```

## Config Files

If configuration is needed from the project, the following may be done:

- Add a yaml file with default configuration values to the template
  
  Location: config/my-template-settings.yaml
  
  ```yaml
  setting1: "test"
  setting2:
    setting2A: "value"
  ```

- If the project wants to override these, they can place the file in the same location in the project before running init or update
  
  - In this scenario, it will use the project version instead of the template version

- Add the following section into the template:
  
  ```yaml
  config_files:
      my_settings: "config/my-template-settings.yaml"
  ```

- In the template, you can reference the liquid values such as: ```{{my_settings.setting1}} and {{my_settings.setting2.setting2A}}```

## Minimum Openplate version:  (v0.0.15)

To specify that the template requires a specific openplate version or higher:

```yaml
min_tool_version: "0.0.15"
```

This functionality works as-of version "0.0.15", if the user has an older version in place it will not work.

## Required Sibling Templates (v0.0.16)

When a template requires that the consumer inherits from a sibling, this is the way to specify it:

```yaml
require_sibling_templates:
    -   template_url: git@github.com:my-org/template-repo.git
        dest_folder: "{{{ dest_folder }}}" # required value
        parameters:
            # can specify replacements in the parameters based on the current project replacement characters
            project_namespace: "Testing{{{project_namespace}}}"
            project_short_name: "none"
            nuget_publish_folder: ""
```

Note: You can now use liquid (ex: variable replacements) in this property

## Conditional Siblings (v1.0.94)

When a sibling template should not always be added, the following syntax can be used:

```yaml
require_sibling_templates:
    -   template_url: git@github.com:my-org/template-repo.git
        dest_folder: "{{{ dest_folder }}}" # required value
        condition: "{{% if deployment_type == 'ec2' %}}true{{% else %}}false{{% endif %}}"
        parameters:
            # can specify replacements in the parameters based on the current project replacement characters
            project_namespace: "Testing{{{project_namespace}}}"
            project_short_name: "none"
            nuget_publish_folder: ""
```

- If the rendered value of "condition" is:
  - "true", "1", or "yes" -> Included
  - "false", "0", "no" -> Excluded
- This check is case-insensitive, so "Yes" also qualifies as "yes".

## Ignore Inherited Files (v0.0.17)

When a template is also a project, it will inherit files from it's super-template.  There is now an option to NOT send these fils to project which ue this template.

```yaml
ignore_inherited_files: NONE # Don't ignore, same as not specified
#or
ignore_inherited_files: ALL # Ignore ALL inherited files
#or
ignore_inherited_files: READONLY # Only ignore readonly inherited files, others should be sent
```

## Init Commands (v0.0.22)

This setting is used when a template requires specific commands to run after init. IE: Adding a project template to a solution.

```yaml
init_commands:
    - "dotnet sln add src/{{{ initial_project_namespace }}}/{{{ initial_project_namespace }}}.csproj"
```

## Multiplexing files:

In order to have one file in a template become many files in the project, add this to the project file:

```yaml
multiplex:
    - source: "{{{ dest_folder }}}/src/{{{ settings.net_project_name }}}/appsettings.multiplex.json"
      destination: "{{{ dest_folder }}}/src/{{{ settings.net_project_name }}}/appsettings.test.{{{ multiplex_item }}}.json"
      items: "environments.environments"
```

- The file in "source" will not be copied/run normally it will only be multiplexed
- The file in source is an exact file name where the replacements will not be run until it is time to copy to the destination
- The file in destination is the file which will have replacements run on it
- The items setting is the list of items to be used to create the files
- The value of items is a reference to an object, a literal value is not currently supported
- The object in items is the object from parameters or configuration which has either:
  - a csv string
  - a list of strings
- For every file, the "multiplex_item" variable will be set to the value of the item in the list

## Conditional files/folders (v1.0.98):

In order to conditionally include files/folders in a template:

```yaml
conditional:
    - location: "{{{ dest_folder }}}/some-file"
      condition: "{{% if deployment_type == 'ec2' %}}true{{% else %}}false{{% endif %}}"
```

- The location condition will NOT be replaced, it is used as-is to match files or folders.
- The condition is rendered before checking if the value is True
- If the rendered value of "condition" is:
  - "true", "1", or "yes" -> Included
  - "false", "0", "no" -> Excluded
- This check is case-insensitive, so "Yes" also qualifies as "yes".
- This check also applies to directories
