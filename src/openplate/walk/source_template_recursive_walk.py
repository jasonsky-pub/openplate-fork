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
from dataclasses import dataclass, field
from typing import Optional

from openplate import project_config_resolver, template_processor
from openplate.prompts.prompt_document import PromptInputTracker
from openplate.cfg import template_config, project_config
from openplate.cfg.open_plate_settings import OpenPlateSettings, OpenPlateRuntimeSettings
from openplate.git import get_git_last_tag
from openplate.project_metadata_resolver import resolve_template_consent_metadata, resolve_template_source_metadata
from openplate.project_template_identity import source_cache_key
from openplate.sibling_template_resolver import find_matching_template, render_sibling_template_config
from openplate.shell_command_processor import process_command
from openplate.util import str_to_bool
from openplate.walk import template_init_commands_gate
from openplate.walk.init_walker import walk_init
from openplate.walk.recursive_walker import norm_relative_path
from openplate.walk.update_walker import walk_update
from openplate.walk.verify_walker import VerifyWalkOptions, walk_verify


TemplateNodeKey = tuple[tuple[str, str], str]
ExportIdentity = tuple[str, str]


@dataclass
class RenderedTemplateExport:
    producer_key: TemplateNodeKey
    location: str
    key: str
    value: str
    shared_export: bool


@dataclass
class CompletedTemplateNode:
    repo_sha: str
    visible_producer_keys: set[TemplateNodeKey] = field(default_factory=set)


@dataclass
class TemplateWalkRuntimeState:
    completed_nodes: dict[TemplateNodeKey, CompletedTemplateNode] = field(default_factory=dict)
    in_progress_nodes: set[TemplateNodeKey] = field(default_factory=set)
    export_registry: dict[ExportIdentity, list[RenderedTemplateExport]] = field(default_factory=dict)


@dataclass
class TemplateWalkResult:
    project_config_changed: bool
    found_changes: bool
    sha: str
    visible_producer_keys: set[TemplateNodeKey] = field(default_factory=set)


def _template_node_key(
    settings: OpenPlateSettings,
    config_project_template: project_config.ProjectTemplateConfig,
) -> TemplateNodeKey:
    return (
        source_cache_key(settings, config_project_template),
        config_project_template.dest_folder or ".",
    )


def _resolve_location(
    raw_location: Optional[str],
    default_location: str,
    template_options: dict[str, object],
    config_template: template_config.TemplateConfig,
    template_source: str,
) -> str:
    if raw_location is None or not str(raw_location).strip():
        return default_location

    rendered_location = template_processor.process(
        template_options,
        str(raw_location),
        [],
        template_source,
        config_template.override_tag_start,
        config_template.override_tag_end,
        config_template.override_statement_start,
        config_template.override_statement_end,
    )

    if not str(rendered_location).strip():
        return default_location

    return norm_relative_path(str(rendered_location).strip()) or "."


def _render_required_value(
    raw_value: str,
    field_name: str,
    template_options: dict[str, object],
    config_template: template_config.TemplateConfig,
    template_source: str,
) -> str:
    rendered_value = template_processor.process(
        template_options,
        str(raw_value),
        [],
        template_source,
        config_template.override_tag_start,
        config_template.override_tag_end,
        config_template.override_statement_start,
        config_template.override_statement_end,
    )

    normalized_value = str(rendered_value).strip()
    if not normalized_value:
        raise RuntimeError(f"{field_name} rendered blank for {template_source}")

    return normalized_value


def _register_template_exports(
    config_template: template_config.TemplateConfig,
    template_options: dict[str, object],
    config_project_template: project_config.ProjectTemplateConfig,
    runtime_state: TemplateWalkRuntimeState,
    node_key: TemplateNodeKey,
):
    default_location = config_project_template.dest_folder or "."
    template_source = config_project_template.get_template_source_name()

    for export in config_template.exports:
        rendered_key = _render_required_value(
            export.key,
            "Export key",
            template_options,
            config_template,
            template_source,
        )
        rendered_value = template_processor.process(
            template_options,
            str(export.value),
            [],
            f"Export value[{rendered_key}]",
            config_template.override_tag_start,
            config_template.override_tag_end,
            config_template.override_statement_start,
            config_template.override_statement_end,
        )
        rendered_location = _resolve_location(
            export.location,
            default_location,
            template_options,
            config_template,
            f"Export location[{rendered_key}]",
        )

        export_identity = (rendered_location, rendered_key)
        existing_exports = runtime_state.export_registry.get(export_identity, [])
        if existing_exports:
            if any(current.shared_export != export.shared_export for current in existing_exports):
                raise RuntimeError(
                    "Cannot mix shared and non-shared exports for "
                    f"location={rendered_location!r} key={rendered_key!r}"
                )
            if not export.shared_export:
                raise RuntimeError(
                    f"Duplicate export for location={rendered_location!r} key={rendered_key!r}"
                )

        runtime_state.export_registry.setdefault(export_identity, []).append(
            RenderedTemplateExport(
                node_key,
                rendered_location,
                rendered_key,
                str(rendered_value),
                export.shared_export,
            )
        )


