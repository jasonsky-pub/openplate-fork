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
from typing import Optional

from openplate.cfg import project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings, OpenPlateRuntimeSettings
from openplate.prompts.prompt_input_logging import log_ignored_prompt_templates
from openplate.prompts.prompt_document_collector import collect_prompt_document_single
from openplate.prompts.prompt_document import PromptDocument, PromptInputTracker
from openplate.walk.source_template_recursive_walk import VerifyWalkOptions, source_template_recursive_walk_single


class InitOptions:
    def __init__(
        self,
        add_template: project_config.ProjectTemplateConfig,
        destination: str,
        overwrite_existing_files: bool,
        allow_template_commands: bool,
        print_prompts_json: bool = False,
        prompt_document: Optional[PromptDocument] = None,
    ):
        if add_template is None:
            raise TypeError
        if destination is None:
            raise TypeError
        self.add_template = add_template
        self.destination = destination
        self.overwrite_existing_files = overwrite_existing_files or False
        self.allow_template_commands = allow_template_commands or False
        self.print_prompts_json = print_prompts_json or False
        self.prompt_document = prompt_document


async def print_prompt_document(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    add_template: project_config.ProjectTemplateConfig,
    destination: str,
    verbose: bool,
):
    config_project = project_config.from_file(
        settings,
        os.path.join(destination, project_config.project_config_file_name)
    )

    config_project.templates.append(add_template)
    prompt_document = await collect_prompt_document_single(
        settings,
        runtime_settings,
        add_template,
        destination,
        config_project,
    )
    print(prompt_document.to_json_string(verbose=verbose))


async def run(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    options: InitOptions,
):
    print(f"Running init on folder: {options.destination} source: {options.add_template.__str__()}")

    config_project = project_config.from_file(
        settings,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    tracked_template = next(
        (
            template for template in config_project.templates
            if template.dest_folder == options.add_template.dest_folder
            and template.src_url == options.add_template.src_url
            and template.src_name == options.add_template.src_name
            and template.src_folder == options.add_template.src_folder
        ),
        None,
    )
    if tracked_template is None:
        tracked_template = options.add_template
        tracked_template.provenance = project_config.TEMPLATE_PROVENANCE_REQUESTED
        config_project.templates.append(tracked_template)
    else:
        if not options.overwrite_existing_files:
            tracked_dest_folder = tracked_template.dest_folder or "."
            raise SystemExit(
                "Template already exists at destination folder "
                f"'{tracked_dest_folder}'. Use 'openplate update' for maintenance or "
                "rerun with 'openplate init --overwrite'."
            )
        tracked_template.version = options.add_template.version
        tracked_template.template_ignore_paths = options.add_template.template_ignore_paths
        tracked_template.no_cache = options.add_template.no_cache
        tracked_template.provenance = project_config.TEMPLATE_PROVENANCE_REQUESTED

    allow_template_commands = settings.allow_template_commands or options.allow_template_commands

    prompt_input_tracker = None
    if options.prompt_document is not None:
        prompt_input_tracker = PromptInputTracker(options.prompt_document)

    await source_template_recursive_walk_single(
        settings,
        runtime_settings,
        tracked_template,
        options.destination,
        VerifyWalkOptions(
            True,
            False
        ),
        config_project,
        allow_template_commands,
        not options.overwrite_existing_files,
        False,
        True,
        True,
        options.overwrite_existing_files,
        True,
        options.prompt_document is not None,
        prompt_input_tracker,
    )

    log_ignored_prompt_templates(prompt_input_tracker)

    # Always update config from an init:
    project_config.to_file(
        config_project,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    print("Done!")
