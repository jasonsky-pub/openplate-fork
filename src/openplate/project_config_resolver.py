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
from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings, OpenPlateSettings
from openplate.cfg.template_config import TemplateConfigParameter
from openplate.project_metadata_resolver import resolve_project_metadata
from openplate.prompts.prompt_document import PromptInputTracker
from openplate.prompts.prompt_parameter_resolver import (
    log_unused_prompt_parameters,
    mark_template_used,
    resolve_runtime_parameter_fallback,
    try_resolve_parameter_without_prompt,
)
from openplate.template_processor import compile_template_options


def resolve_parameter_hidden_state(
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    parameter: TemplateConfigParameter,
    runtime_settings: OpenPlateRuntimeSettings,
) -> bool:
    effective_hidden = bool(parameter.hidden)

    if parameter.conditionally_hidden is None:
        return effective_hidden

    template_options = compile_template_options(
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        runtime_settings.ignore_tool_version
    )
    rendered_hidden_state = template_processor.process(
        template_options,
        str(parameter.conditionally_hidden),
        [],
        "Parameter conditionally_hidden: " + str(parameter.conditionally_hidden),
        config_template.override_tag_start,
        config_template.override_tag_end,
        config_template.override_statement_start,
        config_template.override_statement_end
    )
    normalized_hidden_state = str(rendered_hidden_state).strip().lower()

    if normalized_hidden_state not in {"true", "false"}:
        raise ValueError(
            f"Parameter '{parameter.name}' conditionally_hidden must render to 'true' or 'false', got '{rendered_hidden_state}'"
        )

    return normalized_hidden_state == "false"


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
    fail_on_prompt: bool,
    prompt_input_tracker: Optional[PromptInputTracker] = None,
) -> (bool, str):
    key_exists = parameter.name in config_project_template.parameters
    existing_value = config_project_template.parameters.get(parameter.name)
    fallback_value = resolve_runtime_parameter_fallback(
        settings,
        runtime_settings,
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        parameter,
    )

    # Auto answer case, hidden:
    if parameter.hidden and not runtime_settings.ask_hidden:
        logging.debug(f"not prompting for hidden parameter[{parameter.name}]")
        return False, fallback_value

    effective_hidden = resolve_parameter_hidden_state(
        config_template,
        config_project,
        config_project_template,
        project_base_folder,
        template_base_folder,
        parameter,
        runtime_settings
    )

    # Auto answer case, hidden:
    if effective_hidden and not runtime_settings.ask_hidden:
        logging.debug(f"not prompting for hidden parameter[{parameter.name}]")
        return False, fallback_value

    resolved_answer = try_resolve_parameter_without_prompt(
        config_project_template,
        parameter,
        existing_value,
        fallback_value if existing_value is None else None,
        fail_on_prompt,
        prompt_input_tracker,
    )
    if resolved_answer is not None:
        return resolved_answer

    # Auto answer case, already answered and not re-asking:
    if not runtime_settings.ask_again and key_exists:
        logging.debug(f"not re-prompting for already answered parameter[{parameter.name}]")
        return False, fallback_value

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
                 + (f"(Default: \"{fallback_value}\")" if fallback_value is not None else "") + ": "
        value = input(description)

        # if answered, return that:
        if value and value.strip():
            if parameter.choices and value.strip() not in parameter.choices:
                print(f"ERROR: Value must be one of: {', '.join(parameter.choices)}")
                continue
            return True, value.strip()

        # auto-answer case: if no answer and a default exists, take it:
        if fallback_value is not None:
            logging.debug(f"Taking default value [{fallback_value}] for unanswered parameter[{parameter.name}]")
            return True, fallback_value

        print("ERROR: This question is mandatory, please answer")


def resolve(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_template: template_config.TemplateConfig,
    config_project: project_config.ProjectConfig,
    config_project_template: project_config.ProjectTemplateConfig,
    project_base_folder: str,
    template_base_folder: str,
    fail_on_prompt: bool,
    prompt_input_tracker: Optional[PromptInputTracker] = None,
) -> bool:
    any_changed = resolve_project_metadata(runtime_settings, config_project, project_base_folder)
    any_asked = False

    mark_template_used(prompt_input_tracker, config_project_template)

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
            fail_on_prompt,
            prompt_input_tracker,
        )

        if asked:
            any_asked = True

        if new_value != original_value:
            any_changed = True
            config_project_template.parameters[parameter.name] = new_value

    log_unused_prompt_parameters(prompt_input_tracker, config_project_template)

    return any_changed
