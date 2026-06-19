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
import json
import logging
import subprocess
from io import StringIO
from pathlib import Path

import pytest
import yaml

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
import json
import logging
import subprocess
from io import StringIO
from pathlib import Path

import pytest
import yaml

from openplate.__main__ import async_main
from openplate.cfg import project_config
from openplate.project_template_identity import full_prompt_node_id, short_prompt_node_id
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


def _node_id(template: str, dest_folder: str = ".", full: bool = False):
    full_id = full_prompt_node_id(template, dest_folder)
    if full:
        return full_id
    return short_prompt_node_id(full_id)


def test_project_print_init_json_compact_is_read_only_and_omits_info(tmp_path, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "print-init-json",
        source_url,
    ]

    asyncio.run(async_main(args))

    printed = json.loads(capsys.readouterr().out)
    assert not (project_path / project_config.project_config_file_name).exists()
    assert printed == [
        {
            "node-id": _node_id(source_url, "."),
            "answers": {
                "service_name": None,
            },
        }
    ]


def test_project_print_init_json_verbose_includes_caller_side_sibling_metadata(tmp_path, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
  - name: include_api
    description: Include API
    default: "false"
require_sibling_templates:
  - template_url: "{{ template_src_url }}"
    dest_folder: "services/{{ project_folder_name }}/api"
    condition: "{{ include_api }}"
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "print-init-json",
        source_url,
        "--verbose",
    ]

    asyncio.run(async_main(args))

    printed = json.loads(capsys.readouterr().out)
    root_node = next(node for node in printed if node["info"]["template"] == source_url)
    sibling_node = next(node for node in printed if node["info"]["template"] == "{{ template_src_url }}")

    assert root_node["info"]["require_sibling_templates"] == [
        {
            "template": "{{ template_src_url }}",
            "dest_folder": f"services/{project_path.name}/api",
            "condition": "{{ include_api }}",
        }
    ]
    assert "condition" not in sibling_node["info"]


def test_project_print_init_json_deduplicates_duplicate_discovered_templates(tmp_path, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
require_sibling_templates:
  - template_url: "{{ template_src_url }}"
    dest_folder: "shared"
  - template_url: "{{ template_src_url }}"
    dest_folder: "shared"
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "print-init-json",
        source_url,
    ]

    asyncio.run(async_main(args))

    printed = json.loads(capsys.readouterr().out)
    assert len(printed) == 2
    assert len({node["node-id"] for node in printed}) == 2


def test_project_print_init_json_excludes_hidden_parameters_without_ask_hidden(tmp_path, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
  - name: hidden_name
    description: Hidden Name
    default: secret
    hidden: true
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "print-init-json",
        source_url,
    ]

    asyncio.run(async_main(args))

    printed = json.loads(capsys.readouterr().out)
    assert printed[0]["answers"] == {"service_name": None}


def test_project_print_init_json_includes_hidden_parameters_with_ask_hidden(tmp_path, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
  - name: hidden_name
    description: Hidden Name
    default: secret
    hidden: true
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "--ask-hidden",
        "print-init-json",
        source_url,
        "--verbose",
    ]

    asyncio.run(async_main(args))

    printed = json.loads(capsys.readouterr().out)
    assert printed[0]["answers"]["hidden_name"] is None
    assert printed[0]["info"]["parameters"]["hidden_name"]["hidden"] is True


def test_project_print_init_json_fails_when_sibling_metadata_cannot_be_resolved(tmp_path):
    repo_path = tmp_path / "template"
    sibling_source_url = f"{repo_path.as_uri()}?path=missing#main"
    source_url = _write_template_repo(
        repo_path,
        "\n".join(
            [
                "require_sibling_templates:",
                f"  - template_url: \"{sibling_source_url}\"",
                "    dest_folder: \"broken\"",
            ]
        ),
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "print-init-json",
        source_url,
    ]

    with pytest.raises(RuntimeError, match="Unable to resolve sibling declaration"):
        asyncio.run(async_main(args))


def test_project_print_init_json_reuses_single_source_fetch(tmp_path, monkeypatch, capsys):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
require_sibling_templates:
  - template_url: "{{ template_src_url }}"
    dest_folder: "services/{{ project_folder_name }}/api"
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
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
        "print-init-json",
        source_url,
    ]

    asyncio.run(async_main(args))

    json.loads(capsys.readouterr().out)
    assert enter_count == 1


def test_project_init_accepts_prompts_json_file_with_node_ids(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "service_name": "demo",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

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
        "--prompts-json-file",
        str(prompts_path),
    ]

    asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["service_name"] == "demo"


def test_project_init_accepts_prompts_json_from_stdin(tmp_path, monkeypatch):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()

    monkeypatch.setattr(
        "sys.stdin",
        StringIO(
            json.dumps(
                [
                    {
                        "node-id": _node_id(source_url, "."),
                        "answers": {
                            "service_name": "stdin-demo",
                        },
                    }
                ]
            )
        ),
    )

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
        "--prompts-json-stdin",
    ]

    asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["service_name"] == "stdin-demo"


def test_project_init_accepts_blank_string_prompt_value(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "service_name": "",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

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
        "--prompts-json-file",
        str(prompts_path),
    ]

    asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["service_name"] == ""


def test_project_init_ignores_info_metadata_on_import(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "service_name": "demo",
                    },
                    "info": {
                        "template": "mutated-template",
                        "dest_folder": "mutated-folder",
                        "parameters": {},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

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
        "--prompts-json-file",
        str(prompts_path),
    ]

    asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["service_name"] == "demo"


