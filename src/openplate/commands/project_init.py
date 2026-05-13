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
from openplate.walk.source_template_recursive_walk import VerifyWalkOptions, source_template_recursive_walk_single


class InitOptions:
    def __init__(
        self,
        add_template: project_config.ProjectTemplateConfig,
        destination: str,
        overwrite_existing_files: bool,
        allow_template_commands: bool
    ):
        if add_template is None:
            raise TypeError
        if destination is None:
            raise TypeError
        self.add_template = add_template
        self.destination = destination
        self.overwrite_existing_files = overwrite_existing_files or False
        self.allow_template_commands = allow_template_commands or False


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

    config_project.templates.append(options.add_template)

    allow_template_commands = settings.allow_template_commands or options.allow_template_commands

    await source_template_recursive_walk_single(
        settings,
        runtime_settings,
        options.add_template,
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
        False
    )

    # Always update config from an init:
    project_config.to_file(
        config_project,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    print("Done!")
