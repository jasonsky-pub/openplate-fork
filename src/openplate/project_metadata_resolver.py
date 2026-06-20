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
import os

from openplate.cfg import project_config
from openplate.cfg.template_config import TemplateConfig
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings
from openplate.git import (
    GitTemplateReference,
    build_git_source_reference,
    get_git_email,
    get_git_root,
    get_git_url,
    parse_git_url,
)
from openplate.util import str_to_bool


def _set_runtime_value(target, field_name: str, value) -> bool:
    current_value = getattr(target, field_name, None)
    if current_value == value:
        return False

    setattr(target, field_name, value)
    return True


def resolve_template_source_metadata(
    config_project_template: project_config.ProjectTemplateConfig,
    source,
) -> bool:
    source_reference = (source.template_url() or config_project_template.src_url or "").strip()
    if not source_reference:
        return False

    parsed_reference = GitTemplateReference.parse(source_reference)
    url_info = None
    if hasattr(source, "git_url_info"):
        url_info = source.git_url_info()
    if url_info is None:
        url_info = parse_git_url(parsed_reference.repo_location)

    if url_info is None:
        runtime_values = {
            "template_src_url": source_reference,
            "template_git_ssh_src_url": "",
            "template_git_https_src_url": "",
            "template_git_repo_url": "",
            "template_git_ssh_repo_url": "",
            "template_git_https_repo_url": "",
            "template_git_repo_org": "",
            "template_git_repo_name": "",
            "template_git_repo_path": "",
            "template_git_repo_ref": "",
        }
    else:
        explicit_ref = parsed_reference.branch_name
        resolved_ref = explicit_ref
        if resolved_ref is None and hasattr(source, "resolved_ref"):
            resolved_ref = source.resolved_ref()

        runtime_values = {
            "template_src_url": build_git_source_reference(
                url_info.sanitized_url,
                parsed_reference.template_path,
                explicit_ref,
            ),
            "template_git_ssh_src_url": build_git_source_reference(
                url_info.ssh_url,
                parsed_reference.template_path,
                explicit_ref,
            ) if url_info.ssh_url else "",
            "template_git_https_src_url": build_git_source_reference(
                url_info.https_url,
                parsed_reference.template_path,
                explicit_ref,
            ) if url_info.https_url else "",
            "template_git_repo_url": url_info.sanitized_url,
            "template_git_ssh_repo_url": url_info.ssh_url or "",
            "template_git_https_repo_url": url_info.https_url or "",
            "template_git_repo_org": url_info.repo_org or "",
            "template_git_repo_name": url_info.repo_name or "",
            "template_git_repo_path": parsed_reference.template_path or ".",
            "template_git_repo_ref": resolved_ref or "",
        }

    any_changed = False
    for field_name, value in runtime_values.items():
        if _set_runtime_value(config_project_template, field_name, value):
            any_changed = True

    return any_changed


def resolve_template_consent_metadata(
    config_template: TemplateConfig,
    config_project_template: project_config.ProjectTemplateConfig,
) -> bool:
    return _set_runtime_value(
        config_project_template,
        "requires_last_updater_email",
        bool(getattr(config_template, "requires_last_updater_email", False)),
    )


def resolve_last_updater_email_consent(runtime_settings: OpenPlateRuntimeSettings, settings, template_name: str) -> bool:
    if runtime_settings.last_updater_email_consent is not None:
        return runtime_settings.last_updater_email_consent

    if runtime_settings.allow_last_updater_email or settings.allow_last_updater_email:
        runtime_settings.last_updater_email_consent = True
        return True

    if runtime_settings.is_automation or runtime_settings.is_prompt_json_input or not runtime_settings.can_prompt_for_last_updater_email:
        runtime_settings.last_updater_email_consent = False
        return False

    while True:
        answer = input(
            f"Template '{template_name}' requires last_updater_email. Allow OpenPlate to read your Git email for this run? [y/N]: "
        )

        if not answer or not answer.strip():
            runtime_settings.last_updater_email_consent = False
            return False

        try:
            runtime_settings.last_updater_email_consent = str_to_bool(answer)
            return runtime_settings.last_updater_email_consent
        except ValueError:
            print("ERROR: Please answer yes or no.")


def resolve_project_metadata(
    runtime_settings: OpenPlateRuntimeSettings,
    config_project: project_config.ProjectConfig,
    project_base_folder: str,
    resolve_last_updater_email: bool = False,
) -> bool:
    any_changed = False
    root_folder_name = os.path.basename(os.path.abspath(os.path.normpath(project_base_folder)))

    project_git_mode = get_git_root(project_base_folder) is not None
    if _set_runtime_value(config_project, "project_git_mode", project_git_mode):
        any_changed = True

    project_folder_name = root_folder_name

    try:
        project_src_url = (get_git_url(project_base_folder) or "").strip()
        parsed_project_url = parse_git_url(project_src_url) if project_src_url else None
        sanitized_project_src_url = project_src_url
        if parsed_project_url is not None:
            sanitized_project_src_url = parsed_project_url.sanitized_url

        if _set_runtime_value(config_project, "project_src_url", sanitized_project_src_url):
            any_changed = True
        if _set_runtime_value(config_project, "project_git_repo_url", sanitized_project_src_url):
            any_changed = True
        if _set_runtime_value(config_project, "project_git_ssh_repo_url", parsed_project_url.ssh_url if parsed_project_url and parsed_project_url.ssh_url else ""):
            any_changed = True
        if _set_runtime_value(config_project, "project_git_https_repo_url", parsed_project_url.https_url if parsed_project_url and parsed_project_url.https_url else ""):
            any_changed = True

        project_repo_org = parsed_project_url.repo_org if parsed_project_url and parsed_project_url.repo_org else ""
        project_repo_name = parsed_project_url.repo_name if parsed_project_url and parsed_project_url.repo_name else ""

        if _set_runtime_value(config_project, "project_git_repo_org", project_repo_org):
            any_changed = True
        if _set_runtime_value(config_project, "project_git_repo_name", project_repo_name):
            any_changed = True
        if _set_runtime_value(config_project, "project_repo_org", project_repo_org):
            any_changed = True
        if _set_runtime_value(config_project, "project_repo_name", project_repo_name):
            any_changed = True

        if project_git_mode and project_repo_name:
            project_folder_name = project_repo_name

    except Exception:
        pass

    if _set_runtime_value(config_project, "project_folder_name", project_folder_name):
        any_changed = True

    if resolve_last_updater_email:
        try:
            last_updater_email = get_git_email(project_base_folder)
            if not config_project.last_updater_email or config_project.last_updater_email != last_updater_email:
                config_project.last_updater_email = last_updater_email
                any_changed = True
        except Exception:
            pass

    return any_changed