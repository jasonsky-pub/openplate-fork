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
import uuid
from typing import Optional

from openplate.cfg import serialization
from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.cfg.serialization import deserialize_string_dictionary, deserialize_string_list
from openplate.sources.url_source import UrlTemplateSource
from openplate.walk.recursive_walker import norm_relative_path


_RAW_DEST_FOLDER_UNSET = object()


def _normalize_legacy_source_field(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    stripped_value = str(value).strip()
    if not stripped_value:
        return None

    return stripped_value


def _reject_legacy_source_field(value: Optional[str], field_name: str):
    normalized_value = _normalize_legacy_source_field(value)
    if normalized_value is not None:
        raise RuntimeError(
            f"Project configuration field '{field_name}' is no longer supported. "
            "URL-backed template references are required."
        )


class ProjectTemplateFileInfo:
    def __init__(self, relative_path: str, is_readonly: bool):
        if relative_path is None:
            raise ValueError("relative_path cannot be None")

        self.relative_path = relative_path
        self.is_readonly = is_readonly

class ProjectTemplateConfig:
    def __init__(
        self,
        src_url: Optional[str],
        src_name: Optional[str],
        src_folder: Optional[str],
        dest_folder: Optional[str],
        version: Optional[str],
        parameters: dict[str, str],
        template_ignore_paths: Optional[list[str]],
        no_cache: Optional[bool],
        raw_template_reference: Optional[str] = None,
        raw_dest_folder = _RAW_DEST_FOLDER_UNSET,
        raw_condition: Optional[str] = None,
    ):
        self.src_url = src_url
        self.src_name = src_name
        self.src_folder = src_folder
        self.raw_template_reference = raw_template_reference or src_url or src_name or src_folder

        if raw_dest_folder is _RAW_DEST_FOLDER_UNSET:
            self.raw_dest_folder = dest_folder
        else:
            self.raw_dest_folder = raw_dest_folder

        self.raw_condition = raw_condition

        self.dest_folder = None
        if dest_folder and dest_folder.strip():
            self.dest_folder = norm_relative_path(dest_folder)

        # Do not update if not supplied, because not supplied will take from template.
        # Only update if "blank"
        if self.dest_folder == "":
            self.dest_folder = "."

        self.version = version
        self.parameters = parameters
        self.template_ignore_paths = template_ignore_paths
        self.no_cache = no_cache

    def __getstate__(self):
        return {
            "src_url": self.src_url,
            "dest_folder": self.dest_folder,
            "version": self.version,
            "parameters": self.parameters,
            "template_ignore_paths": self.template_ignore_paths,
            "no_cache": self.no_cache,
        }

    def __str__(self):
        return \
            f"src_url: {self.src_url} " if self.src_url else "" \
            + f"src_name: {self.src_name} " if self.src_name else "" \
            + f"src_folder: {self.src_folder} " if self.src_folder else "" \
            + f"dest_folder: {self.src_name} " if self.dest_folder else ""

    def get_template_source_name(self):
        if self.src_url:
            return "from url: " + self.src_url
        elif self.src_name:
            return "from name: " + self.src_name
        elif self.src_folder:
            return "from folder: " + self.src_folder
        raise ValueError("Unknown template source")

    def to_source(self, settings: OpenPlateSettings):
        if self.src_url:
            return UrlTemplateSource(settings, self.src_url)
        else:
            raise ValueError("Unknown or unsupported template source")

class ProjectConfig:
    def __init__(
            self,
            templates: Optional[list[ProjectTemplateConfig]],
            template_src_url: Optional[str],
            template_src_folder: Optional[str],
            template_version: Optional[str],
            project_folder_name: Optional[str],
            project_src_url: Optional[str],
            project_repo_org: Optional[str],
            project_repo_name: Optional[str],
            project_guid1: Optional[str],
            project_guid2: Optional[str],
            project_guid3: Optional[str],
            parameters: dict[str, str],
            template_file_cache: Optional[dict[str, ProjectTemplateFileInfo]],
            last_updater_email: Optional[str]
    ):
        self.templates = templates
        if (template_src_url is not None
                or template_src_folder is not None
                or template_version is not None
                or (parameters is not None and bool(parameters))):
            self.templates.append(
                ProjectTemplateConfig(
                    template_src_url,
                    None,
                    template_src_folder,
                    None,
                    template_version,
                    parameters or {},
                    [],
                    None
                )
            )
        self.project_folder_name = project_folder_name
        self.project_src_url = project_src_url
        self.project_repo_org = project_repo_org
        self.project_repo_name = project_repo_name
        self.project_guid1 = project_guid1 or uuid.uuid4().__str__()
        self.project_guid2 = project_guid2 or uuid.uuid4().__str__()
        self.project_guid3 = project_guid3 or uuid.uuid4().__str__()
        self.template_file_cache = template_file_cache
        self.last_updater_email = last_updater_email

    def __getstate__(self):
        return {
            "templates": self.templates,
            "project_guid1": self.project_guid1,
            "project_guid2": self.project_guid2,
            "project_guid3": self.project_guid3,
            "template_file_cache": self.template_file_cache,
            "last_updater_email": self.last_updater_email,
        }

    def has_template(self, config: ProjectTemplateConfig) -> bool:
        assert config is not None
        for template in self.templates:
            if template.dest_folder != config.dest_folder:
                continue
            if template.src_url != config.src_url:
                continue

            return True
        return False





def from_file(settings: OpenPlateSettings, file_name: str) -> Optional[ProjectConfig]:
    data = serialization.from_file(file_name)
    if data is None:
        return ProjectConfig(
            [],
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
            {},
            {},
            None
        )
    return deserialize_project_config(settings, data)


def to_file(data: ProjectConfig, file_name: str):
    serialization.to_file(data, file_name)


def deserialize_project_config(settings: OpenPlateSettings, data):
    _reject_legacy_source_field(data.get("template_src_folder"), "template_src_folder")

    return ProjectConfig(
        deserialize_templates(settings, data.get("templates")),
        data.get("template_src_url"),
        None,
        data.get("template_version"),
        None,
        None,
        None,
        None,
        data.get("project_guid1"),
        data.get("project_guid2"),
        data.get("project_guid3"),
        deserialize_string_dictionary(data.get("parameters"), "parameters"),
        deserialize_project_template_file_dictionary(data.get("template_file_cache"), "template_file_cache"),
        data.get("last_updater_email")
    )

def deserialize_project_template_file(data):
    return ProjectTemplateFileInfo(
        data.get("relative_path"),
        data.get("is_readonly")
    )


def deserialize_project_template_file_dictionary(data, field_name: str) -> dict[str:ProjectTemplateFileInfo]:
    result = {}

    if data is not None:
        for key in data.keys():
            if not isinstance(key, str):
                raise TypeError("key in dictionary: " + field_name + " in project configuration is not a string")
            result[key] = deserialize_project_template_file(data[key])

    return result



def deserialize_templates(settings: OpenPlateSettings, data):
    templates = []

    if data is not None:
        for template in data:
            templates.append(deserialize_template(settings, template))

    return templates


def deserialize_template(settings: OpenPlateSettings, data):
    url = data.get("src_url")

    _reject_legacy_source_field(data.get("src_name"), "src_name")
    _reject_legacy_source_field(data.get("src_folder"), "src_folder")

    return ProjectTemplateConfig(
        url,
        None,
        None,
        data.get("dest_folder"),
        data.get("version"),
        deserialize_string_dictionary(data.get("parameters"), "template_parameters"),
        deserialize_string_list(data.get("template_ignore_paths"), "template_ignore_paths"),
        data.get("no_cache"),
        data.get("src_url") or data.get("src_name") or data.get("src_folder"),
        data.get("dest_folder"),
    )

project_config_file_name = ".openplate.project.yaml"
