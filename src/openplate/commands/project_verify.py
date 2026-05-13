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
import sys

from openplate.cfg import project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings, OpenPlateRuntimeSettings
from openplate.walk.source_template_recursive_walk import VerifyWalkOptions, source_template_recursive_walk_all


class VerifyOptions:
    def __init__(self, project_folder: str):
        if project_folder is None:
            raise TypeError
        self.destination = project_folder


async def run(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    options
):
    if options is None:
        raise TypeError

    if not runtime_settings.is_automation:
        print(f"Running verify on folder: {options.destination}")

    config_project = project_config.from_file(
        settings,
        os.path.join(options.destination, project_config.project_config_file_name)
    )

    (result, found_changes, sha) = await source_template_recursive_walk_all(
        settings,
        runtime_settings,
        options.destination,
        VerifyWalkOptions(
            False,
            True
        ),
        config_project,
        settings.allow_template_commands,
        False,
        True,
        False,
        False,
        False,
        not runtime_settings.is_automation,
        True
    )

    if runtime_settings.is_automation:
        print(f"{sha}")
    else:
        print("Done!")

    if found_changes:
        sys.exit(-1)
