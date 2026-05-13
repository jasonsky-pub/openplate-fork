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
from openplate.cfg import serialization
from openplate.cfg.serialization import deserialize_string_dictionary
from openplate.util import str_to_bool


class OpenPlateSettings:
    def __init__(
            self,
            vcs_url: str,
            template_prefix: str,
            default_values: dict[str, str],
            allow_template_commands: bool
    ):
        if vcs_url is None:
            raise TypeError
        self.vcs_url = vcs_url
        self.template_prefix = template_prefix
        self.default_values = default_values or {}
        self.allow_template_commands = allow_template_commands or False

class OpenPlateRuntimeSettings:
    def __init__(
            self,
            ask_again: bool,
            ask_hidden: bool,
            ignore_tool_version: bool,
            is_automation: bool
    ):
        self.ask_again = ask_again
        self.ask_hidden = ask_hidden
        self.ignore_tool_version = ignore_tool_version
        self.is_automation = is_automation


def from_file(file_name: str):
    return deserialize_settings(serialization.from_file(file_name))


def to_file(settings: OpenPlateSettings, file_name: str):
    serialization.to_file(settings, file_name)


def deserialize_settings(data):
    if data is None:
        data = {}

    allow_template_commands_raw = data.get("allow_template_commands")
    if allow_template_commands_raw is None:
        allow_template_commands = defaultSettings.allow_template_commands
    else:
        allow_template_commands = str_to_bool(allow_template_commands_raw)

    return OpenPlateSettings(
        data.get("vcs_url") or defaultSettings.vcs_url,
        data.get("template_prefix") or defaultSettings.template_prefix,
        deserialize_string_dictionary(data.get("default_values"), "default_values"),
        allow_template_commands
    )


defaultSettings = OpenPlateSettings("https://github.com", "ot-", {}, False)
defaultSettingsLocation = "~/.openplate"
