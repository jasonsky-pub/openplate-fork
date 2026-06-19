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

from openplate.cfg import open_plate_settings
from openplate.cfg.open_plate_settings import OpenPlateSettings


class ConfigSetOptions:
    def __init__(self, config_file, defaults, allow_template_commands):
        self.config_file = config_file
        self.defaults = defaults or {}
        self.allow_template_commands = allow_template_commands


async def run(settings: OpenPlateSettings, options: ConfigSetOptions):
    if options is None:
        raise TypeError

    merged_defaults = settings.default_values
    for key, value in options.defaults.items():
        if value:
            merged_defaults[key] = value
        else:
            del merged_defaults[key]

    newConfiguration = OpenPlateSettings(
        settings.vcs_url or open_plate_settings.defaultSettings.vcs_url,
        settings.template_prefix or open_plate_settings.defaultSettings.template_prefix,
        merged_defaults,
        settings.allow_template_commands if options.allow_template_commands is None else options.allow_template_commands
    )

    logging.debug(f"Setting Configuration to: {newConfiguration.__str__()}")

    open_plate_settings.to_file(
        newConfiguration,
        options.config_file or open_plate_settings.defaultSettingsLocation
    )
