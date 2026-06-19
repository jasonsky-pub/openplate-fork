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
from typing import Optional

from openplate import project_config_resolver, template_processor
from openplate.prompts.prompt_document import PromptInputTracker
from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings, OpenPlateRuntimeSettings
from openplate.git import get_git_last_tag
from openplate.project_metadata_resolver import resolve_template_source_metadata
from openplate.sibling_template_resolver import render_sibling_template_config
from openplate.shell_command_processor import process_command
from openplate.util import str_to_bool
from openplate.walk import template_init_commands_gate
from openplate.walk.init_walker import walk_init
from openplate.walk.recursive_walker import norm_relative_path
from openplate.walk.update_walker import walk_update
from openplate.walk.verify_walker import VerifyWalkOptions, walk_verify


async def source_template_recursive_walk_all(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    destination: str,
    walk_options: VerifyWalkOptions,
    config_project: project_config.ProjectConfig,
    allow_template_commands: bool,
    perform_init_walk: bool,
    perform_verify_walk: bool,
    perform_update_walk: bool,
    create_non_template_files: bool,
    update_non_template_files: bool,
    raise_error_on_verify: bool,
    fail_on_prompt: bool,
    prompt_input_tracker: Optional[PromptInputTracker] = None,
):
    project_config_changed = False
    found_changes = False
    last_sha = ""
    for template in config_project.templates:
        current_project_config_changed, current_found_changes, sha = await source_template_recursive_walk_single(
            settings,
            runtime_settings,
            template,
            destination,
            walk_options,
            config_project,
            allow_template_commands,
            perform_init_walk,
            perform_verify_walk,
            perform_update_walk,
            create_non_template_files,
            update_non_template_files,
            raise_error_on_verify,
            fail_on_prompt,
            prompt_input_tracker,
        )
        if current_project_config_changed:
            project_config_changed = True
        if current_found_changes:
            found_changes = True
        if sha:
            last_sha = sha

    return project_config_changed, found_changes, last_sha

