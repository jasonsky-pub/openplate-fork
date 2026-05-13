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


class RecursiveWalkListener:

    async def check_navigate_dir(self, template_relative_path: str, project_relative_path: str) -> bool:
        pass

    async def resolve_template_path(self, template_relative_path: str) -> str:
        pass

    async def on_folder_not_found_project(self, relative_path: str, template_path: str, project_path: str):
        pass

    async def on_file_not_found_project(
        self,
        template_relative_path: str,
        project_relative_path: str,
        template_path: str,
        project_path: str
    ):
        pass

    async def on_both_folders_exist(self, relative_path: str, template_path: str, project_path: str):
        pass

    async def on_both_files_exist(
        self,
        template_relative_path: str,
        project_relative_path: str,
        template_path: str,
        project_path: str
    ):
        pass

    async def on_complete(
        self,
        template_path: str,
        project_path: str
    ):
        pass
