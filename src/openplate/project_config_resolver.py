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
import re

from openplate import template_processor

from openplate.template_processor import compile_template_options

from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings, OpenPlateSettings
from openplate.cfg.template_config import TemplateConfigParameter
from openplate.git import get_git_url, get_git_email


def resolve_parameter(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    parameter: TemplateConfigParameter,
    already_asked: bool,
    fail_on_prompt: bool
) -> (bool, str):
    key_exists = parameter.name in config_project_template.parameters
    value = config_project_template.parameters.get(parameter.name)

    # create temporary template_options to resolve things like dest_folder or project_folder_name
    temp_options = compile_template_options(
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        runtime_settings.ignore_tool_version
    )

    # default is existing value or parameter default (do not process this one, use as-is)
    default_value = value

    if default_value is None:
        global_setting = settings.default_values.get(parameter.name)
        if global_setting is not None:
            logging.debug(f"preparing global default value[{global_setting}] for [{parameter.name}]")
            default_value = template_processor.process(
                temp_options,
                str(global_setting),
                [],
                "Global Default: " + global_setting,
                config_template.override_tag_start,
                config_template.override_tag_end,
                config_template.override_statement_start,
                config_template.override_statement_end
            )

    if default_value is None:
        if parameter.default is not None:
            # for template default values, we want to resolve existing variables (such as dest_folder or project_folder_name)
            default_value = template_processor.process(
                temp_options,
                str(parameter.default),
                [],
                "Parameter Default: " + str(parameter.default),
                config_template.override_tag_start,
                config_template.override_tag_end,
                config_template.override_statement_start,
                config_template.override_statement_end
            )



    # Auto answer case, hidden:
    if parameter.hidden and not runtime_settings.ask_hidden:
        logging.debug(f"not prompting for hidden parameter[{parameter.name}]")
        return False, default_value

    # Auto answer case, already answered and not re-asking:
    if not runtime_settings.ask_again and key_exists:
        logging.debug(f"not re-prompting for already answered parameter[{parameter.name}]")
        return False, default_value

    # Ask:
    while True:
        # At this point we are asking a question
        if fail_on_prompt:
            raise Exception(f"Template has unresolved parameter[{parameter.name}]: [{parameter.description}]")

        if not already_asked:
            print(f"For Template: {config_project_template.get_template_source_name()}, ")
            print(f"In folder: {config_project_template.dest_folder}, ")
            print("Please enter the following parameters:")
            already_asked = True

        allowed_values_string = ""
        if parameter.choices:
            allowed_values_string = " (Must be one of: " + ", ".join(parameter.choices) + ")"
        description = (parameter.description or parameter.name) \
                 + allowed_values_string \
                 + (f"(Default: \"{default_value}\")" if default_value is not None else "") + ": "
        value = input(description)

        # if answered, return that:
        if value and value.strip():
            if parameter.choices and value.strip() not in parameter.choices:
                print(f"ERROR: Value must be one of: {', '.join(parameter.choices)}")
                continue
            return True, value.strip()

        # auto-answer case: if no answer and a default exists, take it:
        if default_value is not None:
            logging.debug(f"Taking default value [{default_value}] for unanswered parameter[{parameter.name}]")
            return True, default_value

        print("ERROR: This question is mandatory, please answer")


def resolve(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    fail_on_prompt: bool
) -> bool:
    any_changed = False
    any_asked = False

    project_folder_name = os.path.basename(os.path.abspath(os.path.normpath(project_base_folder)))
    if not config_project.project_folder_name or config_project.project_folder_name != project_folder_name:
        config_project.project_folder_name = project_folder_name
        any_changed = True

    try:
        project_src_url = get_git_url(project_base_folder)
        project_repo_name = None
        project_repo_org = None
        if project_src_url is not None:
            project_src_url = project_src_url.strip()
            # Extract org name using regex
            match = re.search(r'[:/](?P<org>[^/]+)/(?P<repo>[^/]+?)(\.git)?$', project_src_url)
            project_repo_org = match.group('org') if match else None
            project_repo_name = match.group('repo') if match else None

        if not config_project.project_src_url or config_project.project_src_url != project_src_url:
            config_project.project_src_url = project_src_url
            any_changed = True

        if not config_project.project_repo_org or config_project.project_repo_org != project_repo_org:
            config_project.project_repo_org = project_repo_org
            any_changed = True

        if not config_project.project_repo_name or config_project.project_repo_name != project_repo_name:
            config_project.project_repo_name = project_repo_name
            any_changed = True

    except Exception:
        pass

    # Do not update the user email when doing automated processing:
    if not runtime_settings.is_automation:
        try:
            last_updater_email = get_git_email(project_base_folder)
            if not config_project.last_updater_email or config_project.last_updater_email != last_updater_email:
                config_project.last_updater_email = last_updater_email
                any_changed = True
        except Exception:
            pass

    for parameter in config_template.parameters:
        original_value = config_project_template.parameters.get(parameter.name)

        asked, new_value = resolve_parameter(
            settings,
            runtime_settings,
            config_template,
            config_project,
            config_project_template,
            project_base_folder,
            template_base_folder,
            parameter,
            any_asked,
            fail_on_prompt
        )

        if asked:
            any_asked = True

        if new_value != original_value:
            any_changed = True
            config_project_template.parameters[parameter.name] = new_value


    return any_changed
