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
from openplate import template_processor

from openplate.cfg import project_config, template_config
from openplate.cfg.project_config import ProjectTemplateConfig


def render_sibling_template_config(
    config_template: template_config.TemplateConfig,
    template_options,
    sibling_template: template_config.RequireSiblingTemplate,
    source,
) -> ProjectTemplateConfig:
    raw_template_reference = sibling_template.template_url
    raw_dest_folder = sibling_template.dest_folder
    raw_condition = sibling_template.condition

    processed_template_reference = template_processor.process(
        template_options,
        str(raw_template_reference),
        [],
        "Sibling Template URL",
        config_template.override_tag_start,
        config_template.override_tag_end,
        config_template.override_statement_start,
        config_template.override_statement_end,
    )

    parameters = {}
    if sibling_template.parameters is not None:
        for key, value in sibling_template.parameters.items():
            parameters[key] = template_processor.process(
                template_options,
                str(value),
                [],
                "Sibling Template Parameter[" + key + "]",
                config_template.override_tag_start,
                config_template.override_tag_end,
                config_template.override_statement_start,
                config_template.override_statement_end,
            )

    # If specified, take the one in the template:
    if raw_dest_folder:
        new_dest_folder = raw_dest_folder
    else:
        # Else, throw an exception:
        raise ValueError(f"Template {source.__str__()} requires sibling but does not specify it's dest_folder")

    processed_dest_folder = template_processor.process(
        template_options,
        str(new_dest_folder),
        [],
        "Destination folder: " + str(new_dest_folder),
        config_template.override_tag_start,
        config_template.override_tag_end,
        config_template.override_statement_start,
        config_template.override_statement_end,
    )

    return ProjectTemplateConfig(
        processed_template_reference,
        None,
        None,
        processed_dest_folder,
        None,
        parameters,
        None,
        None,
        raw_template_reference,
        raw_dest_folder,
        raw_condition,
        provenance=project_config.TEMPLATE_PROVENANCE_INHERITED,
    )


def find_matching_template(
    config_project: project_config.ProjectConfig,
    config_project_template: ProjectTemplateConfig,
):
    for current_template in config_project.templates:
        if current_template.dest_folder != config_project_template.dest_folder:
            continue
        if current_template.src_url != config_project_template.src_url:
            continue

        return current_template

    return None


def copy_template_with_raw_identity(
    config_project_template: ProjectTemplateConfig,
    raw_template_reference: str,
    raw_dest_folder,
    raw_condition,
):
    return ProjectTemplateConfig(
        config_project_template.src_url,
        config_project_template.src_name,
        config_project_template.src_folder,
        config_project_template.dest_folder,
        config_project_template.version,
        dict(config_project_template.parameters),
        list(config_project_template.template_ignore_paths) if config_project_template.template_ignore_paths is not None else None,
        config_project_template.no_cache,
        raw_template_reference,
        raw_dest_folder,
        raw_condition,
        provenance=config_project_template.provenance,
    )