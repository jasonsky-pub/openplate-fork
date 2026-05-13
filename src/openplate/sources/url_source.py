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
from openplate.git import GitClonedTemporaryFolder
from openplate.sources.source import TemplateSource


class UrlTemplateSource(TemplateSource):
    def __init__(self, configuration: OpenPlateSettings, url: str):
        if url is None:
            raise TypeError
        self.configuration = configuration
        self._url = url
        self._gitFolder = GitClonedTemporaryFolder(self._url)

    def __str__(self):
        return f"Template: {self._url}"

    def folder_path(self):
        return self._gitFolder.folder_path()

    def repo_sha(self):
        return self._gitFolder.repo_sha

    def template_url(self):
        return self._url

    def template_folder(self):
        return None

    def __enter__(self):
        logging.debug(f"Getting Source from url: {self._url}")
        self._gitFolder.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._gitFolder.__exit__(exception_type, exception_value, traceback)
