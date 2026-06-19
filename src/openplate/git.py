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
import os
import re
import subprocess
from typing import Optional
from urllib.parse import parse_qsl, quote, urlparse, urlunparse

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


@dataclass(frozen=True)
class GitUrlInfo:
    sanitized_url: str
    ssh_url: Optional[str]
    https_url: Optional[str]
    repo_org: Optional[str]
    repo_name: Optional[str]


@dataclass(frozen=True)
class GitHeadReference:
    value: str
    source: str


_SCP_GIT_URL_PATTERN = re.compile(
    r"^(?P<user>[^@\s]+)@(?P<host>[^:/?#\s]+):(?P<path>[^?#\s]+)$"
)


def _extract_repo_identity(repo_path: str) -> tuple[Optional[str], Optional[str]]:
    clean_parts = [part for part in str(repo_path).strip("/").split("/") if part]
    if len(clean_parts) < 2:
        return None, None

    repo_name = clean_parts[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if not repo_name:
        return None, None

    return clean_parts[-2], repo_name


def parse_git_url(url: str) -> Optional[GitUrlInfo]:
    if url is None:
        raise TypeError

    candidate = url.strip()
    if not candidate:
        raise ValueError("Git URL cannot be blank")

    scp_match = _SCP_GIT_URL_PATTERN.match(candidate)
    if scp_match is not None:
        user = scp_match.group("user")
        host = scp_match.group("host")
        repo_path = scp_match.group("path").lstrip("/")
        if not repo_path:
            return None

        repo_org, repo_name = _extract_repo_identity(repo_path)
        sanitized_url = f"{user}@{host}:{repo_path}"
        return GitUrlInfo(
            sanitized_url=sanitized_url,
            ssh_url=sanitized_url,
            https_url=f"https://{host}/{repo_path}",
            repo_org=repo_org,
            repo_name=repo_name,
        )

    parsed_url = urlparse(candidate)
    scheme = (parsed_url.scheme or "").lower()

    if scheme == "https":
        host = parsed_url.hostname
        repo_path = parsed_url.path.lstrip("/")
        if not host or not repo_path:
            return None

        repo_org, repo_name = _extract_repo_identity(repo_path)
        sanitized_url = urlunparse(("https", host, f"/{repo_path}", "", "", ""))
        return GitUrlInfo(
            sanitized_url=sanitized_url,
            ssh_url=f"git@{host}:{repo_path}",
            https_url=sanitized_url,
            repo_org=repo_org,
            repo_name=repo_name,
        )

    if scheme == "ssh":
        host = parsed_url.hostname
        repo_path = parsed_url.path.lstrip("/")
        if not host or not repo_path:
            return None

        repo_org, repo_name = _extract_repo_identity(repo_path)
        username = parsed_url.username or "git"
        netloc = host
        if parsed_url.username:
            netloc = f"{parsed_url.username}@{netloc}"
        if parsed_url.port:
            netloc = f"{netloc}:{parsed_url.port}"

        sanitized_url = urlunparse(("ssh", netloc, f"/{repo_path}", "", "", ""))
        ssh_url = None
        if parsed_url.port in (None, 22):
            ssh_url = f"{username}@{host}:{repo_path}"

        return GitUrlInfo(
            sanitized_url=sanitized_url,
            ssh_url=ssh_url,
            https_url=f"https://{host}/{repo_path}",
            repo_org=repo_org,
            repo_name=repo_name,
        )

    return None


def build_git_source_reference(repo_location: str, template_path: Optional[str], ref_name: Optional[str]) -> str:
    if repo_location is None:
        raise TypeError

    result = repo_location.strip()
    if not result:
        raise ValueError("Repository location cannot be blank")

    if template_path is not None:
        normalized_path = norm_relative_path(template_path)
        if normalized_path in ("", "."):
            raise ValueError("Template source path must reference a sub-folder inside the repository")
        result += f"?path={quote(normalized_path, safe='/')}"

    if ref_name is not None:
        stripped_ref = ref_name.strip()
        if not stripped_ref:
            raise ValueError("Template source ref cannot be blank")
        result += f"#{quote(stripped_ref, safe='/')}"

    return result


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

        self.head_reference = get_git_head_reference(self._temp_folder.folder_path())

        # before processing templates, remove the .git folder:
        self._temp_folder.remove_sub_path(".git")

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._temp_folder.__exit__(exception_type, exception_value, traceback)


def _run_git_stdout(folder_path: str, args: list[str], missing_message: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=folder_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8'
        )

        output_text = result.stdout
        if result.returncode != 0:
            if output_text is not None:
                output_text = output_text.strip()

            logging.debug(f"NON-FATAL: {missing_message}: {folder_path}, detail: {output_text}")
            return None

        return output_text.strip()
    except Exception as e:
        logging.debug(f"NON-FATAL: Error when running git command {args}: {e.__str__()}")
        return None


def get_git_root(folder_path: str) -> Optional[str]:
    git_root = _run_git_stdout(
        folder_path,
        ["rev-parse", "--show-toplevel"],
        "git errored, assuming folder not a git location"
    )
    if git_root is None:
        return None

    return os.path.abspath(os.path.normpath(git_root))


def get_git_head_reference(folder_path: str) -> Optional[GitHeadReference]:
    branch_name = _run_git_stdout(
        folder_path,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        "git errored, assuming HEAD is detached"
    )
    if branch_name:
        return GitHeadReference(branch_name, "branch")

    exact_tags = _run_git_stdout(
        folder_path,
        ["tag", "--points-at", "HEAD"],
        "git errored, assuming HEAD has no exact tags"
    )
    if exact_tags:
        tag_names = sorted(tag.strip() for tag in exact_tags.splitlines() if tag.strip())
        if tag_names:
            return GitHeadReference(tag_names[0], "tag")

    sha = _run_git_stdout(
        folder_path,
        ["rev-parse", "--short", "HEAD"],
        "git errored, assuming HEAD SHA unavailable"
    )
    if sha:
        return GitHeadReference(sha, "sha")

    return None


def get_git_url(folder_path: str) -> Optional[str]:
    return _run_git_stdout(
        folder_path,
        ["config", "--get", "remote.origin.url"],
        "git errored, assuming folder not a git location"
    )

def get_git_email(folder_path: str) -> Optional[str]:
    return _run_git_stdout(
        folder_path,
        ["config", "--get", "user.email"],
        "git errored, assuming folder not a git email"
    )


def get_git_last_tag(folder_path: str) -> Optional[str]:
    return _run_git_stdout(
        folder_path,
        ["describe", "--abbrev=0", "--tags"],
        "git errored, assuming no tag"
    )
