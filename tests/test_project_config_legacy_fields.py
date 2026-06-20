import subprocess
from pathlib import Path

import pytest
import yaml

from openplate.__main__ import create_arg_parser
from openplate.cfg import open_plate_settings, project_config
from openplate.cfg.project_config import ProjectConfig, ProjectTemplateConfig, project_config_file_name


pytestmark = pytest.mark.unit


def test_project_config_write_omits_runtime_metadata_fields(tmp_path):
    config = ProjectConfig(
        [
            ProjectTemplateConfig(
                "https://example.com/template.git#main",
                None,
                None,
                ".",
                None,
                {},
                [],
                False,
            )
        ],
        None,
        None,
        None,
        "workspace",
        "https://github.com/my-org/my-repo.git",
        "my-org",
        "my-repo",
        None,
        None,
        None,
        {},
        {},
        "tests@example.com",
    )

    config_path = tmp_path / project_config_file_name
    project_config.to_file(config, str(config_path))

    written = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "project_folder_name" not in written
    assert "project_src_url" not in written
    assert "project_repo_org" not in written
    assert "project_repo_name" not in written
    assert "last_updater_email" not in written


def test_project_config_load_ignores_persisted_runtime_metadata_fields(tmp_path):
    config_path = tmp_path / project_config_file_name
    config_path.write_text(
        "\n".join([
            "templates:",
            "  - src_url: https://example.com/template.git#main",
            "    dest_folder: .",
            "project_folder_name: stale-workspace",
            "project_src_url: https://example.com/stale.git",
            "project_repo_org: stale-org",
            "project_repo_name: stale-repo",
        ]),
        encoding="utf-8",
    )

    loaded = project_config.from_file(open_plate_settings.defaultSettings, str(config_path))

    assert loaded.project_folder_name is None
    assert loaded.project_src_url is None
    assert loaded.project_repo_org is None
    assert loaded.project_repo_name is None


def test_project_config_rejects_non_blank_legacy_template_source_fields(tmp_path):
    config_path = tmp_path / project_config_file_name
    config_path.write_text(
        "\n".join([
            "templates:",
            "  - src_url: https://example.com/template.git#main",
            "    src_name: legacy-template",
            "    dest_folder: .",
        ]),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="URL-backed template references are required"):
        project_config.from_file(open_plate_settings.defaultSettings, str(config_path))


def test_project_config_rejects_non_blank_legacy_top_level_template_src_folder(tmp_path):
    config_path = tmp_path / project_config_file_name
    config_path.write_text(
        "\n".join([
            "template_src_url: https://example.com/template.git#main",
            "template_src_folder: ./templates/api",
        ]),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="URL-backed template references are required"):
        project_config.from_file(open_plate_settings.defaultSettings, str(config_path))


def test_settings_serialization_omits_legacy_source_resolution_fields(tmp_path):
    settings = open_plate_settings.OpenPlateSettings(
        "https://github.com",
        "ot-",
        {"service_name": "demo"},
        True,
        True,
    )

    settings_path = tmp_path / "settings.yaml"
    open_plate_settings.to_file(settings, str(settings_path))

    written = yaml.safe_load(settings_path.read_text(encoding="utf-8"))

    assert written == {
        "default_values": {"service_name": "demo"},
        "allow_template_commands": True,
        "allow_last_updater_email": True,
    }


def test_settings_load_ignores_legacy_source_resolution_fields(tmp_path):
    settings_path = tmp_path / "settings.yaml"
    settings_path.write_text(
        "\n".join([
            "vcs_url: https://example.com",
            "template_prefix: legacy-",
            "default_values:",
            "  service_name: demo",
        ]),
        encoding="utf-8",
    )

    loaded = open_plate_settings.from_file(str(settings_path))

    assert loaded.default_values == {"service_name": "demo"}
    assert loaded.vcs_url == open_plate_settings.defaultSettings.vcs_url
    assert loaded.template_prefix == open_plate_settings.defaultSettings.template_prefix
    assert loaded.allow_last_updater_email is False


def test_settings_load_reads_allow_last_updater_email(tmp_path):
    settings_path = tmp_path / "settings.yaml"
    settings_path.write_text(
        "allow_last_updater_email: true\n",
        encoding="utf-8",
    )

    loaded = open_plate_settings.from_file(str(settings_path))

    assert loaded.allow_last_updater_email is True


def test_project_config_load_reads_requires_last_updater_email(tmp_path):
    config_path = tmp_path / project_config_file_name
    config_path.write_text(
        "\n".join([
            "templates:",
            "  - src_url: https://example.com/template.git#main",
            "    dest_folder: .",
            "    requires_last_updater_email: true",
        ]),
        encoding="utf-8",
    )

    loaded = project_config.from_file(open_plate_settings.defaultSettings, str(config_path))

    assert loaded.templates[0].requires_last_updater_email is True


def test_config_set_parser_rejects_removed_legacy_source_resolution_flags():
    parser = create_arg_parser(["openplate", "config", "set"])

    with pytest.raises(SystemExit):
        parser.parse_args(["config", "set", "--vcs-url", "https://example.com"])

    with pytest.raises(SystemExit):
        parser.parse_args(["config", "set", "--template-prefix", "legacy-"])