async def source_template_recursive_walk_single(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_project_template: project_config.ProjectTemplateConfig,
    project_folder: str,
    walk_options: VerifyWalkOptions,
    config_project: project_config.ProjectConfig,
    allow_template_commands: bool,
    perform_init_walk: bool,
    perform_verify_walk: bool,
    perform_update_walk: bool,
    create_non_template_files: bool,
    update_non_template_files: bool,
    raise_error_on_verify: bool,
    fail_on_prompt: bool,
    prompt_input_tracker: Optional[PromptInputTracker] = None,
):
    # Note, Dest folder is no longer a root for the template
    # both the repo root and the dest folder will be available to the template

    if not os.path.exists(project_folder):
        raise FileNotFoundError("Project folder not found: " + project_folder)

    source = config_project_template.to_source(settings)

    found_changes = False
    project_config_changed = False

    with source:
        logging.debug(f"Loading Template Configuration file")
        config_template = template_config.from_file(
            os.path.join(source.folder_path(), template_config.template_config_file_name))
        logging.debug(f"useDeprecatedUserPaths: {config_template.useDeprecatedUserPaths()}")

        if perform_init_walk and config_template.init_commands is not None:
            if not template_init_commands_gate.confirm_continue_with_template_init_commands(
                source=source,
                init_commands=config_template.init_commands,
                project_folder=project_folder,
                allow_template_commands=allow_template_commands,
                fail_on_prompt=fail_on_prompt,
            ):
                raise SystemExit(1)

        # Update project's default dest_folder if not specified
        if config_project_template.dest_folder is None:
            config_project_template.dest_folder = config_template.default_dest_folder or ""
            project_config_changed = True

        logging.debug(f"Using dest_folder: {config_project_template.dest_folder}")

        config_template_project = None

        try:
            logging.debug(f"Loading Template Project Configuration file")
            config_template_project = project_config.from_file(
                settings,
                os.path.join(source.folder_path(), project_config.project_config_file_name)
            )
        except Exception:
            logging.debug(f"No Template Project config or other error (ok)")

        if resolve_template_source_metadata(config_project_template, source):
            project_config_changed = True

        # Answer questions:
        if project_config_resolver.resolve(
            settings,
            runtime_settings,
            config_template,
            config_project,
            config_project_template,
            project_folder,
            source.folder_path(),
            fail_on_prompt,
            prompt_input_tracker,
        ):
            project_config_changed = True

        new_template_version = get_git_last_tag(source.folder_path())
        if new_template_version and new_template_version != config_project_template.version:
            config_project_template.version = new_template_version
            project_config_changed = True

        template_options = template_processor.compile_template_options(
            config_template,
            config_project,
            config_project_template,
            source.folder_path(),
            project_folder,
            runtime_settings.ignore_tool_version
        )

        # Handle Sibling templates:
        if config_template.require_sibling_templates is not None:
            for sibling_template in config_template.require_sibling_templates:
                if sibling_template.condition:
                    rendered_condition = template_processor.process(
                        template_options,
                        sibling_template.condition,
                        [],
                        "Sibling Template URL",
                        config_template.override_tag_start,
                        config_template.override_tag_end,
                        config_template.override_statement_start,
                        config_template.override_statement_end
                    )
                    if not str_to_bool(rendered_condition):
                        logging.debug(f"Skipping sibling template {sibling_template.template_url} due to condition result: {rendered_condition}")
                        continue

                model_template_config = render_sibling_template_config(
                    config_template,
                    template_options,
                    sibling_template,
                    source,
                )

                # If the template isnt already on the project, add it and walk it before continuing:
                if not config_project.has_template(model_template_config):
                    logging.debug(f"Sibling is missing, adding {model_template_config.__str__()}")
                    config_project.templates.append(model_template_config)
                    project_config_changed = True
                    (sub_project_config_changed, sub_found_changes, sub_repo_sha) = \
                        await source_template_recursive_walk_single(
                            settings,
                            runtime_settings,
                            model_template_config,
                            project_folder,
                            walk_options,
                            config_project,
                            allow_template_commands,
                            perform_init_walk,
                            perform_verify_walk,
                            perform_update_walk,
                            create_non_template_files,
                            update_non_template_files,
                            raise_error_on_verify,
                            fail_on_prompt,
                            prompt_input_tracker,
                        )
                    if sub_found_changes:
                        found_changes = True
                else:
                    logging.debug(f"Sibling found, skipping {model_template_config.__str__()}")

                # After processing each sibling, need to refresh the variables:
                # for example: to get new configs from sibling 1 which are needed in sibling 2
                template_options = template_processor.compile_template_options(
                    config_template,
                    config_project,
                    config_project_template,
                    source.folder_path(),
                    project_folder,
                    runtime_settings.ignore_tool_version
                )

        if perform_init_walk:
            walk_issues = await walk_init(
                settings,
                source,
                project_folder,
                config_project,
                config_project_template,
                config_template_project,
                config_template,
                template_options
            )
            if len(walk_issues) > 0:
                found_changes = True
                if raise_error_on_verify:
                    logging.error("Issues found in destination folder:")
                    for issue in walk_issues:
                        logging.error(issue)
                    raise RuntimeError("Issues found in destination folder")

        if perform_verify_walk:
            walk_issues = await walk_verify(
                settings,
                walk_options,
                source,
                project_folder,
                config_project,
                config_project_template,
                config_template_project,
                config_template,
                template_options
            )
            if len(walk_issues) > 0:
                found_changes = True
                if raise_error_on_verify:
                    logging.error("Issues found in destination folder:")
                    for issue in walk_issues:
                        logging.error(issue)
                    raise RuntimeError("Issues found in destination folder")

        if perform_update_walk:
            await walk_update(
                settings,
                source,
                project_folder,
                config_project,
                config_project_template,
                config_template_project,
                config_template,
                template_options,
                create_non_template_files,
                update_non_template_files
            )

        # run init commands
        if perform_init_walk and config_template.init_commands is not None:
            for idx, init_command in enumerate(config_template.init_commands):
                if not template_init_commands_gate.confirm_run_init_command(
                    source=source,
                    init_command=init_command,
                    command_index=idx,
                    template_options=template_options,
                    config_template=config_template,
                    project_folder=project_folder,
                    allow_template_commands=allow_template_commands,
                    fail_on_prompt=fail_on_prompt,
                ):
                    raise SystemExit(1)

                command = template_processor.process(
                    template_options,
                    str(init_command.command),
                    [],
                    f"init_commands[{idx}]",
                    config_template.override_tag_start,
                    config_template.override_tag_end,
                    config_template.override_statement_start,
                    config_template.override_statement_end,
                )

                if not init_command.folder:
                    folder = project_folder
                else:
                    folder_processed = template_processor.process(
                        template_options,
                        str(init_command.folder),
                        [],
                        f"init_commands[{idx}]",
                        config_template.override_tag_start,
                        config_template.override_tag_end,
                        config_template.override_statement_start,
                        config_template.override_statement_end
                    )
                    relative_folder = norm_relative_path(folder_processed)
                    folder = os.path.join(project_folder, relative_folder)

                await process_command(command, folder)

        return project_config_changed, found_changes, source.repo_sha()

