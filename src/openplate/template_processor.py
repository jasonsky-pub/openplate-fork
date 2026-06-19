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
import logging
import os
import semver
from typing import Optional

from liquid import Environment

from openplate import __semver__ as module_semver
from openplate.cfg.project_config import ProjectConfig, ProjectTemplateConfig
from openplate.cfg.serialization import raw_from_file, from_string
from openplate.cfg.template_config import TemplateConfig
from openplate.template_loader import OpenPlateTemplateLoader


def compile_template_options(
        config_template: TemplateConfig,
        config_project: ProjectConfig,
        config_project_template: ProjectTemplateConfig,
        source_folder: str,
        destination_folder: str,
        ignore_tool_version: bool
) -> dict[str, object]:

    if not ignore_tool_version:
        if config_template.min_tool_version is not None and config_template.min_tool_version.strip():
            openplate_version_string = module_semver
            openplate_version = semver.VersionInfo.parse(openplate_version_string)
            min_version_string = config_template.min_tool_version.strip()
            min_version = semver.VersionInfo.parse(min_version_string)
            if openplate_version < min_version:
                raise ValueError("This Template Requires Openplate Version >= {}, however the current version is {}".format(min_version_string, openplate_version_string))


    options = {}
    for key in config_project_template.parameters.keys():
        options[key] = config_project_template.parameters[key]

    options["dest_folder"] = config_project_template.dest_folder
    options["project_git_mode"] = bool(getattr(config_project, "project_git_mode", False))
    options["project_folder_name"] = config_project.project_folder_name or ""
    options["project_src_url"] = config_project.project_src_url or ""
    options["project_git_repo_url"] = getattr(config_project, "project_git_repo_url", "") or ""
    options["project_git_ssh_repo_url"] = getattr(config_project, "project_git_ssh_repo_url", "") or ""
    options["project_git_https_repo_url"] = getattr(config_project, "project_git_https_repo_url", "") or ""
    options["project_git_repo_org"] = getattr(config_project, "project_git_repo_org", "") or ""
    options["project_git_repo_name"] = getattr(config_project, "project_git_repo_name", "") or ""
    options["project_repo_name"] = getattr(config_project, "project_repo_name", "") or ""
    options["project_repo_org"] = getattr(config_project, "project_repo_org", "") or ""
    options["project_guid1"] = config_project.project_guid1 or ""
    options["project_guid2"] = config_project.project_guid2 or ""
    options["project_guid3"] = config_project.project_guid3 or ""
    options["last_updater_email"] = config_project.last_updater_email or ""

    options["template_src_url"] = getattr(config_project_template, "template_src_url", None) or config_project_template.src_url or ""
    options["template_git_ssh_src_url"] = getattr(config_project_template, "template_git_ssh_src_url", "") or ""
    options["template_git_https_src_url"] = getattr(config_project_template, "template_git_https_src_url", "") or ""
    options["template_git_repo_url"] = getattr(config_project_template, "template_git_repo_url", "") or ""
    options["template_git_ssh_repo_url"] = getattr(config_project_template, "template_git_ssh_repo_url", "") or ""
    options["template_git_https_repo_url"] = getattr(config_project_template, "template_git_https_repo_url", "") or ""
    options["template_git_repo_org"] = getattr(config_project_template, "template_git_repo_org", "") or ""
    options["template_git_repo_name"] = getattr(config_project_template, "template_git_repo_name", "") or ""
    options["template_git_repo_path"] = getattr(config_project_template, "template_git_repo_path", "") or ""
    options["template_git_repo_ref"] = getattr(config_project_template, "template_git_repo_ref", "") or ""
    options["template_version"] = config_project_template.version or ""

    for (config_file_key, config_file_location) in config_template.config_files.items():
        # First render the config file name:
        rendered_config_file_location = process(
            options,
            config_file_location,
            [],
            config_file_location,
            config_template.override_tag_start,
            config_template.override_tag_end,
            config_template.override_statement_start,
            config_template.override_statement_end
        )

        # load the config file string:
        file_source = os.path.join(destination_folder, rendered_config_file_location)
        config_str = raw_from_file(file_source)
        if config_str is None:
            # If loading from template, use the un-rendered file name
            file_source = os.path.join(source_folder, config_file_location)
            config_str = raw_from_file(file_source)

        if config_str is not None:
            # process the config file replacements:
            config_str = process(
                options,
                config_str,
                [],
                file_source,
                config_template.override_tag_start,
                config_template.override_tag_end,
                config_template.override_statement_start,
                config_template.override_statement_end
            )

            # deserialize from yaml and add config data to options:
            config = from_string(config_str, file_source)
            options[config_file_key] = config

    return options


def process(
        template_options: dict[str, str],
        template_string: str,
        paths: list[str],
        template_source: str = "UNKNOWN",
        override_tag_start: Optional[str] = None,
        override_tag_end: Optional[str] = None,
        override_statement_start: Optional[str] = None,
        override_statement_end: Optional[str] = None
) -> str:
    try:

        env = Environment(
            loader=OpenPlateTemplateLoader(template_string, paths),
            tag_start_string=override_tag_start or "{%",
            tag_end_string=override_tag_end or "%}",
            statement_start_string=override_statement_start or "{{",
            statement_end_string=override_statement_end or "}}"
        )
        template = env.get_template("")
        # template = Template(template_string)
        return template.render(template_options)
    except Exception as e:
        logging.error(f"Error processing template from {template_source}: {e}")
        raise
