import subprocess
from pathlib import Path

import pytest

from openplate.git import build_git_source_reference, get_git_head_reference, parse_git_url
from openplate.project_runtime_context import resolve_project_runtime_context


pytestmark = pytest.mark.unit


def _create_git_repo(repo_path: Path):
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "OpenPlate Tests"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    (repo_path / "README.md").write_text("repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")


def test_parse_git_url_sanitizes_https_and_derives_url_families():
    parsed = parse_git_url("https://user:pass@github.com/my-org/my-repo.git")

    assert parsed is not None
    assert parsed.sanitized_url == "https://github.com/my-org/my-repo.git"
    assert parsed.https_url == "https://github.com/my-org/my-repo.git"
    assert parsed.ssh_url == "git@github.com:my-org/my-repo.git"
    assert parsed.repo_org == "my-org"
    assert parsed.repo_name == "my-repo"


def test_parse_git_url_supports_scp_and_ssh_scheme_forms():
    scp_parsed = parse_git_url("git@github.com:my-org/my-repo.git")
    ssh_parsed = parse_git_url("ssh://git@github.com/my-org/my-repo.git")

    assert scp_parsed is not None
    assert scp_parsed.sanitized_url == "git@github.com:my-org/my-repo.git"
    assert scp_parsed.https_url == "https://github.com/my-org/my-repo.git"

    assert ssh_parsed is not None
    assert ssh_parsed.sanitized_url == "ssh://git@github.com/my-org/my-repo.git"
    assert ssh_parsed.ssh_url == "git@github.com:my-org/my-repo.git"
    assert ssh_parsed.https_url == "https://github.com/my-org/my-repo.git"


def test_parse_git_url_returns_none_for_non_git_file_urls():
    assert parse_git_url("file:///c:/templates/python-api") is None


def test_build_git_source_reference_preserves_path_and_ref():
    assert (
        build_git_source_reference("https://github.com/my-org/template.git", "python/api", "release/v1")
        == "https://github.com/my-org/template.git?path=python/api#release/v1"
    )


def test_get_git_head_reference_prefers_alphabetical_exact_tag(tmp_path):
    repo_path = tmp_path / "template"
    _create_git_repo(repo_path)
    subprocess.run(["git", "tag", "v2"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "tag", "release-1"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "checkout", "--detach"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")

    resolved_ref = get_git_head_reference(str(repo_path))

    assert resolved_ref is not None
    assert resolved_ref.source == "tag"
    assert resolved_ref.value == "release-1"


def test_resolve_project_runtime_context_uses_git_top_level_and_invocation_relative_dest(tmp_path):
    repo_path = tmp_path / "repo"
    _create_git_repo(repo_path)
    invocation_folder = repo_path / "services" / "api"
    invocation_folder.mkdir(parents=True, exist_ok=True)

    context = resolve_project_runtime_context(str(invocation_folder), None, None)

    assert context.project_root_folder == str(repo_path.resolve())
    assert context.project_git_mode is True
    assert context.dest_folder == "services/api"
    assert context.invocation_relative_folder == "services/api"


def test_resolve_project_runtime_context_rejects_explicit_git_subfolder_root(tmp_path):
    repo_path = tmp_path / "repo"
    _create_git_repo(repo_path)
    subfolder = repo_path / "services" / "api"
    subfolder.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="Git top-level folder"):
        resolve_project_runtime_context(str(subfolder), str(subfolder), None)


def test_resolve_project_runtime_context_defaults_dest_to_root_for_explicit_project_root(tmp_path):
    project_root = tmp_path / "workspace"
    project_root.mkdir()

    context = resolve_project_runtime_context(str(tmp_path), str(project_root), None)

    assert context.project_root_folder == str(project_root.resolve())
    assert context.project_git_mode is False
    assert context.dest_folder == "."