import os
from dataclasses import dataclass
from typing import Optional

from openplate.git import get_git_root
from openplate.walk.recursive_walker import norm_relative_path


@dataclass(frozen=True)
class ProjectRuntimeContext:
    project_root_folder: str
    dest_folder: str
    project_git_mode: bool
    invocation_folder: str
    invocation_relative_folder: str


def _normalize_abs_path(path: str) -> str:
    if path is None:
        raise TypeError

    return os.path.realpath(os.path.abspath(os.path.normpath(path)))


def _normalize_dest_folder(dest_folder: Optional[str]) -> Optional[str]:
    if dest_folder is None:
        return None

    stripped_dest_folder = str(dest_folder).strip()
    if not stripped_dest_folder:
        return "."

    normalized_dest_folder = norm_relative_path(stripped_dest_folder)
    return normalized_dest_folder or "."


def _paths_match(left: str, right: str) -> bool:
    return os.path.normcase(_normalize_abs_path(left)) == os.path.normcase(_normalize_abs_path(right))


def resolve_project_runtime_context(
    invocation_folder: str,
    project_root_override: Optional[str],
    dest_folder_override: Optional[str],
) -> ProjectRuntimeContext:
    normalized_invocation_folder = _normalize_abs_path(invocation_folder)
    normalized_dest_folder = _normalize_dest_folder(dest_folder_override)

    if project_root_override is not None:
        normalized_project_root = _normalize_abs_path(project_root_override)
        git_root = get_git_root(normalized_project_root)
        if git_root is not None and not _paths_match(normalized_project_root, git_root):
            raise ValueError(
                "Explicit project roots inside Git must use the Git top-level folder"
            )

        return ProjectRuntimeContext(
            project_root_folder=normalized_project_root,
            dest_folder=normalized_dest_folder or ".",
            project_git_mode=git_root is not None,
            invocation_folder=normalized_invocation_folder,
            invocation_relative_folder=".",
        )

    invocation_git_root = get_git_root(normalized_invocation_folder)
    if invocation_git_root is not None:
        invocation_relative_folder = norm_relative_path(
            os.path.relpath(normalized_invocation_folder, invocation_git_root)
        ) or "."
        return ProjectRuntimeContext(
            project_root_folder=invocation_git_root,
            dest_folder=normalized_dest_folder or invocation_relative_folder,
            project_git_mode=True,
            invocation_folder=normalized_invocation_folder,
            invocation_relative_folder=invocation_relative_folder,
        )

    return ProjectRuntimeContext(
        project_root_folder=normalized_invocation_folder,
        dest_folder=normalized_dest_folder or ".",
        project_git_mode=False,
        invocation_folder=normalized_invocation_folder,
        invocation_relative_folder=".",
    )