def _resolve_template_imports(
    config_template: template_config.TemplateConfig,
    template_options: dict[str, object],
    config_project_template: project_config.ProjectTemplateConfig,
    visible_producer_keys: set[TemplateNodeKey],
    runtime_state: TemplateWalkRuntimeState,
) -> dict[str, object]:
    resolved_imports = {}
    default_location = config_project_template.dest_folder or "."
    template_source = config_project_template.get_template_source_name()

    for template_import in config_template.imports:
        rendered_export_key = _render_required_value(
            template_import.export_key,
            "Import export-key",
            template_options,
            config_template,
            template_source,
        )
        rendered_import_key = _render_required_value(
            template_import.import_key,
            "Import import-key",
            template_options,
            config_template,
            template_source,
        )
        rendered_location = _resolve_location(
            template_import.location,
            default_location,
            template_options,
            config_template,
            f"Import location[{rendered_export_key}]",
        )

        matching_exports = [
            current_export
            for current_export in runtime_state.export_registry.get((rendered_location, rendered_export_key), [])
            if current_export.producer_key in visible_producer_keys
        ]
        if not matching_exports:
            raise RuntimeError(
                "Unresolved import for "
                f"template={template_source!r} location={rendered_location!r} export-key={rendered_export_key!r}"
            )

        if matching_exports[0].shared_export:
            resolved_imports[rendered_import_key] = [current_export.value for current_export in matching_exports]
        else:
            resolved_imports[rendered_import_key] = matching_exports[0].value

    return resolved_imports


async def _source_template_recursive_walk_single_result(
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
    prompt_input_tracker: Optional[PromptInputTracker],
    runtime_state: TemplateWalkRuntimeState,
) -> TemplateWalkResult:
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

        # Update project's default dest_folder if not specified
        if config_project_template.dest_folder is None:
            config_project_template.dest_folder = config_template.default_dest_folder or ""
            project_config_changed = True

        node_key = _template_node_key(settings, config_project_template)
        completed_node = runtime_state.completed_nodes.get(node_key)
        if completed_node is not None:
            logging.debug("Template instance already completed, reusing exports for %s", node_key)
            return TemplateWalkResult(False, False, completed_node.repo_sha, set(completed_node.visible_producer_keys))

        if node_key in runtime_state.in_progress_nodes:
            logging.debug("Template instance already in progress, skipping recursive re-entry for %s", node_key)
            return TemplateWalkResult(False, False, "", set())

        runtime_state.in_progress_nodes.add(node_key)
        try:
            if perform_init_walk and config_template.init_commands is not None:
                if not template_init_commands_gate.confirm_continue_with_template_init_commands(
                    source=source,
                    init_commands=config_template.init_commands,
                    project_folder=project_folder,
                    allow_template_commands=allow_template_commands,
                    fail_on_prompt=fail_on_prompt,
                ):
                    raise SystemExit(1)

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

            if resolve_template_consent_metadata(config_template, config_project_template):
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

            visible_producer_keys = set()

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

                    matching_template = find_matching_template(config_project, model_template_config)
                    if matching_template is None:
                        logging.debug(f"Sibling is missing, adding {model_template_config.__str__()}")
                        config_project.templates.append(model_template_config)
                        project_config_changed = True
                        matching_template = model_template_config
                    else:
                        if matching_template.provenance is None:
                            logging.debug(
                                "Sibling found without provenance, preserving existing tracked template provenance state for %s",
                                matching_template,
                            )
                        logging.debug(f"Sibling found, reusing {matching_template.__str__()}")

                    sub_result = await _source_template_recursive_walk_single_result(
                        settings,
                        runtime_settings,
                        matching_template,
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
                        runtime_state,
                    )
                    if sub_result.project_config_changed:
                        project_config_changed = True
                    if sub_result.found_changes:
                        found_changes = True
                    visible_producer_keys.update(sub_result.visible_producer_keys)

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

            resolved_imports = _resolve_template_imports(
                config_template,
                template_options,
                config_project_template,
                visible_producer_keys,
                runtime_state,
            )
            template_options = template_processor.compile_template_options(
                config_template,
                config_project,
                config_project_template,
                source.folder_path(),
                project_folder,
                runtime_settings.ignore_tool_version,
                resolved_imports,
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

            template_options = template_processor.compile_template_options(
                config_template,
                config_project,
                config_project_template,
                source.folder_path(),
                project_folder,
                runtime_settings.ignore_tool_version,
                resolved_imports,
            )
            _register_template_exports(
                config_template,
                template_options,
                config_project_template,
                runtime_state,
                node_key,
            )

            visible_producer_keys.add(node_key)
            runtime_state.completed_nodes[node_key] = CompletedTemplateNode(
                source.repo_sha(),
                set(visible_producer_keys),
            )
            return TemplateWalkResult(
                project_config_changed,
                found_changes,
                source.repo_sha(),
                set(visible_producer_keys),
            )
        finally:
            runtime_state.in_progress_nodes.discard(node_key)


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
    runtime_state: Optional[TemplateWalkRuntimeState] = None,
):
    if runtime_state is None:
        runtime_state = TemplateWalkRuntimeState()

    project_config_changed = False
    found_changes = False
    last_sha = ""
    for template in config_project.templates:
        current_result = await _source_template_recursive_walk_single_result(
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
            runtime_state,
        )
        if current_result.project_config_changed:
            project_config_changed = True
        if current_result.found_changes:
            found_changes = True
        if current_result.sha:
            last_sha = current_result.sha

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
    runtime_state: Optional[TemplateWalkRuntimeState] = None,
):
    if runtime_state is None:
        runtime_state = TemplateWalkRuntimeState()

    result = await _source_template_recursive_walk_single_result(
        settings,
        runtime_settings,
        config_project_template,
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
        runtime_state,
    )
    return result.project_config_changed, result.found_changes, result.sha