def test_project_init_rejects_non_array_prompt_document(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(repo_path, "version: 1\n")
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text("{}", encoding="utf-8")

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    with pytest.raises(TypeError, match="Prompt document must be a JSON array"):
        asyncio.run(async_main(args))


def test_project_init_rejects_invalid_answer_value_type(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(repo_path, "version: 1\n")
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "service_name": 123,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    with pytest.raises(TypeError, match="must be a string or null"):
        asyncio.run(async_main(args))


def test_project_init_uses_default_value_when_answer_is_null(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
    default: demo
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "service_name": None,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["service_name"] == "demo"


def test_project_init_fails_when_required_value_remains_unresolved_in_json_mode(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: service_name
    description: Service Name
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "service_name": None,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    with pytest.raises(Exception, match="unresolved parameter"):
        asyncio.run(async_main(args))


def test_project_init_json_mode_ignores_hidden_value_without_ask_hidden(tmp_path, caplog):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: hidden_name
    description: Hidden Name
    default: secret
    hidden: true
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "hidden_name": "override",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    with caplog.at_level(logging.WARNING):
        asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["hidden_name"] == "secret"
    assert any("Ignoring unused supplied prompt parameter" in record.message for record in caplog.records)


def test_project_init_json_mode_uses_hidden_value_with_ask_hidden(tmp_path):
    repo_path = tmp_path / "template"
    source_url = _write_template_repo(
        repo_path,
        """
parameters:
  - name: hidden_name
    description: Hidden Name
    default: secret
    hidden: true
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(source_url, "."),
                    "answers": {
                        "hidden_name": "override",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "--ask-hidden",
        "init",
        source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    assert written_config["templates"][0]["parameters"]["hidden_name"] == "override"


def test_project_init_json_mode_uses_supplied_value_for_existing_sibling_parameter(tmp_path, caplog, monkeypatch):
    child_repo_path = tmp_path / "child-template"
    child_source_url = _write_template_repo(
        child_repo_path,
        """
parameters:
  - name: artifact_name
    description: Artifact Name
""",
    )
    root_repo_path = tmp_path / "root-template"
    root_source_url = _write_template_repo(
        root_repo_path,
        f"""
parameters:
  - name: service_name
    description: Service Name
require_sibling_templates:
  - template_url: "{child_source_url}"
    dest_folder: "child"
    parameters:
      artifact_name: "{{{{ service_name }}}}"
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(root_source_url, "."),
                    "answers": {
                        "service_name": "demo",
                    },
                },
                {
                    "node-id": _node_id(child_source_url, "child"),
                    "answers": {
                        "artifact_name": "override",
                    },
                },
            ]
        ),
        encoding="utf-8",
    )

    async def fake_walk_init(*_args, **_kwargs):
        return []

    async def fake_walk_update(*_args, **_kwargs):
        return None

    monkeypatch.setattr("openplate.walk.source_template_recursive_walk.walk_init", fake_walk_init)
    monkeypatch.setattr("openplate.walk.source_template_recursive_walk.walk_update", fake_walk_update)

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        root_source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    with caplog.at_level(logging.WARNING):
        asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    child_templates = [
        template for template in written_config["templates"]
        if template["src_url"] == child_source_url and template["dest_folder"] == "child"
    ]
    assert len(child_templates) == 1
    assert child_templates[0]["parameters"]["artifact_name"] == "override"


def test_project_init_json_mode_uses_raw_dest_identity_for_dynamic_sibling_dest(tmp_path, caplog, monkeypatch):
    child_repo_path = tmp_path / "child-template"
    child_source_url = _write_template_repo(
        child_repo_path,
        """
parameters:
  - name: artifact_name
    description: Artifact Name
""",
    )
    root_repo_path = tmp_path / "root-template"
    root_source_url = _write_template_repo(
        root_repo_path,
        f"""
parameters:
  - name: service_name
    description: Service Name
require_sibling_templates:
  - template_url: "{child_source_url}"
    dest_folder: "child/{{{{ service_name }}}}"
    parameters:
      artifact_name: "{{{{ service_name }}}}"
""",
    )
    project_path = tmp_path / "project"
    project_path.mkdir()
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text(
        json.dumps(
            [
                {
                    "node-id": _node_id(root_source_url, "."),
                    "answers": {
                        "service_name": "demo",
                    },
                },
                {
                    "node-id": _node_id(child_source_url, "child/{{ service_name }}"),
                    "answers": {
                        "artifact_name": "override",
                    },
                },
            ]
        ),
        encoding="utf-8",
    )

    async def fake_walk_init(*_args, **_kwargs):
        return []

    async def fake_walk_update(*_args, **_kwargs):
        return None

    monkeypatch.setattr("openplate.walk.source_template_recursive_walk.walk_init", fake_walk_init)
    monkeypatch.setattr("openplate.walk.source_template_recursive_walk.walk_update", fake_walk_update)

    args = [
        "openplate",
        "-c",
        str(tmp_path / "missing-config.yaml"),
        "project",
        "--project-root",
        str(project_path),
        "init",
        root_source_url,
        "--prompts-json-file",
        str(prompts_path),
    ]

    with caplog.at_level(logging.WARNING):
        asyncio.run(async_main(args))

    written_config = yaml.safe_load((project_path / project_config.project_config_file_name).read_text(encoding="utf-8"))
    child_templates = [
        template for template in written_config["templates"]
        if template["src_url"] == child_source_url and template["dest_folder"] == "child/demo"
    ]
    assert len(child_templates) == 1
    assert child_templates[0]["parameters"]["artifact_name"] == "override"
    assert "Ignoring supplied prompt template because it was not processed" not in caplog.text

