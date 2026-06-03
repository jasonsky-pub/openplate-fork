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
from dataclasses import dataclass
import re
import subprocess
from typing import Optional
from urllib.parse import parse_qsl

from openplate.temporary_folder import TemporaryFolder
from openplate.walk.recursive_walker import norm_relative_path


@dataclass(frozen=True)
class GitTemplateReference:
    source_reference: str
    repo_location: str
    branch_name: Optional[str]
    template_path: Optional[str]

    @classmethod
    def parse(cls, source_reference: str):
        if source_reference is None:
            raise TypeError

        reference_string = source_reference.strip()
        if not reference_string:
            raise ValueError("Template source reference cannot be blank")

        reference_parts = reference_string.split("#")
        if len(reference_parts) > 2:
            raise ValueError(f"Bad template source reference, too many '#': {source_reference}")

        repo_and_query = reference_parts[0].strip()
        if not repo_and_query:
            raise ValueError("Template source reference must include a repository location")

        branch_name = None
        if len(reference_parts) == 2:
            branch_name = reference_parts[1].strip()
            if not branch_name:
                raise ValueError("Template source reference has an empty branch or tag")

        repo_location = repo_and_query
        template_path = None

        if "?" in repo_and_query:
            repo_location, query_string = repo_and_query.split("?", 1)
            repo_location = repo_location.strip()
            if not repo_location:
                raise ValueError("Template source reference must include a repository location")

            query_pairs = parse_qsl(query_string, keep_blank_values=True)
            query_parameters = {}
            for key, value in query_pairs:
                query_parameters.setdefault(key, []).append(value)

            unknown_keys = [key for key in query_parameters if key != "path"]
            if unknown_keys:
                raise ValueError(f"Unsupported template source query parameter(s): {', '.join(sorted(unknown_keys))}")

            if "path" in query_parameters:
                raw_path_values = query_parameters["path"]
                if len(raw_path_values) != 1:
                    raise ValueError("Template source path may only be specified once")

                raw_path = raw_path_values[0].strip()
                if not raw_path:
                    raise ValueError("Template source path cannot be blank")
                if raw_path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[/\\]", raw_path):
                    raise ValueError("Template source path must be relative to the repository root")

                normalized_path = norm_relative_path(raw_path)
                if normalized_path in ("", "."):
                    raise ValueError("Template source path must reference a sub-folder inside the repository")

                template_path = normalized_path

        return cls(reference_string, repo_location, branch_name, template_path)


class GitClonedTemporaryFolder:
    def __init__(self, source_reference: str):
        if source_reference is None:
            raise TypeError

        self.reference = GitTemplateReference.parse(source_reference)
        self.repo_location = self.reference.repo_location
        self.branch_name = self.reference.branch_name


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
