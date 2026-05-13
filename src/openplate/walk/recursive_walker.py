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
import asyncio
import logging
import os.path
import re

from openplate.walk.recursive_walk_listener import RecursiveWalkListener

hardcoded_ignore_paths = [
    '.git',
    '.openplate.project.yaml',
    'openplate.template.yaml'
]


class WalkTemplateOptions:
    def __init__(self, create_destination_folders: bool = True):
        self.create_destination_folders = create_destination_folders


async def begin_recursive_walk(
        template_folder: str,
        project_folder: str,
        options: WalkTemplateOptions,
        listener: RecursiveWalkListener
):
    await recursive_walk(
        template_folder,
        project_folder,
        '',
        options,
        listener
    )
    await listener.on_complete(template_folder, project_folder)



async def recursive_walk(
        template_root_folder: str,
        project_root_folder: str,
        template_relative_path: str,
        options: WalkTemplateOptions,
        listener: RecursiveWalkListener
):
    if options is None:
        raise TypeError
    if template_relative_path is None:
        raise TypeError
    if template_root_folder is None:
        raise TypeError
    if project_root_folder is None:
        raise TypeError
    if listener is None:
        raise TypeError

    if template_relative_path in hardcoded_ignore_paths:
        return

    original_project_relative_path = await listener.resolve_template_path(template_relative_path)

    # resolve any ../
    project_relative_path = norm_relative_path(original_project_relative_path)

    template_folder = os.path.join(template_root_folder, template_relative_path)
    if project_relative_path == "":
        project_folder = project_root_folder
    else:
        project_folder = os.path.join(project_root_folder, project_relative_path)

    logging.debug(f"Inspecting folder: {template_folder} -> {project_folder}")

    if not os.path.exists(template_folder):
        raise FileNotFoundError("Template folder not found: " + template_folder)

    if not os.path.isdir(template_folder):
        raise FileNotFoundError("Template folder location found but not a folder: " + template_folder)

    tasks = []

    if not await listener.check_navigate_dir(template_relative_path, project_relative_path):
        logging.debug(f"Skipping folder that we shouldn't inspect: {project_folder}")
        return

    if os.path.exists(project_folder):
        if not os.path.isdir(project_folder):
            raise FileExistsError("File exists where folder needed: " + template_folder)

        tasks.append(
            asyncio.create_task(
                listener.on_both_folders_exist(template_relative_path, template_folder, project_folder)
            )
        )
    else:
        if not options.create_destination_folders:
            return

        project_folder_abs = os.path.abspath(project_folder)
        logging.debug(f"Creating folder: {project_relative_path}")
        os.makedirs(project_folder_abs, exist_ok=True)

        tasks.append(
            asyncio.create_task(
                listener.on_folder_not_found_project(template_relative_path, template_folder, project_folder)
            )
        )

    for sub_path in os.listdir(template_folder):
        new_template_path = os.path.join(template_folder, sub_path)

        template_relative_sub_path = \
            template_relative_path + (
                '/' if len(template_relative_path) > 0 and template_relative_path[-1] != '/' else '') + sub_path

        original_project_relative_sub_path = await listener.resolve_template_path(template_relative_sub_path)

        # resolve and validate:
        project_relative_sub_path = norm_relative_path(original_project_relative_sub_path)

        logging.debug(f"Inspecting file: {template_relative_sub_path} -> {project_relative_sub_path}")

        new_project_path = os.path.join(project_root_folder, project_relative_sub_path)

        if not os.path.isdir(new_template_path):
            # template file:
            if not os.path.exists(new_project_path):
                # project doesn't have file:
                tasks.append(
                    asyncio.create_task(
                        listener.on_file_not_found_project(
                            template_relative_sub_path,
                            project_relative_sub_path,
                            new_template_path,
                            new_project_path
                        )
                    )
                )
            else:
                # project has the file but it is a folder (conflicting with template)
                if os.path.isdir(new_project_path):
                    raise FileExistsError("Folder exists where file needed: " + new_project_path)

                # project has file
                tasks.append(
                    asyncio.create_task(
                        listener.on_both_files_exist(
                            template_relative_sub_path,
                            project_relative_sub_path,
                            new_template_path,
                            new_project_path
                        )
                    )
                )
        else:
            # template sub folder:
            tasks.append(
                asyncio.create_task(
                    recursive_walk(
                        template_root_folder,
                        project_root_folder,
                        template_relative_sub_path,
                        options,
                        listener
                    )
                )
            )

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    exceptions = []
    for task in done:
        # make sure to trigger any exceptions
        try:
            task.result()
        except Exception as ex:
            if isinstance(ex, ExceptionGroup):
                for ex2 in ex.exceptions:
                    exceptions.append(ex2)
            else:
                exceptions.append(ex)

    if exceptions:
        if len(exceptions)==1:
            raise exceptions[0]
        else:
            raise ExceptionGroup("Errors occurred", exceptions)


def norm_relative_path(path: str):
    # First strip off leading slashes:
    path_no_slash = path.lstrip("/\\")

    # Then convert to a proper relative path:
    norm_path = os.path.normpath(path_no_slash)

    # Ensure no more ..'s or / references to not access outside of project root
    sub_parts = re.split(r"[\\/]", norm_path)
    if "" in sub_parts:
        raise ValueError(f"Bad relative path, contains an empty or root element: {path}")

    if ".." in sub_parts:
        raise ValueError(f"Bad relative path, references files outside of root: {path}")

    # return all relative paths with unix slashes (so templates match properly):
    return norm_path.replace("\\", "/")
