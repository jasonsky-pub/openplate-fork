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
import threading
from typing import Optional

import openplate.template_processor as template_processor
from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.sources.source import TemplateSource
from openplate.walk.common_walker import CommonRecursiveWalkListener
from openplate.walk.recursive_walker import begin_recursive_walk, WalkTemplateOptions


class VerifyWalkOptions:
    def __init__(
            self,
            error_on_existing: bool,
            error_on_content_different: bool
    ):
        self.error_on_existing = error_on_existing
        self.error_on_content_different = error_on_content_different


def binary_files_equal(file1: str, file2: str, chunk_size: int = 1024 * 1024) -> bool:
    with open(file1, mode="rb") as file1, open(file2, mode="rb") as file2:
        while True:
            chunk1 = file1.read(chunk_size)
            chunk2 = file2.read(chunk_size)

            # this handles both unequal bytes and one ending before the other:
            if chunk1 != chunk2:
                return False

            if not chunk1:
                break

    return True


class VerifyRecursiveWalkListener(CommonRecursiveWalkListener):
    def __init__(
        self,
        settings: OpenPlateSettings,
        options: VerifyWalkOptions,
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
        self._options = options

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
            if self._options.error_on_existing:
                self.add_issue(f"{project_relative_path} exists already")
                return

        if should_be_readonly:
            if not exists:
                self.add_issue(f"{project_relative_path} missing")
                return
            else:
                if self._options.error_on_content_different:
                    up_to_date = True
                    if not is_replacement:
                        if not binary_files_equal(template_path, project_path):
                            up_to_date = False
                    else:
                        with open(template_path) as stream:
                            file_data = stream.read()

                        template_dir = os.path.dirname(template_path)
                        project_dir = os.path.dirname(project_path)

                        processed_contents = template_processor.process(
                            self._template_options,
                            file_data,
                            [template_dir, project_dir],
                            template_relative_path,
                            self._config_template.override_tag_start,
                            self._config_template.override_tag_end,
                            self._config_template.override_statement_start,
                            self._config_template.override_statement_end
                        )

                        with open(project_path) as file:
                            existing_contents = file.read()

                        if processed_contents != existing_contents:
                            up_to_date = False

                    if not up_to_date:
                        self.add_issue(f"{project_relative_path} is not up to date (content)")

async def walk_verify(
        settings: OpenPlateSettings,
        walk_options: VerifyWalkOptions,
        source: TemplateSource,
        destination: str,
        config_project: project_config.ProjectConfig,
        config_project_template: project_config.ProjectTemplateConfig,
        config_template_project: project_config.ProjectConfig,
        config_template: template_config.TemplateConfig,
        template_options: dict[str, str]
):
    logging.debug(f"Performing Pre-check")

    checkWalkListener = VerifyRecursiveWalkListener(
        settings,
        walk_options,
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

