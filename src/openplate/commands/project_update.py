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
from typing import Optional

from openplate.cfg import project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings, OpenPlateRuntimeSettings
from openplate.prompts.prompt_input_logging import log_ignored_prompt_templates
from openplate.prompts.prompt_document_collector import collect_prompt_document_all
from openplate.prompts.prompt_document import PromptDocument, PromptInputTracker
from openplate.walk.source_template_recursive_walk import VerifyWalkOptions, source_template_recursive_walk_all


class UpdateOptions:
    def __init__(
        self,
        destination: str,
        create_non_template_files: bool,
        update_non_template_files: bool,
        print_prompts_json: bool = False,
        prompt_document: Optional[PromptDocument] = None,
    ):
        if destination is None:
            raise TypeError
        self.destination = destination
        self.create_non_template_files = create_non_template_files
        self.update_non_template_files = update_non_template_files
        self.print_prompts_json = print_prompts_json or False
        self.prompt_document = prompt_document


async def run(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    options
):
    print(f"Running update on folder: {options.destination}")
    logging.debug(f"create_non_template_files: {options.create_non_template_files}, update_non_template_files: {options.update_non_template_files}")

    config_project = project_config.from_file(
        settings,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    (config_updated, found_changes, sha) = await source_template_recursive_walk_all(
        settings,
        runtime_settings,
        options.destination,
        VerifyWalkOptions(
            False,
            False
        ),
        config_project,
        settings.allow_template_commands,
        False,
        False,
        True,
        options.create_non_template_files,
        options.update_non_template_files,
        False,
        False,
        None,
    )

    # if config_updated:

    # Always attempt to fix config file (to update name references which should be urls for example)
    project_config.to_file(
        config_project,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    print("Done!")



