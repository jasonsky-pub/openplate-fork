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
from io import StringIO
from pathlib import Path

import pytest

from openplate.__main__ import async_main, create_arg_parser, load_prompt_document, resolve_project_init_source_reference
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


def test_create_arg_parser_accepts_top_level_init_with_shared_project_options():
    args = ["openplate", "init", "--project-folder", "workspace", "--ask-hidden", "https://example.com/template.git#main"]
    parser = create_arg_parser(args)

    result = parser.parse_args(args[1:])

    assert result.command == "project-init"
    assert result.project_folder == "workspace"
    assert result.ask_hidden is True
    assert result.source == "https://example.com/template.git#main"


def test_create_arg_parser_accepts_top_level_update_with_shared_project_options():
    args = ["openplate", "update", "--project-folder", "workspace", "--ask-again", "--update-full"]
    parser = create_arg_parser(args)

    result = parser.parse_args(args[1:])

    assert result.command == "project-update"
    assert result.project_folder == "workspace"
    assert result.ask_again is True
    assert result.update_full is True


def test_create_arg_parser_accepts_legacy_project_update_with_shared_project_options():
    args = ["openplate", "project", "--project-folder", "workspace", "update", "--update-full"]
    parser = create_arg_parser(args)

    result = parser.parse_args(args[1:])

    assert result.command == "project-update"
    assert result.project_folder == "workspace"
    assert result.update_full is True


def test_create_arg_parser_top_level_help_hides_project_command():
    parser = create_arg_parser(["openplate", "--help"])

    help_text = parser.format_help()

    assert "{config,init,update}" in help_text
    assert "{config,init,update,project}" not in help_text
    assert "==SUPPRESS==" not in help_text


def test_create_arg_parser_accepts_prompts_json_input_flags_for_top_level_init():
    args = ["openplate", "init", "https://example.com/template.git#main", "--prompts-json-stdin"]
    parser = create_arg_parser(args)

    result = parser.parse_args(args[1:])

    assert result.command == "project-init"
    assert result.prompts_json_file is None
    assert result.prompts_json_stdin is True


def test_create_arg_parser_accepts_print_init_json_command():
    args = ["openplate", "project", "print-init-json", "https://example.com/template.git#main", "--verbose"]
    parser = create_arg_parser(args)

    result = parser.parse_args(args[1:])

    assert result.command == "project-print-init-json"
    assert result.source == "https://example.com/template.git#main"
    assert result.verbose is True


def test_resolve_project_init_source_reference_rejects_conflicting_inputs():
    result = create_arg_parser(["openplate", "project", "init"]).parse_args([
        "project", "init", "https://example.com/template.git#main", "-r", "https://example.com/other.git#main"
    ])

    with pytest.raises(ValueError, match="Specify exactly one template source URL"):
        resolve_project_init_source_reference(result)


def test_load_prompt_document_rejects_multiple_input_sources():
    result = create_arg_parser(["openplate", "project", "init"]).parse_args([
        "project", "init", "https://example.com/template.git#main", "--prompts-json-file", "prompts.json", "--prompts-json-stdin"
    ])

    with pytest.raises(ValueError, match="Specify only one prompts JSON input source"):
        load_prompt_document(result)


def test_create_arg_parser_rejects_removed_update_prompt_json_flags():
    parser = create_arg_parser(["openplate", "project", "update"])

    with pytest.raises(SystemExit):
        parser.parse_args(["project", "update", "--prompts-json-file", "prompts.json"])


def test_create_arg_parser_rejects_removed_init_print_flag():
    parser = create_arg_parser(["openplate", "project", "init"])

    with pytest.raises(SystemExit):
        parser.parse_args(["project", "init", "https://example.com/template.git#main", "--print-prompts-json"])


def test_load_prompt_document_reads_json_from_stdin(monkeypatch):
    result = create_arg_parser(["openplate", "project", "init"]).parse_args([
        "project", "init", "https://example.com/template.git#main", "--prompts-json-stdin"
    ])
    monkeypatch.setattr("sys.stdin", StringIO("[]"))

    document = load_prompt_document(result)

    assert document is not None
    assert document.templates == []


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


def test_async_main_passes_prompt_document_to_project_init(monkeypatch, tmp_path):
    captured_options = {}

    async def fake_run(_settings, _runtime_settings, options):
        captured_options["prompt_document"] = options.prompt_document

    monkeypatch.setattr("openplate.commands.project_init.run", fake_run)

    prompts_json = tmp_path / "prompts.json"
    prompts_json.write_text("[]", encoding="utf-8")

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-folder",
        str(tmp_path),
        "init",
        "https://example.com/template.git#main",
        "--prompts-json-file",
        str(prompts_json),
    ]

    asyncio.run(async_main(args))

    assert captured_options["prompt_document"] is not None
    assert captured_options["prompt_document"].templates == []


def test_async_main_dispatches_print_init_json(monkeypatch, tmp_path):
    captured_options = {}

    async def fake_print(_settings, _runtime_settings, template, destination, verbose):
        captured_options["template"] = template
        captured_options["destination"] = destination
        captured_options["verbose"] = verbose

    monkeypatch.setattr("openplate.commands.project_init.print_prompt_document", fake_print)

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-folder",
        str(tmp_path),
        "print-init-json",
        "https://example.com/template.git#main",
        "--verbose",
    ]

    asyncio.run(async_main(args))

    assert captured_options["template"].src_url == "https://example.com/template.git#main"
    assert captured_options["destination"] == str(tmp_path.resolve())
    assert captured_options["verbose"] is True


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


def test_documentation_uses_top_level_init_and_update_examples():
    repo_root = Path(__file__).resolve().parents[1]
    commands_text = (repo_root / "docs" / "commands.md").read_text(encoding="utf-8")
    readme_text = (repo_root / "readme.md").read_text(encoding="utf-8")

    assert "openplate init https://github.com/my-org/ot-template.git#v1" in commands_text
    assert "openplate update" in commands_text
    assert "openplate project init https://github.com/my-org/ot-template.git#v1" not in commands_text
    assert "openplate project update" not in commands_text

    assert 'openplate init "https://github.com/my-org/ot-template.git#v1"' in readme_text
    assert "openplate update" in readme_text
    assert "openplate project init " not in readme_text