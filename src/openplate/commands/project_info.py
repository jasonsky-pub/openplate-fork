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
import os

from openplate.cfg import project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings, OpenPlateRuntimeSettings
from openplate.project_template_identity import prompt_dest_folder, prompt_template_reference
from openplate.prompts.prompt_document_collector import collect_prompt_document_all


class InfoOptions:
    def __init__(self, destination: str, offline: bool):
        if destination is None:
            raise TypeError

        self.destination = destination
        self.offline = bool(offline)


def _format_scalar(value):
    if value is None:
        return "<none>"

    if value == "":
        return '""'

    return str(value)


def _append_template_header(lines: list[str], config_project_template: project_config.ProjectTemplateConfig):
    lines.append(f"Template: {config_project_template.src_url}")
    lines.append(f"Destination: {config_project_template.dest_folder or '.'}")
    lines.append(f"Provenance: {config_project_template.provenance or 'unknown'}")
    if config_project_template.version is not None:
        lines.append(f"Version: {config_project_template.version}")


def _render_offline_info(config_project: project_config.ProjectConfig) -> str:
    lines = []

    if not config_project.templates:
        return "No tracked templates."

    for idx, config_project_template in enumerate(config_project.templates):
        if idx > 0:
            lines.append("")

        _append_template_header(lines, config_project_template)
        if not config_project_template.parameters:
            lines.append("Saved Parameters: <none>")
            continue

        lines.append("Saved Parameters:")
        for parameter_name, parameter_value in config_project_template.parameters.items():
            lines.append(f"  {parameter_name}: {_format_scalar(parameter_value)}")

    return "\n".join(lines)


def _render_resolved_info(config_project: project_config.ProjectConfig, prompt_document) -> str:
    prompt_nodes = {}
    for node in prompt_document.nodes:
        if node.info is None:
            continue
        prompt_nodes[(node.info.template, node.info.dest_folder)] = node

    lines = []
    if not config_project.templates:
        return "No tracked templates."

    for idx, config_project_template in enumerate(config_project.templates):
        if idx > 0:
            lines.append("")

        _append_template_header(lines, config_project_template)

        prompt_node = prompt_nodes.get((
            prompt_template_reference(config_project_template),
            prompt_dest_folder(config_project_template),
        ))
        if prompt_node is None or prompt_node.parameters is None:
            raise RuntimeError(
                "Unable to locate prompt metadata for tracked template: "
                f"{config_project_template.src_url}"
            )

        if not prompt_node.parameters:
            lines.append("Parameters: <none>")
            continue

        lines.append("Parameters:")
        for parameter_name, parameter_value in prompt_node.parameters.items():
            lines.append(f"  {parameter_name}: {_format_scalar(parameter_value.current)}")
            if parameter_value.description is not None:
                lines.append(f"    Description: {parameter_value.description}")
            if parameter_value.default is not None:
                lines.append(f"    Default: {_format_scalar(parameter_value.default)}")
            if parameter_value.existing is not None:
                lines.append(f"    Existing: {_format_scalar(parameter_value.existing)}")
            if parameter_value.required is not None:
                lines.append(f"    Required: {parameter_value.required}")
            if parameter_value.choices:
                lines.append(f"    Choices: {', '.join(parameter_value.choices)}")

    return "\n".join(lines)


async def run(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    options: InfoOptions,
):
    if options.offline and runtime_settings.ask_hidden:
        raise ValueError("--show-hidden cannot be used with --offline")

    config_project = project_config.from_file(
        settings,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    if options.offline:
        print(_render_offline_info(config_project))
        return

    prompt_document = await collect_prompt_document_all(
        settings,
        runtime_settings,
        options.destination,
        config_project,
        include_current=True,
    )
    print(_render_resolved_info(config_project, prompt_document))