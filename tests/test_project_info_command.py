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

import pytest
import yaml

from openplate.__main__ import async_main
from openplate.cfg import open_plate_settings, project_config, template_config
from openplate.commands import project_init
from openplate.commands.project_init import InitOptions


pytestmark = pytest.mark.unit


def _create_git_repo(repo_path: Path):
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "OpenPlate Tests"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")


def _write_template_repo(repo_path: Path, template_text: str) -> str:
    repo_path.mkdir(parents=True, exist_ok=True)
    (repo_path / "openplate.template.yaml").write_text(template_text, encoding="utf-8")
    (repo_path / "README.md").write_text("template\n", encoding="utf-8")
    _create_git_repo(repo_path)
    return f"{repo_path.as_uri()}#main"


def _runtime_settings(*, ask_hidden: bool = False):
    return open_plate_settings.OpenPlateRuntimeSettings(
        False,
        ask_hidden,
        False,
        False,
        False,
        False,
        True,
        True,
    )


def test_project_init_records_requested_provenance(tmp_path, monkeypatch):
    source_url = _write_template_repo(
        tmp_path / "template",
        "parameters:\n  - name: service_name\n    description: Service Name\n    default: demo\n",
    )
    destination = tmp_path / "project"
    destination.mkdir()
    monkeypatch.setattr("builtins.input", lambda _prompt: "")

    options = InitOptions(
        project_config.ProjectTemplateConfig(source_url, None, None, ".", None, {}, [], False),
        str(destination),
        False,
        False,
    )

    asyncio.run(project_init.run(open_plate_settings.defaultSettings, _runtime_settings(), options))

    written = yaml.safe_load((destination / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written["templates"][0]["provenance"] == project_config.TEMPLATE_PROVENANCE_REQUESTED


def test_project_init_overwrite_promotes_inherited_provenance(tmp_path, monkeypatch):
    source_url = _write_template_repo(
        tmp_path / "template",
        "parameters:\n  - name: service_name\n    description: Service Name\n    default: demo\n",
    )
    destination = tmp_path / "project"
    destination.mkdir()
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    (destination / project_config.project_config_file_name).write_text(
        yaml.safe_dump(
            {
                "templates": [
                    {
                        "src_url": source_url,
                        "dest_folder": ".",
                        "parameters": {},
                        "template_ignore_paths": [],
                        "no_cache": False,
                        "provenance": project_config.TEMPLATE_PROVENANCE_INHERITED,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    options = InitOptions(
        project_config.ProjectTemplateConfig(source_url, None, None, ".", None, {}, [], False),
        str(destination),
        True,
        False,
    )

    asyncio.run(project_init.run(open_plate_settings.defaultSettings, _runtime_settings(), options))

    written = yaml.safe_load((destination / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written["templates"][0]["provenance"] == project_config.TEMPLATE_PROVENANCE_REQUESTED


def test_recursive_sibling_add_records_inherited_provenance(tmp_path, monkeypatch):
    sibling_source_url = _write_template_repo(
        tmp_path / "sibling-template",
        "\n".join([
            "ignore_paths:",
            "  - '^openplate\\.template\\.yaml$'",
            "  - '^README\\.md$'",
            "parameters:",
            "  - name: sibling_name",
            "    description: Sibling Name",
            "    default: worker",
        ]) + "\n",
    )
    root_source_url = _write_template_repo(
        tmp_path / "root-template",
        "\n".join([
            "ignore_paths:",
            "  - '^openplate\\.template\\.yaml$'",
            "  - '^README\\.md$'",
            "parameters:",
            "  - name: include_worker",
            "    description: Include Worker",
            "    default: \"true\"",
            "require_sibling_templates:",
            f"  - template_url: \"{sibling_source_url}\"",
            "    dest_folder: worker",
        ]) + "\n",
    )

    destination = tmp_path / "project"
    destination.mkdir()
    monkeypatch.setattr("builtins.input", lambda _prompt: "")

    options = InitOptions(
        project_config.ProjectTemplateConfig(root_source_url, None, None, ".", None, {}, [], False),
        str(destination),
        False,
        False,
    )

    asyncio.run(project_init.run(open_plate_settings.defaultSettings, _runtime_settings(), options))

    written = yaml.safe_load((destination / project_config.project_config_file_name).read_text(encoding="utf-8"))
    templates_by_dest = {entry["dest_folder"]: entry for entry in written["templates"]}
    assert templates_by_dest["."]["provenance"] == project_config.TEMPLATE_PROVENANCE_REQUESTED
    assert templates_by_dest["worker"]["provenance"] == project_config.TEMPLATE_PROVENANCE_INHERITED


def test_info_offline_prints_persisted_project_data(tmp_path, capsys):
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / project_config.project_config_file_name).write_text(
        yaml.safe_dump(
            {
                "templates": [
                    {
                        "src_url": "https://example.com/template.git#main",
                        "dest_folder": "services/api",
                        "version": "v1",
                        "parameters": {
                            "service_name": "saved-name",
                        },
                        "template_ignore_paths": [],
                        "no_cache": False,
                        "provenance": project_config.TEMPLATE_PROVENANCE_REQUESTED,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "info",
        "--project-root",
        str(project_path),
        "--offline",
    ]

    asyncio.run(async_main(args))

    printed = capsys.readouterr().out
    assert "Template: https://example.com/template.git#main" in printed
    assert "Destination: services/api" in printed
    assert "Provenance: requested" in printed
    assert "Version: v1" in printed
    assert "Saved Parameters:" in printed
    assert "service_name: saved-name" in printed


def test_info_resolved_prints_prompt_metadata(tmp_path, capsys):
    source_url = _write_template_repo(
        tmp_path / "template",
        "\n".join([
            "parameters:",
            "  - name: service_name",
            "    description: Service Name",
            "    default: default-name",
            "  - name: deployment",
            "    description: Deployment",
            "    default: api",
            "    choices:",
            "      - api",
            "      - worker",
            "  - name: hidden_name",
            "    description: Hidden Name",
            "    default: secret",
            "    hidden: true",
        ]) + "\n",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / project_config.project_config_file_name).write_text(
        yaml.safe_dump(
            {
                "templates": [
                    {
                        "src_url": source_url,
                        "dest_folder": ".",
                        "version": "v1",
                        "parameters": {
                            "service_name": "existing-name",
                        },
                        "template_ignore_paths": [],
                        "no_cache": False,
                        "provenance": project_config.TEMPLATE_PROVENANCE_REQUESTED,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "info",
        "--project-root",
        str(project_path),
    ]

    asyncio.run(async_main(args))

    printed = capsys.readouterr().out
    assert f"Template: {source_url}" in printed
    assert "Destination: ." in printed
    assert "Provenance: requested" in printed
    assert "service_name: existing-name" in printed
    assert "Description: Service Name" in printed
    assert "Default: default-name" in printed
    assert "Existing: existing-name" in printed
    assert "deployment: api" in printed
    assert "Choices: api, worker" in printed
    assert "hidden_name" not in printed


def test_info_show_hidden_includes_hidden_parameters(tmp_path, capsys):
    source_url = _write_template_repo(
        tmp_path / "template",
        "\n".join([
            "parameters:",
            "  - name: visible_name",
            "    description: Visible Name",
            "    default: public",
            "  - name: hidden_name",
            "    description: Hidden Name",
            "    default: secret",
            "    hidden: true",
        ]) + "\n",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / project_config.project_config_file_name).write_text(
        yaml.safe_dump(
            {
                "templates": [
                    {
                        "src_url": source_url,
                        "dest_folder": ".",
                        "parameters": {},
                        "template_ignore_paths": [],
                        "no_cache": False,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "info",
        "--project-root",
        str(project_path),
        "--show-hidden",
    ]

    asyncio.run(async_main(args))

    printed = capsys.readouterr().out
    assert "visible_name: public" in printed
    assert "hidden_name: secret" in printed


def test_info_offline_rejects_show_hidden(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / project_config.project_config_file_name).write_text("templates: []\n", encoding="utf-8")

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "info",
        "--project-root",
        str(project_path),
        "--offline",
        "--show-hidden",
    ]

    with pytest.raises(ValueError, match="show-hidden"):
        asyncio.run(async_main(args))


def test_info_resolved_fails_when_template_cannot_be_inspected(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()
    missing_source_url = f"{(tmp_path / 'missing-template').as_uri()}#main"
    (project_path / project_config.project_config_file_name).write_text(
        yaml.safe_dump(
            {
                "templates": [
                    {
                        "src_url": missing_source_url,
                        "dest_folder": ".",
                        "parameters": {},
                        "template_ignore_paths": [],
                        "no_cache": False,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "info",
        "--project-root",
        str(project_path),
    ]

    with pytest.raises(RuntimeError, match="Unable to fully inspect template"):
        asyncio.run(async_main(args))