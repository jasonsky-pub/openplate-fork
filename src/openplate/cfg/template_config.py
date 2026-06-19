#
#              Copyright 2025 Comcast Cable Communications Management, LLC
#
#              Licensed under the Apache License, Version 2.0 (the "License");
#              you may not use this file except in compliance with the License.
#              You may obtain a copy of the License at
#
#              http://www.apache.org/licenses/LICENSE-2.0
#
#              Unless required by applicable law or agreed to in writing, software
#              distributed under the License is distributed on an "AS IS" BASIS,
#              WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#              See the License for the specific language governing permissions and
#              limitations under the License.
#
#              SPDX-License-Identifier: Apache-2.0
#
#              This product includes software developed at Comcast (https://www.comcast.com/).#
from enum import Enum
from typing import Optional

from openplate.cfg import serialization
from openplate.cfg.serialization import deserialize_string_list, deserialize_string_dictionary
from openplate.walk.recursive_walker import norm_relative_path


class TemplateConfigParameter:
    def __init__(
        self,
        name: str,
        description: str,
        default: str,
        hidden: Optional[bool],
        choices: Optional[list[str]],
        conditionally_hidden: Optional[str] = None
    ):
        if name is None:
            raise ValueError("name cannot be None")
        if description is None:
            raise ValueError("description cannot be None")
        self.name = name
        self.description = description
        self.default = default
        self.hidden = hidden
        self.choices = choices
        self.conditionally_hidden = conditionally_hidden

        if default is not None and choices is not None:
            if default not in choices:
                message_string = ", ".join(choices)
                raise ValueError(f"Default value '{default}' for parameter '{name}' is not in the choices: [{message_string}]")

        if self.hidden is not None and self.conditionally_hidden is not None:
            raise ValueError("A parameter cannot specify both hidden and conditionally_hidden")

        if self.hidden and self.default is None:
            raise ValueError("If a parameter is hidden, it must have a default")

        if self.conditionally_hidden is not None and self.default is None:
            raise ValueError("If a parameter uses conditionally_hidden, it must have a default")


class RequireSiblingTemplate:
    def __init__(
        self,
        template_url: str,
        dest_folder: Optional[str],
        parameters: Optional[dict[str, str]],
        condition: Optional[str] = None
    ):
        if template_url is None:
            raise TypeError
        self.template_url = template_url
        self.dest_folder = dest_folder
        self.parameters = parameters
        self.condition = condition


class MultiplexFile:
    def __init__(
        self,
        source: str,
        destination: str,
        items: str
    ):
        if source is None:
            raise TypeError
        if destination is None:
            raise TypeError
        if items is None:
            raise TypeError
        self.source = source
        self.destination = destination
        self.items = items


class ConditionalFile:
    def __init__(
        self,
        location: str,
        condition: str
    ):
        if location is None:
            raise TypeError
        if condition is None:
            raise TypeError
        self.location = location
        self.condition = condition


class IgnoreInheritedFilesType(Enum):
    NONE = 0
    ALL = 1
    READONLY = 2

class InitCommand:
    def __init__(self, command: str, folder: str):
        if command is None:
            raise TypeError
        self.command = command
        self.folder = folder

class TemplateConfig:
    def __init__(
            self,
            parameters: list[TemplateConfigParameter],
            ignore_paths: list[str],
            replacement_paths: list[str],
            user_paths: list[str],
            readonly_paths: list[str],
            optional_paths: list[str],
            rename_rules: dict[str, str],
            config_files: dict[str, str],
            override_tag_start: Optional[str],
            override_tag_end: Optional[str],
            override_statement_start: Optional[str],
            override_statement_end: Optional[str],
            min_tool_version: Optional[str],
            remove_files: Optional[list[str]],
            require_sibling_templates: Optional[list[RequireSiblingTemplate]],
            ignore_inherited_files: Optional[IgnoreInheritedFilesType],
            init_commands: Optional[list[InitCommand]],
            default_dest_folder: Optional[str],
            multiplex: Optional[list[MultiplexFile]],
            conditional: Optional[list[ConditionalFile]]
    ):
        if parameters is None:
            raise TypeError

        self.parameters = parameters or []
        self.ignore_paths = ignore_paths or []
        self.replacement_paths = replacement_paths or []
        self.user_paths = user_paths or []
        self.readonly_paths = readonly_paths or []
        self.optional_paths = optional_paths or []
        self.rename_rules = rename_rules or {}
        self.config_files = config_files or {}
        self.override_tag_start = override_tag_start
        self.override_tag_end = override_tag_end
        self.override_statement_start = override_statement_start
        self.override_statement_end = override_statement_end
        self.min_tool_version = min_tool_version
        self.remove_files = remove_files
        self.require_sibling_templates = require_sibling_templates
        self.ignore_inherited_files = ignore_inherited_files
        self.init_commands = init_commands
        self.multiplex = multiplex
        self.conditional = conditional

        self.default_dest_folder = None
        if default_dest_folder and default_dest_folder.strip():
            self.default_dest_folder = norm_relative_path(default_dest_folder)
        if not self.default_dest_folder:
            self.default_dest_folder = "."

        if len(self.user_paths) > 0 and len(self.readonly_paths) > 0:
            raise ValueError("Cannot specify both user paths and readonly paths at the same time")

    def useDeprecatedUserPaths(self):
        return (self.user_paths is not None) and len(self.user_paths) > 0

    def get_ignore_inherited_files(self):
        if self.ignore_inherited_files is None:
            return IgnoreInheritedFilesType.NONE
        return self.ignore_inherited_files

