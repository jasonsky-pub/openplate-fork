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
import re

from openplate.cfg import project_config
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings
from openplate.git import get_git_email, get_git_url


def resolve_project_metadata(
    runtime_settings: OpenPlateRuntimeSettings,
    config_project: project_config.ProjectConfig,
    project_base_folder: str,
) -> bool:
    any_changed = False

    project_folder_name = os.path.basename(os.path.abspath(os.path.normpath(project_base_folder)))
    if not config_project.project_folder_name or config_project.project_folder_name != project_folder_name:
        config_project.project_folder_name = project_folder_name
        any_changed = True

    try:
        project_src_url = get_git_url(project_base_folder)
        project_repo_name = None
        project_repo_org = None
        if project_src_url is not None:
            project_src_url = project_src_url.strip()
            # Extract org name using regex
            match = re.search(r'[:/](?P<org>[^/]+)/(?P<repo>[^/]+?)(\.git)?$', project_src_url)
            project_repo_org = match.group('org') if match else None
            project_repo_name = match.group('repo') if match else None

        if not config_project.project_src_url or config_project.project_src_url != project_src_url:
            config_project.project_src_url = project_src_url
            any_changed = True

        if not config_project.project_repo_org or config_project.project_repo_org != project_repo_org:
            config_project.project_repo_org = project_repo_org
            any_changed = True

        if not config_project.project_repo_name or config_project.project_repo_name != project_repo_name:
            config_project.project_repo_name = project_repo_name
            any_changed = True

    except Exception:
        pass

    # Do not update the user email when doing automated processing:
    if not runtime_settings.is_automation:
        try:
            last_updater_email = get_git_email(project_base_folder)
            if not config_project.last_updater_email or config_project.last_updater_email != last_updater_email:
                config_project.last_updater_email = last_updater_email
                any_changed = True
        except Exception:
            pass

    return any_changed