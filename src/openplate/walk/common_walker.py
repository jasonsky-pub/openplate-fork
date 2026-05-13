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
from pathlib import Path
from typing import Optional

from openplate import template_processor

from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.cfg.template_config import IgnoreInheritedFilesType
from openplate.cfg.template_config_matcher import TemplateConfigMatcher
from openplate.util import str_to_bool
from openplate.walk.recursive_walker import RecursiveWalkListener


class CommonRecursiveWalkListener(RecursiveWalkListener):
    def __init__(
            self,
            settings: OpenPlateSettings,
            config_template: template_config.TemplateConfig,
            config_project: project_config.ProjectConfig,
            config_project_template: project_config.ProjectTemplateConfig,
            config_template_project: Optional[project_config.ProjectConfig],
            template_options: dict[str, str],
            project_root: str
    ):
        self._settings = settings
        self._config_template = config_template
        self._config_project = config_project
        self._config_project_template = config_project_template
        self._config_template_project = config_template_project
        self._matcher = TemplateConfigMatcher(config_template, config_project_template)
        self._template_options = template_options
        self._config_templates = template_options
        self._project_root = project_root

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
        pass

    async def check_navigate_dir(self, template_relative_path: str, project_relative_path: str) -> bool:
        if self._matcher.ignore_paths_matcher.is_match(
                template_relative_path,
                self._template_options,
                self._config_template
            ):
            return False

        if self._config_template.conditional:
            for conditional_file in self._config_template.conditional:
                if conditional_file.location == template_relative_path:
                    condition = template_processor.process(
                        self._template_options,
                        conditional_file.condition,
                        [],
                        template_relative_path,
                        self._config_template.override_tag_start,
                        self._config_template.override_tag_end,
                        self._config_template.override_statement_start,
                        self._config_template.override_statement_end
                    )
                    if not str_to_bool(condition):
                        logging.debug(f"Skipping conditional file {template_relative_path} due to condition result: {condition}")
                        return False

        return True

    async def resolve_template_path(self, template_relative_path: str) -> str:
        replacement = self._matcher.rename_rules_replacer.replace(
            template_relative_path,
            self._template_options,
            self._config_template
        )

        return template_processor.process(
            self._template_options,
            replacement,
            [],
            template_relative_path,
            self._config_template.override_tag_start,
            self._config_template.override_tag_end,
            self._config_template.override_statement_start,
            self._config_template.override_statement_end
        )

    async def on_folder_not_found_project(self, relative_path: str, template_path: str, folder_path: str):
        pass

    async def on_file_not_found_project(
        self,
        template_relative_path: str,
        project_relative_path: str,
        template_path: str,
        project_path: str
    ):
        await self.process_file(
            template_relative_path,
            project_relative_path,
            template_path,
            project_path,
            False,
            True
        )

    async def process_file(
        self,
        template_relative_path: str,
        project_relative_path: str,
        template_path: str,
        project_path: str,
        exists: bool,
        perform_multiplex: bool
    ):

        ignore_inherited_files_type = self._config_template.get_ignore_inherited_files()
        if ignore_inherited_files_type != IgnoreInheritedFilesType.NONE and self._config_template_project.template_file_cache is not None:
            cur_file = self._config_template_project.template_file_cache.get(template_relative_path)
            if cur_file is not None:
                if ignore_inherited_files_type == IgnoreInheritedFilesType.ALL or cur_file.is_readonly:
                    logging.debug(f"ignoring template inherited file[{cur_file.relative_path}], is_readonly[{cur_file.is_readonly}]")
                    return

        is_remove_path = self._matcher.remove_paths_matcher.is_match(
            project_relative_path,
            self._template_options,
            self._config_template
        )

        if is_remove_path:
            logging.debug(f'Ignoring remove-path: {project_relative_path}')
            return

        is_ignore = self._matcher.ignore_paths_matcher.is_match(
            template_relative_path,
            self._template_options,
            self._config_template
        )

        if is_ignore:
            logging.debug(f"ignoring file: {template_relative_path}")
            return

        if self._config_template.conditional:
            for conditional_file in self._config_template.conditional:
                if conditional_file.location == template_relative_path:
                    condition = template_processor.process(
                        self._template_options,
                        conditional_file.condition,
                        [],
                        template_relative_path,
                        self._config_template.override_tag_start,
                        self._config_template.override_tag_end,
                        self._config_template.override_statement_start,
                        self._config_template.override_statement_end
                    )
                    if not str_to_bool(condition):
                        logging.debug(f"Skipping conditional file {template_relative_path} due to condition result: {condition}")
                        return

        if perform_multiplex:
            any_multiplexed = False

            # multiplex logic
            for multiplex in self._config_template.multiplex:
                if multiplex.source == template_relative_path:
                    any_multiplexed = True
                    logging.debug(f"processing multiplex rule for {template_relative_path}")

                    item_source = resolve_nested_key(self._template_options, multiplex.items)

                    # item_source = self._template_options.get(multiplex.items)
                    if item_source is None:
                        logging.debug(f"item source not found: {multiplex.items}")
                        continue

                    items = []
                    if isinstance(item_source, str):
                        items = [s.strip() for s in item_source.split(",")]
                    elif isinstance(item_source, list):
                        items = item_source
                    else:
                        logging.debug(f"not sure how to enumerate {multiplex.items}, it must be a string or list, currently it is: {type(item_source)}")
                        continue

                    for item in items:
                        new_template_options = self._template_options.copy()
                        new_template_options["multiplex_item"] = item

                        item_path = template_processor.process(
                            new_template_options,
                            multiplex.destination,
                            [],
                            template_relative_path,
                            self._config_template.override_tag_start,
                            self._config_template.override_tag_end,
                            self._config_template.override_statement_start,
                            self._config_template.override_statement_end
                        )

                        logging.debug(f"multiplexing file: {item_path}")


                        project_path = str(Path(self._project_root).joinpath(item_path).resolve())
                        new_file_exists = os.path.exists(project_path)

                        # swap out template options temporarily
                        current_template_options = self._template_options
                        self._template_options = new_template_options
                        await self.process_file(
                            template_relative_path,
                            item_path,
                            template_path,
                            project_path,
                            new_file_exists,
                            False
                        )
                        self._template_options = current_template_options

            # After performing the multiplex do not process other logic
            if any_multiplexed:
                logging.debug(f"Done processing multiplex for file {template_relative_path}")
                return


        is_project_ignore = self._matcher.project_template_ignore_paths.is_match(
            project_relative_path,
            self._template_options,
            self._config_template
        )
        if is_project_ignore:
            logging.debug(f"ignoring project-template ignored file: {project_relative_path}")
            return


        is_replacement = self._matcher.replacement_paths_matcher.is_match(
            project_relative_path,
            self._template_options,
            self._config_template
        )

        use_deprecated_readonly_structure = self._config_template.useDeprecatedUserPaths()

        # new way of designating which files belong to the template or project:
        is_readonly_path = self._matcher.readonly_paths_matcher.is_match(
            project_relative_path,
            self._template_options,
            self._config_template
        )

        is_optional_path = self._matcher.optional_paths_matcher.is_match(
            project_relative_path,
            self._template_options,
            self._config_template
        )

        if is_optional_path and exists:
            logging.debug(f'Ignoring optional-path which exists: {project_relative_path}')
            return

        # old way of designating which files belong to the template or project:
        is_user = self._matcher.user_paths_matcher.is_match(
            project_relative_path,
            self._template_options,
            self._config_template
        )

        should_be_readonly = \
            (
                (   # New way: readonly only if "readonly path"
                    not use_deprecated_readonly_structure
                    and is_readonly_path
                ) or
                (   # Old way: readonly if not user path
                    use_deprecated_readonly_structure
                    and not is_user
                )
             )

        await self.handle_file(
            project_path,
            template_path,
            template_relative_path,
            project_relative_path,
            exists,
            is_replacement,
            should_be_readonly
        )


    async def on_both_folders_exist(self, relative_path: str, template_path: str, project_path: str):
        pass

    async def on_both_files_exist(
            self,
            template_relative_path: str,
            project_relative_path: str,
            template_path: str,
            project_path: str
    ):
        await self.process_file(
            template_relative_path,
            project_relative_path,
            template_path,
            project_path,
            True,
            True
        )

def resolve_nested_key(thing: dict, key_path: str):
    """
    Resolves a nested key path like 'x.y.z' by navigating self._template_options.

    :param key_path: A dot-separated string representing the nested keys.
    :return: The value at the specified key path, or None if the path is invalid.
    """
    keys = key_path.split(".")
    value = thing

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            logging.debug(f"Key path '{key_path}' is invalid at '{key}'")
            return None

    return value