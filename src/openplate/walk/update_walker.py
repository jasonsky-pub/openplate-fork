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
import shutil
import stat
from typing import Optional

import openplate.template_processor as template_processor
from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.cfg.project_config import ProjectTemplateFileInfo
from openplate.sources.source import TemplateSource
from openplate.walk.common_walker import CommonRecursiveWalkListener
from openplate.walk.recursive_walker import begin_recursive_walk, WalkTemplateOptions


class UpdateRecursiveWalkListener(CommonRecursiveWalkListener):
    def __init__(
        self,
        settings: OpenPlateSettings,
        config_template: template_config.TemplateConfig,
        config_project: project_config.ProjectConfig,
        config_project_template: project_config.ProjectTemplateConfig,
        config_template_project: Optional[project_config.ProjectConfig],
        template_options: dict[str, str],
        create_non_template_files: bool,
        update_non_template_files: bool,
        project_root: str
    ):
        super().__init__(
            settings,
            config_template,
            config_project,
            config_project_template,
            config_template_project,
            template_options,
            project_root
        )
        self._create_non_template_files = create_non_template_files
        self._update_non_template_files = update_non_template_files

    async def on_complete(
        self,
        template_path: str,
        project_path: str
    ):
        if self._config_template.remove_files is not None:
            logging.debug(f'Processing Remove Files')
            for remove_file in self._config_template.remove_files:
                remove_file = template_processor.process(
                    self._template_options,
                    remove_file,
                    [],
                    "Remove file: " + remove_file,
                    self._config_template.override_tag_start,
                    self._config_template.override_tag_end,
                    self._config_template.override_statement_start,
                    self._config_template.override_statement_end
                )
                project_remove_file_path = os.path.join(project_path, remove_file)
                exists = os.path.exists(project_remove_file_path)
                if exists:
                    logging.debug(f'Removing remove file: {project_remove_file_path}')
                    is_currently_readonly = not os.access(project_remove_file_path, os.W_OK)

                    # Remove readonly so we can remove the file:
                    if is_currently_readonly:
                        os.chmod(project_remove_file_path, stat.S_IWRITE)

                    os.remove(project_remove_file_path)
                else:
                    logging.debug(f'Skipping non-existent remove-file: {project_remove_file_path}')

    def update_template_file_cache(self, relative_path: str, is_readonly: bool):
        if self._config_project.template_file_cache is None:
            self._config_project.template_file_cache = {}
        template_cache = self._config_project.template_file_cache

        entry = template_cache.get(relative_path)
        if entry is None:
            entry = ProjectTemplateFileInfo(relative_path, is_readonly)
            template_cache[relative_path] = entry
        else:
            entry.is_readonly = entry.is_readonly



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

        if not should_be_readonly:
            # Will only update non-existing "non-template" files if the option has been specified
            if not exists and not self._create_non_template_files and not self._update_non_template_files:
                # Option not specified
                logging.debug(f'Skipping non-existing non-readonly path: {project_relative_path}')
                return
            # Will only overwrite existing non-readonly files if option specified
            if exists and not self._update_non_template_files:
                # Option not specified
                logging.debug(f'Skipping existing non-readonly path: {project_relative_path}')
                return

        logging.debug(
            f"generating file: {project_relative_path} is_replacement={is_replacement} should_be_readonly={should_be_readonly}"
        )

        is_currently_readonly = not os.access(project_path, os.W_OK)

        # Remove readonly so we can write the file:
        if exists and is_currently_readonly:
            os.chmod(project_path, stat.S_IWRITE)

        if not is_replacement:
            shutil.copyfile(template_path, project_path)
        else:
            with open(template_path) as stream:
                file_data = stream.read()

            template_dir = os.path.dirname(template_path)
            project_dir = os.path.dirname(project_path)

            new_data = template_processor.process(
                self._template_options,
                file_data,
                [template_dir, project_dir],
                template_relative_path,
                self._config_template.override_tag_start,
                self._config_template.override_tag_end,
                self._config_template.override_statement_start,
                self._config_template.override_statement_end
            )

            with open(project_path, "w") as stream:
                stream.write(new_data)

        if should_be_readonly:
            os.chmod(project_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

        if self._config_project_template.no_cache:
            logging.debug(f"Skipping caching of no-cache file: {project_relative_path}")
        else:
            self.update_template_file_cache(project_relative_path, should_be_readonly)


async def walk_update(
        settings: OpenPlateSettings,
        source: TemplateSource,
        destination: str,
        config_project: project_config.ProjectConfig,
        config_project_template: project_config.ProjectTemplateConfig,
        config_template_project: project_config.ProjectConfig,
        config_template: template_config.TemplateConfig,
        template_options: dict[str, str],
        create_non_template_files: bool,
        update_non_template_files: bool
):
    logging.debug(f"Performing Updates")

    await begin_recursive_walk(
        source.folder_path(),
        destination,
        WalkTemplateOptions(True),
        UpdateRecursiveWalkListener(
            settings,
            config_template,
            config_project,
            config_project_template,
            config_template_project,
            template_options,
            create_non_template_files,
            update_non_template_files,
            destination
        )
    )
