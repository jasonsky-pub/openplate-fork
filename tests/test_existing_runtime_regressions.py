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
import subprocess
from pathlib import Path
import yaml

import pytest

from openplate import project_config_resolver
from openplate.__main__ import async_main
from openplate.cfg import template_config
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings, defaultSettings
from openplate.cfg.project_config import ProjectConfig, ProjectTemplateConfig, project_config_file_name
from openplate.cfg.template_config import TemplateConfig, TemplateConfigParameter
from openplate.commands.project_init import InitOptions
from openplate.commands.project_update import UpdateOptions
from openplate.commands import project_init, project_update
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


def _write_template_repo(repo_path: Path, template_yaml: str):
    repo_path.mkdir(parents=True, exist_ok=True)
    (repo_path / "openplate.template.yaml").write_text(template_yaml, encoding="utf-8")
    (repo_path / "README.md").write_text("template\n", encoding="utf-8")
    _create_git_repo(repo_path)
    return f"{repo_path.as_uri()}#main"


def _build_template_config(parameter: TemplateConfigParameter) -> TemplateConfig:
    return TemplateConfig(
        parameters=[parameter],
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
    )


def test_resolve_keeps_existing_parameter_without_processing_default(tmp_path):
    config_project_template = ProjectTemplateConfig(
        "https://example.com/template#main",
        None,
        None,
        ".",
        None,
        {"service_name": "existing"},
        [],
        None,
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
    config_template = _build_template_config(
        TemplateConfigParameter("service_name", "Service Name", "{{", False, None)
    )

    changed = project_config_resolver.resolve(
        defaultSettings,
        OpenPlateRuntimeSettings(False, False, True, True),
        config_template,
        config_project,
        config_project_template,
        str(tmp_path),
        str(tmp_path),
        False,
    )

    assert changed is True
    assert config_project_template.parameters["service_name"] == "existing"


def test_project_init_prints_status_before_project_config_load_failure(tmp_path, monkeypatch, capsys):
    def fail_from_file(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(project_init.project_config, "from_file", fail_from_file)

    options = InitOptions(
        ProjectTemplateConfig("https://example.com/template#main", None, None, ".", None, {}, [], None),
        str(tmp_path),
        False,
        False,
        False,
        None,
    )

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(project_init.run(defaultSettings, OpenPlateRuntimeSettings(False, False, True, True), options))

    assert "Running init on folder:" in capsys.readouterr().out


def test_project_update_prints_status_before_project_config_load_failure(tmp_path, monkeypatch, capsys):
    def fail_from_file(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(project_update.project_config, "from_file", fail_from_file)

    options = UpdateOptions(
        str(tmp_path),
        False,
        False,
        False,
        None,
    )

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(project_update.run(defaultSettings, OpenPlateRuntimeSettings(False, False, True, True), options))

    assert "Running update on folder:" in capsys.readouterr().out


def test_runtime_init_reopens_same_source_for_recursive_siblings(tmp_path, monkeypatch, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
require_sibling_templates:
  - template_url: "{{ template_src_url }}"
    dest_folder: "api"
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    async def fake_walk_init(*_args, **_kwargs):
        return []

    monkeypatch.setattr("openplate.walk.source_template_recursive_walk.walk_init", fake_walk_init)

    enter_count = 0
    original_enter = UrlTemplateSource.__enter__

    def counting_enter(self):
        nonlocal enter_count
        enter_count += 1
        return original_enter(self)

    monkeypatch.setattr(UrlTemplateSource, "__enter__", counting_enter)

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        source_url,
        "--dest-folder",
        ".",
    ]

    asyncio.run(async_main(args))

    capsys.readouterr()
    assert enter_count == 2


def test_project_config_does_not_persist_raw_prompt_identity_fields(tmp_path):
    config = ProjectConfig(
        [
            ProjectTemplateConfig(
                "https://example.com/template#main",
                None,
                None,
                ".",
                None,
                {},
                [],
                False,
                "{{ template_src_url }}",
                "services/{{ project_folder_name }}",
                "{{ include_api }}",
            )
        ],
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

    config_path = tmp_path / project_config_file_name
    project_init.project_config.to_file(config, str(config_path))

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    template_data = data["templates"][0]

    assert "raw_template_reference" not in template_data
    assert "raw_dest_folder" not in template_data
    assert "raw_condition" not in template_data


def test_init_overwrite_reuses_existing_template_and_skips_init_commands(tmp_path, monkeypatch):
        repo_path = tmp_path / "template"
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "openplate.template.yaml").write_text(
                "\n".join([
                        "ignore_paths:",
                        "  - '^openplate\\\\.template\\\\.yaml$'",
                        "replacement_paths:",
                        "  - 'scaffold/.*'",
                        "readonly_paths:",
                        "  - 'scaffold/app/managed/.*'",
                        "parameters:",
                        "  - name: service_name",
                        "    description: Service name",
                        "    default: starter-service",
                        "init_commands:",
                        "  - command: >-",
                        "      python -c \"from pathlib import Path; Path('hooks').mkdir(exist_ok=True); Path('hooks/init-command.txt').write_text('init command ran\\n', encoding='utf-8')\"",
                        "",
                ]),
                encoding="utf-8",
        )
        (repo_path / "README.md").write_text("template\n", encoding="utf-8")
        (repo_path / "scaffold" / "app" / "managed").mkdir(parents=True, exist_ok=True)
        (repo_path / "scaffold" / "app" / "managed" / "service.txt").write_text("service={{ service_name }}\n", encoding="utf-8")
        (repo_path / "scaffold" / "app" / "docs").mkdir(parents=True, exist_ok=True)
        (repo_path / "scaffold" / "app" / "docs" / "overview.md").write_text("service={{ service_name }}\n", encoding="utf-8")
        _create_git_repo(repo_path)
        source_url = f"{repo_path.as_uri()}#main"

        project_path = tmp_path / "project"
        project_path.mkdir()

        first_args = [
                "openplate",
                "-c",
                str(tmp_path / "missing-config.yaml"),
                "project",
                "--project-root",
                str(project_path),
                "init",
                source_url,
                "--dest-folder",
                "app",
                "--allow-template-commands",
        ]

        initial_answers = iter(["", ""])
        monkeypatch.setattr("builtins.input", lambda _prompt: next(initial_answers))

        asyncio.run(async_main(first_args))

        managed_path = project_path / "scaffold" / "app" / "managed" / "service.txt"
        docs_path = project_path / "scaffold" / "app" / "docs" / "overview.md"
        hook_path = project_path / "hooks" / "init-command.txt"
        managed_path.chmod(0o666)
        docs_path.write_text("drifted\n", encoding="utf-8")
        hook_path.unlink()

        second_args = [
                "openplate",
                "-c",
                str(tmp_path / "missing-config.yaml"),
                "project",
                "--project-root",
                str(project_path),
                "init",
                source_url,
                "--dest-folder",
                "app",
                "--overwrite",
        ]

        monkeypatch.setattr("builtins.input", lambda _prompt: pytest.fail("init --overwrite unexpectedly prompted"))

        asyncio.run(async_main(second_args))

        config = yaml.safe_load((project_path / project_config_file_name).read_text(encoding="utf-8"))

        assert managed_path.read_text(encoding="utf-8") == "service=starter-service\n"
        assert docs_path.read_text(encoding="utf-8") == "service=starter-service\n"
        assert not hook_path.exists()
        assert len(config["templates"]) == 1


def test_init_rejects_rerun_without_overwrite_for_existing_tracked_template(tmp_path, monkeypatch):
        repo_path = tmp_path / "template"
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "openplate.template.yaml").write_text(
            "\n".join([
                "ignore_paths:",
                "  - '^openplate\\\\.template\\\\.yaml$'",
                "replacement_paths:",
                "  - 'scaffold/.*'",
                "parameters:",
                "  - name: service_name",
                "    description: Service name",
                "    default: starter-service",
                "init_commands:",
                "  - command: >-",
                "      python -c \"from pathlib import Path; Path('hooks').mkdir(exist_ok=True); Path('hooks/init-command.txt').write_text('init command ran\\n', encoding='utf-8')\"",
                "",
            ]),
            encoding="utf-8",
        )
        (repo_path / "README.md").write_text("template\n", encoding="utf-8")
        (repo_path / "scaffold" / "app" / "managed").mkdir(parents=True, exist_ok=True)
        (repo_path / "scaffold" / "app" / "managed" / "service.txt").write_text("service={{ service_name }}\n", encoding="utf-8")
        (repo_path / "scaffold" / "app" / "docs").mkdir(parents=True, exist_ok=True)
        (repo_path / "scaffold" / "app" / "docs" / "overview.md").write_text("service={{ service_name }}\n", encoding="utf-8")
        _create_git_repo(repo_path)
        source_url = f"{repo_path.as_uri()}#main"

        project_path = tmp_path / "project"
        project_path.mkdir()

        first_args = [
            "openplate",
            "-c",
            str(tmp_path / "missing-config.yaml"),
            "project",
            "--project-root",
            str(project_path),
            "init",
            source_url,
            "--dest-folder",
            "app",
            "--allow-template-commands",
        ]

        initial_answers = iter(["", ""])
        monkeypatch.setattr("builtins.input", lambda _prompt: next(initial_answers))

        asyncio.run(async_main(first_args))

        managed_path = project_path / "scaffold" / "app" / "managed" / "service.txt"
        docs_path = project_path / "scaffold" / "app" / "docs" / "overview.md"
        managed_path.unlink()
        docs_path.unlink()

        second_args = [
            "openplate",
            "-c",
            str(tmp_path / "missing-config.yaml"),
            "project",
            "--project-root",
            str(project_path),
            "init",
            source_url,
            "--dest-folder",
            "app",
        ]

        monkeypatch.setattr("builtins.input", lambda _prompt: pytest.fail("rerun without overwrite unexpectedly prompted"))

        with pytest.raises(SystemExit, match="Template already exists at destination folder"):
            asyncio.run(async_main(second_args))

        config = yaml.safe_load((project_path / project_config_file_name).read_text(encoding="utf-8"))

        assert not managed_path.exists()
        assert not docs_path.exists()
        assert len(config["templates"]) == 1


def test_template_config_accepts_legacy_conditional_file_field():
    config = template_config.deserialize_project_config(
        {
            "parameters": [],
            "conditional": [
                {
                    "file": "src/demo/aws-lambda-tools-defaults.json",
                    "condition": "{{ include_lambda }}",
                }
            ],
        }
    )

    assert config.conditional is not None
    assert len(config.conditional) == 1
    assert config.conditional[0].location == "src/demo/aws-lambda-tools-defaults.json"
    assert config.conditional[0].condition == "{{ include_lambda }}"
