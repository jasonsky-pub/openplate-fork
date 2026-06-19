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
from typing import Optional

from openplate import template_processor
from openplate.template_processor import compile_template_options

from openplate.cfg import project_config, template_config
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings, OpenPlateSettings
from openplate.cfg.template_config import TemplateConfigParameter
from openplate.project_template_identity import prompt_dest_folder, prompt_node_id, prompt_template_reference
from openplate.prompts.prompt_document import PromptInputTracker, PromptParameterValue


def _compile_parameter_options(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
):
    # create temporary template_options to resolve things like dest_folder or project_folder_name
    temp_options = compile_template_options(
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        runtime_settings.ignore_tool_version,
    )

    return temp_options


def _resolve_processed_default(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    parameter: TemplateConfigParameter,
) -> Optional[str]:
    temp_options = _compile_parameter_options(
        settings,
        runtime_settings,
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
    )

    default_value = None

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
            config_template.override_statement_end,
        )

    if default_value is None and parameter.default is not None:
        # for template default values, we want to resolve existing variables (such as dest_folder or project_folder_name)
        default_value = template_processor.process(
            temp_options,
            str(parameter.default),
            [],
            "Parameter Default: " + str(parameter.default),
            config_template.override_tag_start,
            config_template.override_tag_end,
            config_template.override_statement_start,
            config_template.override_statement_end,
        )

    return default_value


def resolve_parameter_defaults(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    parameter: TemplateConfigParameter,
) -> tuple[Optional[str], Optional[str]]:
    existing_value = config_project_template.parameters.get(parameter.name)
    default_value = _resolve_processed_default(
        settings,
        runtime_settings,
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        parameter,
    )

    return existing_value, default_value


def resolve_runtime_parameter_fallback(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    parameter: TemplateConfigParameter,
) -> Optional[str]:
    existing_value = config_project_template.parameters.get(parameter.name)

    # default is existing value or parameter default (do not process this one, use as-is)
    if existing_value is not None:
        return existing_value

    return _resolve_processed_default(
        settings,
        runtime_settings,
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        parameter,
    )


def describe_prompt_parameters(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
) -> dict[str, PromptParameterValue]:
    result = {}

    for parameter in config_template.parameters:
        if parameter.hidden and not runtime_settings.ask_hidden:
            continue

        existing_value, default_value = resolve_parameter_defaults(
            settings,
            runtime_settings,
            config_template,
            config_project,
            config_project_template,
            project_base_folder,
            template_base_folder,
            parameter,
        )
        result[parameter.name] = PromptParameterValue(
            default_value,
            existing_value,
            parameter.description,
            parameter.choices,
            parameter.hidden,
            existing_value is None and default_value is None,
        )

    return result


def try_resolve_parameter_without_prompt(
    config_project_template: project_config.ProjectTemplateConfig,
    parameter: TemplateConfigParameter,
    existing_value: Optional[str],
    default_value: Optional[str],
    fail_on_prompt: bool,
    prompt_input_tracker: Optional[PromptInputTracker],
):
    fallback_value = existing_value if existing_value is not None else default_value

    if prompt_input_tracker is not None:
        supplied_value, has_supplied_value = prompt_input_tracker.get_parameter_value(
            prompt_node_id(config_project_template),
            parameter.name,
        )
        if has_supplied_value and supplied_value is not None:
            if parameter.choices and supplied_value not in parameter.choices:
                raise ValueError(f"Template parameter '{parameter.name}' must be one of: {', '.join(parameter.choices)}")
            return False, supplied_value

    if fail_on_prompt and fallback_value is not None:
        return False, fallback_value

    return None


def mark_template_used(
    prompt_input_tracker: Optional[PromptInputTracker],
    config_project_template: project_config.ProjectTemplateConfig,
):
    if prompt_input_tracker is None:
        return

    prompt_input_tracker.mark_template_used(
        prompt_node_id(config_project_template),
    )


def log_unused_prompt_parameters(
    prompt_input_tracker: Optional[PromptInputTracker],
    config_project_template: project_config.ProjectTemplateConfig,
):
    if prompt_input_tracker is None:
        return

    template_reference = prompt_template_reference(config_project_template)
    dest_folder = prompt_dest_folder(config_project_template)
    node_id = prompt_node_id(config_project_template)
    for unused_name in prompt_input_tracker.unused_parameters(node_id):
        logging.warning(
            "Ignoring unused supplied prompt parameter for node-id=%r template=%r dest_folder=%r parameter=%r",
            node_id,
            template_reference,
            dest_folder,
            unused_name,
        )