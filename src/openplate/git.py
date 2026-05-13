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
import subprocess
from typing import Optional

from openplate.temporary_folder import TemporaryFolder


class GitClonedTemporaryFolder:
    def __init__(self, repo_location: str):
        if repo_location is None:
            raise TypeError

        url_parts = repo_location.split("#")
        if len(url_parts) > 2:
            raise TypeError
        self.repo_location = url_parts[0]
        self.branch_name = None
        if len(url_parts) == 2:
            self.branch_name = url_parts[1]


    def folder_path(self):
        return self._temp_folder.folder_path()

    def __enter__(self):
        self._temp_folder = TemporaryFolder()
        self._temp_folder.__enter__()

        logging.debug("Cloning Git: " + self.repo_location + " branch: " + str(self.branch_name) + " into: " + self._temp_folder.folder_path())

        git_clone_cmd = ["git", "clone"]
        if self.branch_name is not None:
            git_clone_cmd += ["--branch", self.branch_name]

        git_clone_cmd += [self.repo_location, self._temp_folder.folder_path()]
        result = subprocess.run(
            git_clone_cmd,
            cwd=self._temp_folder.folder_path(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8'
        )

        if result.returncode != 0:
            outputText = result.stdout
            logging.error(
                "Error from Source Control. url: " + self.repo_location + " exitCode:" + result.returncode.__str__() + ", text: " + outputText)
            logging.error(outputText)
            self.__exit__(None, None, None)
            raise ChildProcessError

        get_sha_result = subprocess.run(
            [
                "git",
                'rev-parse',
                '--short',
                'HEAD'
            ], cwd=self._temp_folder.folder_path(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

        if get_sha_result.returncode != 0:
            outputText = get_sha_result.stdout
            logging.error(
                "Error getting git SHA.  exitCode:" + get_sha_result.returncode.__str__() + ", text: " + outputText)
            self.__exit__(None, None, None)
            raise ChildProcessError

        self.repo_sha = get_sha_result.stdout

        # before processing templates, remove the .git folder:
        self._temp_folder.remove_sub_path(".git")

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._temp_folder.__exit__(exception_type, exception_value, traceback)


def get_git_url(folder_path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "config",
                "--get",
                "remote.origin.url"
            ], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

        outputText = result.stdout
        if result.returncode != 0:
            if outputText is not None:
                outputText = outputText.strip()

            logging.debug(f"NON-FATAL: git errored, assuming folder not a git location: {folder_path}, detail: {outputText}")
            return None

        return outputText.strip()
    except Exception as e:
        logging.debug(f"NON-FATAL: Error when attempting to identify git location: {e.__str__()}")
        return None

def get_git_email(folder_path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "config",
                "--get",
                "user.email"
            ], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

        outputText = result.stdout
        if result.returncode != 0:
            if outputText is not None:
                outputText = outputText.strip()

            logging.debug(f"NON-FATAL: git errored, assuming folder not a git email: {folder_path}, detail: {outputText}")
            return None

        return outputText.strip()
    except Exception as e:
        logging.debug(f"NON-FATAL: Error when attempting to identify git email: {e.__str__()}")
        return None


def get_git_last_tag(folder_path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "describe",
                "--abbrev=0"
                "--tags"
            ], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

        outputText = result.stdout
        if result.returncode != 0:
            if outputText is not None:
                outputText = outputText.strip()
            logging.debug(f"NON-FATAL: git errored, assuming no tag: {folder_path}, detail: {outputText}")
            return None

        return outputText.strip()
    except Exception as e:
        logging.debug(f"NON-FATAL: Error when attempting to identify git tag: {e.__str__()}")
        return None
