import asyncio
import subprocess
from pathlib import Path

import pytest

from openplate.__main__ import async_main, create_arg_parser, resolve_project_init_source_reference
from openplate.cfg import open_plate_settings
from openplate.git import GitTemplateReference
from openplate.sources.url_source import UrlTemplateSource


pytestmark = pytest.mark.unit


def _create_git_repo(repo_path: Path):
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "OpenPlate Tests"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")


def test_create_arg_parser_accepts_positional_source_url():
    args = ["openplate", "project", "init", "https://example.com/template.git#main"]
    parser = create_arg_parser(args)

    result = parser.parse_args(args[1:])

    assert result.command == "project-init"
    assert result.source == "https://example.com/template.git#main"
    assert result.url is None


def test_resolve_project_init_source_reference_rejects_conflicting_inputs():
    result = create_arg_parser(["openplate", "project", "init"]).parse_args([
        "project", "init", "https://example.com/template.git#main", "-r", "https://example.com/other.git#main"
    ])

    with pytest.raises(ValueError, match="Specify exactly one template source URL"):
        resolve_project_init_source_reference(result)


def test_create_arg_parser_rejects_removed_name_option():
    parser = create_arg_parser(["openplate", "project", "init"])

    with pytest.raises(SystemExit):
        parser.parse_args(["project", "init", "-n", "old-template#main"])


def test_create_arg_parser_rejects_removed_folder_option():
    parser = create_arg_parser(["openplate", "project", "init"])

    with pytest.raises(SystemExit):
        parser.parse_args(["project", "init", "-f", "templates/example"])


def test_resolve_project_init_source_reference_requires_ref_without_override():
    result = create_arg_parser(["openplate", "project", "init"]).parse_args([
        "project", "init", "https://example.com/template.git"
    ])

    with pytest.raises(ValueError, match="Must specify a tag or branch name"):
        resolve_project_init_source_reference(result)


def test_async_main_warns_when_using_legacy_r_flag(monkeypatch, capsys, tmp_path):
    async def fake_run(*_args, **_kwargs):
        return None

    monkeypatch.setattr("openplate.commands.project_init.run", fake_run)

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-folder",
        str(tmp_path),
        "init",
        "-r",
        "https://example.com/template.git#main",
        "--allow-template-commands",
    ]

    asyncio.run(async_main(args))

    captured = capsys.readouterr()
    assert "deprecated" in captured.err


def test_git_template_reference_parses_query_path_and_ref():
    reference = GitTemplateReference.parse("https://github.com/my-org/template-catalog.git?path=python/api#v1")

    assert reference.repo_location == "https://github.com/my-org/template-catalog.git"
    assert reference.template_path == "python/api"
    assert reference.branch_name == "v1"


def test_git_template_reference_rejects_invalid_template_path():
    with pytest.raises(ValueError, match="outside of root"):
        GitTemplateReference.parse("https://github.com/my-org/template-catalog.git?path=../outside#v1")


def test_git_template_reference_rejects_absolute_template_path():
    with pytest.raises(ValueError, match="relative to the repository root"):
        GitTemplateReference.parse("file:///C:/repos/template-catalog?path=C:/outside#main")


def test_url_template_source_uses_selected_subfolder(tmp_path):
    repo_path = tmp_path / "template-catalog"
    (repo_path / "templates" / "api").mkdir(parents=True)
    (repo_path / "templates" / "api" / "openplate.template.yaml").write_text("version: 1\n", encoding="utf-8")
    _create_git_repo(repo_path)

    source_url = f"{repo_path.as_uri()}?path=templates/api#main"
    with UrlTemplateSource(open_plate_settings.defaultSettings, source_url) as source:
        assert Path(source.folder_path()).name == "api"
        assert (Path(source.folder_path()) / "openplate.template.yaml").exists()