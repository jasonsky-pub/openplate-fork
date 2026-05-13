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
import threading
from typing import Optional

from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.sources.source import TemplateSource
from openplate.walk.common_walker import CommonRecursiveWalkListener
from openplate.walk.recursive_walker import begin_recursive_walk, WalkTemplateOptions


class InitRecursiveWalkListener(CommonRecursiveWalkListener):
    def __init__(
        self,
        settings: OpenPlateSettings,
        config: template_config.TemplateConfig,
        config_project: project_config.ProjectConfig,
        config_project_template: project_config.ProjectTemplateConfig,
        config_template_project: Optional[project_config.ProjectConfig],
        template_options: dict[str, str],
        project_root: str
    ):
        super().__init__(
            settings,
            config,
            config_project,
            config_project_template,
            config_template_project,
            template_options,
            project_root
        )
        self._lock = threading.Lock()
        self._issues = []

    def get_issues(self):
        self._lock.acquire()
        try:
            return self._issues
        finally:
            self._lock.release()

    def add_issue(self, issue: str):
        self._lock.acquire()
        try:
            self._issues.append(issue)
        finally:
            self._lock.release()

    async def handle_file(
            self,
            project_path: str,
            template_path: str,
            template_relative_path: str,
            project_relative_path: str,
            exists: bool,
            is_replacement: bool,
            should_be_readonly: bool
    ):

        logging.debug(f"Validating file: {project_relative_path} is_replacement={is_replacement}")

        if exists:
            self.add_issue(f"{project_relative_path} exists already")
            return


async def walk_init(
        settings: OpenPlateSettings,
        source: TemplateSource,
        destination: str,
        config_project: project_config.ProjectConfig,
        config_project_template: project_config.ProjectTemplateConfig,
        config_template_project: project_config.ProjectConfig,
        config_template: template_config.TemplateConfig,
        template_options: dict[str, str]
):
    logging.debug(f"Performing Pre-check")

    checkWalkListener = InitRecursiveWalkListener(
        settings,
        config_template,
        config_project,
        config_project_template,
        config_template_project,
        template_options,
        destination
    )

    await begin_recursive_walk(
        source.folder_path(),
        destination,
        WalkTemplateOptions(False),
        checkWalkListener
    )

    return checkWalkListener.get_issues()