def from_file(file_name: str) -> Optional[TemplateConfig]:
    data = serialization.from_file(file_name)
    if data is None:
        return TemplateConfig(
            [],
            [],
            [],
            [],
            [],
            [],
            {},
            {},
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            [],
            []
        )
    return deserialize_project_config(data)


def to_file(data: TemplateConfig, file_name: str):
    serialization.to_file(data, file_name)


def deserialize_project_config(data):
    return TemplateConfig(
        deserialize_parameters(data.get("parameters")),
        deserialize_string_list(data.get("ignore_paths"), "ignore_paths"),
        # Support old name as well "template_paths"
        deserialize_string_list(
            data.get("replacement_paths") or data.get("template_paths"),
            "replacement_paths"
        ),
        deserialize_string_list(data.get("user_paths"), "user_paths"),
        deserialize_string_list(data.get("readonly_paths"), "readonly_paths"),
        deserialize_string_list(data.get("optional_paths"), "optional_paths"),
        deserialize_string_dictionary(data.get("rename_rules"), "rename_rules"),
        deserialize_string_dictionary(data.get("config_files"), "config_files"),
        data.get("override_tag_start"),
        data.get("override_tag_end"),
        data.get("override_statement_start"),
        data.get("override_statement_end"),
        data.get("min_tool_version"),
        deserialize_string_list(data.get("remove_files"), "remove_files"),
        deserialize_require_sibling_template(data.get("require_sibling_templates")),
        deserialize_enum(data.get("ignore_inherited_files"), IgnoreInheritedFilesType),
        deserialize_init_commands(data.get("init_commands")),
        data.get("default_dest_folder"),
        deserialize_multiplex_list(data.get("multiplex")),
        deserialize_conditional_list(data.get("conditional"))
    )

def deserialize_enum(data, enum_type):
    if data is None:
        return None

    return enum_type[data]

def deserialize_parameters(data):
    parameters = []

    if data is not None:
        for parameter in data:
            parameters.append(deserialize_parameter(parameter))

    return parameters


def deserialize_parameter(data):
    default = data.get("default")
    # backwards compatibility
    if default is None:
        required = data.get("required")
        if required is not None and not required:
            default = ""

    return TemplateConfigParameter(
        data["name"],
        data.get("description") or data.get("prompt"), # also take prompt for backwards compatibility
        default,
        data.get("hidden"),
        deserialize_string_list(data.get("choices"), "choices") if data.get("choices") else None,
        data.get("conditionally_hidden")
    )


def deserialize_require_sibling_template(data):
    sibling_templates = []

    if data is not None:
        for template in data:
            sibling_templates.append(
                RequireSiblingTemplate(
                    template.get("template_url"),
                    template.get("dest_folder"),
                    deserialize_string_dictionary(template.get("parameters"), "sibling_template_parameters"),
                    template.get("condition")
                )
            )
    return sibling_templates

def deserialize_conditional_list(data):
    conditional = []

    if data is not None:
        for template in data:
            conditional.append(
                ConditionalFile(
                    template.get("location") or template.get("file"),
                    template.get("condition")
                )
            )
    return conditional

def deserialize_multiplex_list(data):
    multiplex = []

    if data is not None:
        for template in data:
            multiplex.append(
                MultiplexFile(
                    template.get("source"),
                    template.get("destination"),
                    template.get("items")
                )
            )
    return multiplex

def deserialize_init_commands(data) -> list[InitCommand]:
    init_commands = []

    if data is not None:
        for command_obj in data:
            folder = None
            if isinstance(command_obj, str):
                command = command_obj
            else:
                command = command_obj.get("command")
                folder = command_obj.get("folder")

            init_commands.append(InitCommand(command, folder))

    return init_commands if len(init_commands) > 0 else None

template_config_file_name = "openplate.template.yaml"
