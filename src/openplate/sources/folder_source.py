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

from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.sources.source import TemplateSource


class FolderTemplateSource(TemplateSource):
    def __init__(self, configuration: OpenPlateSettings, folder: str):
        if folder is None:
            raise TypeError
        self.configuration = configuration
        self._folder = folder

    def __str__(self):
        return f"Folder Template: {self._folder}"

    def folder_path(self):
        return self._folder

    def template_url(self):
        return None

    def template_folder(self):
        return self._folder

    def repo_sha(self):
        return "NONE"

    def __enter__(self):
        logging.debug(f"Utilizing Template from folder: {self._folder}")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass
