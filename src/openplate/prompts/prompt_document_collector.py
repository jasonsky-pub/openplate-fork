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

from openplate import template_processor
from openplate.cfg import project_config, template_config
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings, OpenPlateSettings
from openplate.cfg.project_config import ProjectTemplateConfig
from openplate.project_metadata_resolver import resolve_project_metadata, resolve_template_source_metadata
from openplate.project_template_identity import prompt_dest_folder, prompt_identity_dest_folder, prompt_template_reference, source_cache_key
from openplate.prompts.prompt_document import PromptDocument, PromptDocumentBuilder, PromptSiblingTemplateInfo
from openplate.prompts.prompt_parameter_resolver import describe_prompt_parameters
from openplate.sibling_template_resolver import copy_template_with_raw_identity, find_matching_template, render_sibling_template_config
from openplate.sources.source_cache import CommandTemplateSourceCache, close_command_template_source_cache


async def _collect_prompt_document_template(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_project_template: ProjectTemplateConfig,
    project_folder: str,
    config_project: project_config.ProjectConfig,
    prompt_document_builder: PromptDocumentBuilder,
    source_cache: CommandTemplateSourceCache,
    visited_template_keys: set,
):
    if not os.path.exists(project_folder):
        raise FileNotFoundError("Project folder not found: " + project_folder)

    visit_key = (source_cache_key(settings, config_project_template), config_project_template.dest_folder)
    if visit_key in visited_template_keys:
        return

    visited_template_keys.add(visit_key)

    try:
        source = source_cache.get_source(config_project_template)
        config_template = template_config.from_file(
            os.path.join(source.folder_path(), template_config.template_config_file_name)
        )
    except Exception as ex:
        raise RuntimeError(
            f"Unable to fully inspect template for prompt export: {config_project_template.get_template_source_name()}"
        ) from ex

    if config_project_template.dest_folder is None:
        config_project_template.dest_folder = config_template.default_dest_folder or ""

    resolve_template_source_metadata(config_project_template, source)
    resolve_project_metadata(runtime_settings, config_project, project_folder)

    try:
        parameters = describe_prompt_parameters(
            settings,
            runtime_settings,
            config_template,
            config_project,
            config_project_template,
            project_folder,
            source.folder_path(),
        )
        template_options = template_processor.compile_template_options(
            config_template,
            config_project,
            config_project_template,
            source.folder_path(),
            project_folder,
            runtime_settings.ignore_tool_version,
        )
    except Exception as ex:
        logging.debug(
            "Unable to enumerate prompt metadata for %s: %s",
            config_project_template.get_template_source_name(),
            ex,
        )
        raise RuntimeError(
            f"Unable to enumerate prompt metadata for {config_project_template.get_template_source_name()}"
        ) from ex

    sibling_declarations = []

    if config_template.require_sibling_templates is None:
        prompt_document_builder.add_template(
            prompt_template_reference(config_project_template),
            prompt_dest_folder(config_project_template),
            parameters,
            None,
            prompt_identity_dest_folder(config_project_template),
        )
        return

    for sibling_template in config_template.require_sibling_templates:
        raw_template_reference = sibling_template.template_url
        raw_dest_folder = sibling_template.dest_folder
        raw_condition = sibling_template.condition

        try:
            rendered_sibling_template = render_sibling_template_config(
                config_template,
                template_options,
                sibling_template,
                source,
            )
        except Exception as ex:
            raise RuntimeError(
                f"Unable to resolve sibling declaration for prompt export: {raw_template_reference}"
            ) from ex

        matching_template = find_matching_template(config_project, rendered_sibling_template)
        if matching_template is not None:
            next_template = copy_template_with_raw_identity(
                matching_template,
                raw_template_reference,
                raw_dest_folder,
                raw_condition,
            )
        else:
            next_template = rendered_sibling_template

        sibling_declarations.append(
            PromptSiblingTemplateInfo(
                raw_template_reference,
                prompt_dest_folder(next_template),
                raw_condition,
            )
        )

        try:
            await _collect_prompt_document_template(
                settings,
                runtime_settings,
                next_template,
                project_folder,
                config_project,
                prompt_document_builder,
                source_cache,
                visited_template_keys,
            )
        except RuntimeError as ex:
            raise RuntimeError(
                f"Unable to resolve sibling declaration for prompt export: {raw_template_reference}"
            ) from ex

    prompt_document_builder.add_template(
        prompt_template_reference(config_project_template),
        prompt_dest_folder(config_project_template),
        parameters,
        sibling_declarations,
        prompt_identity_dest_folder(config_project_template),
    )


async def collect_prompt_document_single(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    config_project_template: ProjectTemplateConfig,
    project_folder: str,
    config_project: project_config.ProjectConfig,
) -> PromptDocument:
    prompt_document_builder = PromptDocumentBuilder()
    source_cache = CommandTemplateSourceCache(settings)
    visited_template_keys = set()

    try:
        await _collect_prompt_document_template(
            settings,
            runtime_settings,
            config_project_template,
            project_folder,
            config_project,
            prompt_document_builder,
            source_cache,
            visited_template_keys,
        )
    finally:
        close_command_template_source_cache(source_cache)

    return prompt_document_builder.build()


async def collect_prompt_document_all(
    settings: OpenPlateSettings,
    runtime_settings: OpenPlateRuntimeSettings,
    destination: str,
    config_project: project_config.ProjectConfig,
) -> PromptDocument:
    prompt_document_builder = PromptDocumentBuilder()
    source_cache = CommandTemplateSourceCache(settings)
    visited_template_keys = set()

    try:
        for config_project_template in list(config_project.templates):
            await _collect_prompt_document_template(
                settings,
                runtime_settings,
                config_project_template,
                destination,
                config_project,
                prompt_document_builder,
                source_cache,
                visited_template_keys,
            )
    finally:
        close_command_template_source_cache(source_cache)

    return prompt_document_builder.build()