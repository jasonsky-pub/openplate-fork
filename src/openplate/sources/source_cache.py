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
import sys

from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.project_template_identity import source_cache_key


class CommandTemplateSourceCache:
    def __init__(self, settings: OpenPlateSettings):
        self._settings = settings
        self._sources = {}

    def get_source(self, config_project_template):
        key = source_cache_key(self._settings, config_project_template)

        source = self._sources.get(key)
        if source is not None:
            return source

        source = config_project_template.to_source(self._settings)
        source.__enter__()
        self._sources[key] = source
        return source

    def close(self):
        first_error = None

        for source in reversed(list(self._sources.values())):
            try:
                source.__exit__(None, None, None)
            except Exception as ex:
                if first_error is None:
                    first_error = ex

        self._sources.clear()

        if first_error is not None:
            raise first_error


def close_command_template_source_cache(source_cache: CommandTemplateSourceCache):
    if source_cache is None:
        return

    if sys.exc_info()[1] is None:
        source_cache.close()
        return

    try:
        source_cache.close()
    except Exception as ex:
        logging.warning("Error closing template source cache after command failure: %s", ex)
