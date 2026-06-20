import subprocess
from pathlib import Path

import pytest

from openplate import project_config_resolver
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings, defaultSettings
from openplate.cfg.project_config import ProjectConfig, ProjectTemplateConfig
from openplate.cfg.template_config import TemplateConfig
from openplate.project_metadata_resolver import resolve_project_metadata, resolve_template_source_metadata
from openplate.template_processor import compile_template_options


pytestmark = pytest.mark.unit


class _FakeTemplateSource:
    def __init__(self, source_url: str, resolved_ref: str | None = None):
        self._source_url = source_url
        self._resolved_ref = resolved_ref

    def template_url(self):
        return self._source_url

    def resolved_ref(self):
        return self._resolved_ref


def _empty_template_config(requires_last_updater_email: bool = False) -> TemplateConfig:
    return TemplateConfig(
        parameters=[],
        ignore_paths=[],
        replacement_paths=[],
        user_paths=[],
        readonly_paths=[],
        optional_paths=[],
        rename_rules={},
        config_files={},
        override_tag_start=None,
        override_tag_end=None,
        override_statement_start=None,
        override_statement_end=None,
        min_tool_version=None,
        remove_files=None,
        require_sibling_templates=None,
        ignore_inherited_files=None,
        init_commands=None,
        default_dest_folder=".",
        multiplex=[],
        conditional=[],
        requires_last_updater_email=requires_last_updater_email,
    )


def _create_git_repo(repo_path: Path, remote_url: str | None = None):
    repo_path.mkdir(parents=True, exist_ok=True)
    (repo_path / "README.md").write_text("repo\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "OpenPlate Tests"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    if remote_url is not None:
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")


def test_compile_template_options_exposes_project_git_metadata_and_aliases(tmp_path):
    project_root = tmp_path / "project"
    _create_git_repo(project_root, "https://user:pass@github.com/my-org/my-repo.git")

    config_project_template = ProjectTemplateConfig(
        "https://example.com/template.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
    )
    config_project = ProjectConfig(
        [config_project_template],
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        {},
        {},
        None,
    )

    resolve_project_metadata(
        OpenPlateRuntimeSettings(False, False, True, True),
        config_project,
        str(project_root),
    )

    options = compile_template_options(
        _empty_template_config(),
        config_project,
        config_project_template,
        str(tmp_path),
        str(project_root),
        True,
    )

    assert options["project_git_mode"] is True
    assert options["project_folder_name"] == "my-repo"
    assert options["project_src_url"] == "https://github.com/my-org/my-repo.git"
    assert options["project_git_repo_url"] == "https://github.com/my-org/my-repo.git"
    assert options["project_git_https_repo_url"] == "https://github.com/my-org/my-repo.git"
    assert options["project_git_ssh_repo_url"] == "git@github.com:my-org/my-repo.git"
    assert options["project_git_repo_org"] == "my-org"
    assert options["project_git_repo_name"] == "my-repo"
    assert options["project_repo_org"] == "my-org"
    assert options["project_repo_name"] == "my-repo"


def test_compile_template_options_falls_back_to_git_root_folder_name_without_remote(tmp_path):
    project_root = tmp_path / "project"
    _create_git_repo(project_root)

    config_project_template = ProjectTemplateConfig(
        "https://example.com/template.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
    )
    config_project = ProjectConfig(
        [config_project_template],
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        {},
        {},
        None,
    )

    resolve_project_metadata(
        OpenPlateRuntimeSettings(False, False, True, True),
        config_project,
        str(project_root),
    )

    options = compile_template_options(
        _empty_template_config(),
        config_project,
        config_project_template,
        str(tmp_path),
        str(project_root),
        True,
    )

    assert options["project_git_mode"] is True
    assert options["project_folder_name"] == "project"
    assert options["project_src_url"] == ""
    assert options["project_git_repo_name"] == ""


def test_compile_template_options_exposes_template_git_url_variants(tmp_path):
    config_project_template = ProjectTemplateConfig(
        "https://user:pass@github.com/my-org/template-catalog.git?path=python/api#v1",
        None,
        None,
        "services/api",
        None,
        {},
        [],
        False,
    )
    config_project = ProjectConfig([], None, None, None, None, None, None, None, None, None, None, {}, {}, None)

    resolve_template_source_metadata(
        config_project_template,
        _FakeTemplateSource(config_project_template.src_url, "v1"),
    )

    options = compile_template_options(
        _empty_template_config(),
        config_project,
        config_project_template,
        str(tmp_path),
        str(tmp_path),
        True,
    )

    assert options["template_src_url"] == "https://github.com/my-org/template-catalog.git?path=python/api#v1"
    assert options["template_git_https_src_url"] == "https://github.com/my-org/template-catalog.git?path=python/api#v1"
    assert options["template_git_ssh_src_url"] == "git@github.com:my-org/template-catalog.git?path=python/api#v1"
    assert options["template_git_repo_url"] == "https://github.com/my-org/template-catalog.git"
    assert options["template_git_https_repo_url"] == "https://github.com/my-org/template-catalog.git"
    assert options["template_git_ssh_repo_url"] == "git@github.com:my-org/template-catalog.git"
    assert options["template_git_repo_org"] == "my-org"
    assert options["template_git_repo_name"] == "template-catalog"
    assert options["template_git_repo_path"] == "python/api"
    assert options["template_git_repo_ref"] == "v1"


def test_template_git_repo_ref_falls_back_to_resolved_head_ref_without_changing_src_url(tmp_path):
    config_project_template = ProjectTemplateConfig(
        "https://github.com/my-org/template-catalog.git?path=python/api",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
    )
    config_project = ProjectConfig([], None, None, None, None, None, None, None, None, None, None, {}, {}, None)

    resolve_template_source_metadata(
        config_project_template,
        _FakeTemplateSource(config_project_template.src_url, "release-1"),
    )

    options = compile_template_options(
        _empty_template_config(),
        config_project,
        config_project_template,
        str(tmp_path),
        str(tmp_path),
        True,
    )

    assert options["template_src_url"] == "https://github.com/my-org/template-catalog.git?path=python/api"
    assert options["template_git_repo_ref"] == "release-1"


def test_non_git_template_source_leaves_template_git_metadata_empty(tmp_path):
    config_project_template = ProjectTemplateConfig(
        "file:///c:/templates/python-api#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
    )
    config_project = ProjectConfig([], None, None, None, None, None, None, None, None, None, None, {}, {}, None)

    resolve_template_source_metadata(
        config_project_template,
        _FakeTemplateSource(config_project_template.src_url, "main"),
    )

    options = compile_template_options(
        _empty_template_config(),
        config_project,
        config_project_template,
        str(tmp_path),
        str(tmp_path),
        True,
    )

    assert options["template_src_url"] == "file:///c:/templates/python-api#main"
    assert options["template_git_ssh_src_url"] == ""
    assert options["template_git_https_src_url"] == ""
    assert options["template_git_repo_url"] == ""
    assert options["template_git_ssh_repo_url"] == ""
    assert options["template_git_https_repo_url"] == ""
    assert options["template_git_repo_org"] == ""
    assert options["template_git_repo_name"] == ""
    assert options["template_git_repo_path"] == ""
    assert options["template_git_repo_ref"] == ""


def test_compile_template_options_omits_last_updater_email_for_non_requiring_template(tmp_path):
    config_project_template = ProjectTemplateConfig(
        "https://example.com/template.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
    )
    config_project = ProjectConfig([], None, None, None, None, None, None, None, None, None, None, {}, {}, "tests@example.com")

    options = compile_template_options(
        _empty_template_config(),
        config_project,
        config_project_template,
        str(tmp_path),
        str(tmp_path),
        True,
    )

    assert options["last_updater_email"] == ""


def test_compile_template_options_exposes_last_updater_email_for_requiring_template(tmp_path):
    config_project_template = ProjectTemplateConfig(
        "https://example.com/template.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
        requires_last_updater_email=True,
    )
    config_project = ProjectConfig([], None, None, None, None, None, None, None, None, None, None, {}, {}, "tests@example.com")

    options = compile_template_options(
        _empty_template_config(requires_last_updater_email=True),
        config_project,
        config_project_template,
        str(tmp_path),
        str(tmp_path),
        True,
    )

    assert options["last_updater_email"] == "tests@example.com"


def test_project_config_resolver_requires_last_updater_email_consent_in_automation(tmp_path):
    project_root = tmp_path / "project"
    _create_git_repo(project_root)

    config_project_template = ProjectTemplateConfig(
        "https://example.com/template.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
        requires_last_updater_email=True,
    )
    config_project = ProjectConfig(
        [config_project_template],
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        {},
        {},
        None,
    )

    with pytest.raises(RuntimeError, match="last_updater_email but it is not allowed"):
        project_config_resolver.resolve(
            defaultSettings,
            OpenPlateRuntimeSettings(False, False, True, True, False, False, True, True),
            _empty_template_config(requires_last_updater_email=True),
            config_project,
            config_project_template,
            str(project_root),
            str(project_root),
            False,
        )


def test_project_config_resolver_prompts_once_for_requiring_templates(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    _create_git_repo(project_root)

    template_one = ProjectTemplateConfig(
        "https://example.com/template-one.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
        requires_last_updater_email=True,
    )
    template_two = ProjectTemplateConfig(
        "https://example.com/template-two.git#main",
        None,
        None,
        "services/api",
        None,
        {},
        [],
        False,
        requires_last_updater_email=True,
    )
    config_project = ProjectConfig(
        [template_one, template_two],
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        {},
        {},
        None,
    )

    prompt_calls = []
    answers = iter(["yes"])

    def _answer(_prompt):
        prompt_calls.append(True)
        return next(answers)

    monkeypatch.setattr("builtins.input", _answer)

    runtime_settings = OpenPlateRuntimeSettings(False, False, True, False, False, False, True, True)

    project_config_resolver.resolve(
        defaultSettings,
        runtime_settings,
        _empty_template_config(requires_last_updater_email=True),
        config_project,
        template_one,
        str(project_root),
        str(project_root),
        False,
    )
    project_config_resolver.resolve(
        defaultSettings,
        runtime_settings,
        _empty_template_config(requires_last_updater_email=True),
        config_project,
        template_two,
        str(project_root),
        str(project_root),
        False,
    )

    assert len(prompt_calls) == 1
    assert config_project.last_updater_email == "tests@example.com"


def test_project_config_resolver_does_not_prompt_when_resolution_is_disabled(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    _create_git_repo(project_root)

    config_project_template = ProjectTemplateConfig(
        "https://example.com/template.git#main",
        None,
        None,
        ".",
        None,
        {},
        [],
        False,
        requires_last_updater_email=True,
    )
    config_project = ProjectConfig(
        [config_project_template],
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        {},
        {},
        "persisted@example.com",
    )

    monkeypatch.setattr("builtins.input", lambda _prompt: pytest.fail("unexpected last_updater_email prompt"))

    project_config_resolver.resolve(
        defaultSettings,
        OpenPlateRuntimeSettings(False, False, True, False),
        _empty_template_config(requires_last_updater_email=True),
        config_project,
        config_project_template,
        str(project_root),
        str(project_root),
        True,
    )

    assert config_project.last_updater_email == "persisted@example.com"