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
import argparse
import asyncio
import logging
import os
import platform
import sys

from openplate import __semver__ as module_semver
from openplate import __version__ as module_version
from openplate.cfg import open_plate_settings
from openplate.cfg.open_plate_settings import OpenPlateRuntimeSettings
from openplate.cfg.project_config import ProjectTemplateConfig
from openplate.commands import (
    config_get,
    config_set,
    project_info,
    project_init,
    project_update,
    project_verify,
)
from openplate.commands.project_info import InfoOptions
from openplate.commands.config_set import ConfigSetOptions
from openplate.commands.project_init import InitOptions
from openplate.commands.project_update import UpdateOptions
from openplate.commands.project_verify import VerifyOptions
from openplate.project_runtime_context import resolve_project_runtime_context
from openplate.prompts.prompt_document_cli import (
    add_prompt_document_input_arguments,
    load_prompt_document as load_prompt_document_from_args,
)


class DeprecatedProjectFolderAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parser.error("The --project-folder option has been renamed. Use --project-root instead.")


def add_common_project_runtime_arguments(parser, include_prompt_flags: bool = True):
    parser.add_argument("-p", "--project-root", required=False,
                        help="Project Root Location: (current folder or Git top-level assumed) ")
    parser.add_argument("--project-folder", required=False, help=argparse.SUPPRESS, action=DeprecatedProjectFolderAction)

    parser.add_argument("--ignore-tool-version", required=False, default=False,
                        help="Ignore project required version (UNSAFE, mainly used for running locally not from pip)", action=argparse.BooleanOptionalAction)
    if include_prompt_flags:
        parser.add_argument("--ask-again", required=False, default=False,
                            help="Ask already asked parameters again", action=argparse.BooleanOptionalAction)
        parser.add_argument("--ask-hidden", required=False, default=False,
                            help="Ask parameters which are normally hidden", action=argparse.BooleanOptionalAction)


def configure_project_init_parser(parser):
    parser.set_defaults(command="project-init")
    parser.add_argument("-o", "--overwrite",
                        required=False, help="Overwrite existing files (Do not fail and update them)",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--cache", required=False,
                        action=argparse.BooleanOptionalAction, help="Cache the files from this template")
    parser.add_argument("--dest-folder", required=False, help="sub-folder to init into.  NOTE: This needs to be implemented in the template (dest_folder variable) to work, otherwise ignored.")
    parser.add_argument("-i", "--ignore", action='append', required=False,
                        help="Ignore files from template with relative path regex")
    parser.add_argument("source", nargs="?", help="Template source URL")
    parser.add_argument("-r", "--url", required=False, help="Template source URL (legacy alias for positional source)")
    parser.add_argument(
        "--allow-default-branch",
        required=False,
        default=False,
        help="Allow use of a default branch in a repo reference",
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        "--allow-template-commands",
        required=False,
        default=False,
        help="One-time override to allow template-provided init_commands to run during this init.",
        action="store_true"
    )
    parser.add_argument(
        "--allow-last-updater-email",
        required=False,
        default=False,
        help="One-time override to allow a requiring template to use last_updater_email during this run.",
        action="store_true"
    )
    add_prompt_document_input_arguments(parser)


def configure_project_update_parser(parser):
    parser.set_defaults(command="project-update")
    parser.add_argument("-m", "--update-missing",
                        required=False, help="Re-create missing non-template files",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-f", "--update-full",
                        required=False, help="Full update, overwrite existing non-template files (WARNING: will overwrite changes)",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument(
        "--allow-last-updater-email",
        required=False,
        default=False,
        help="One-time override to allow a requiring template to use last_updater_email during this run.",
        action="store_true"
    )
    add_prompt_document_input_arguments(parser)


def configure_project_verify_parser(parser):
    parser.set_defaults(command="project-verify")


def configure_project_info_parser(parser):
    parser.set_defaults(command="project-info")
    parser.add_argument(
        "--offline",
        required=False,
        default=False,
        help="Show only persisted project-file data without inspecting template sources.",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--show-hidden",
        required=False,
        default=False,
        help="Include hidden parameters when inspecting template metadata.",
        action=argparse.BooleanOptionalAction,
    )


def hide_subparser_from_help(subparsers, command_name):
    subparsers._choices_actions = [
        choice_action for choice_action in subparsers._choices_actions
        if choice_action.dest != command_name
    ]


def create_arg_parser(args):
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-c", "--config-file", type=str, required=False, help="Configuration file to use (yaml)")
    arg_parser.add_argument("-d", "--debug", required=False,
                            help="Debug mode is enabled or not", action=argparse.BooleanOptionalAction)
    arg_parser.add_argument("--version", action="store_true", help="Show version and exit")
    arg_parser.add_argument(
        "-a", "--automation",
        required=False, default=False, action=argparse.BooleanOptionalAction,
        help="Present an automation readable response instead of human readable one.  Use rules related to automation.")

    subparsers = arg_parser.add_subparsers(required="--version" not in args, metavar="{config,init,update,verify,info}")

    parser_config = subparsers.add_parser("config")
    config_subparsers = parser_config.add_subparsers(required=True)

    parser_get_config = config_subparsers.add_parser("get")
    parser_get_config.set_defaults(command="config-get")

    parser_set_config = config_subparsers.add_parser("set")
    parser_set_config.set_defaults(command="config-set")
    parser_set_config.add_argument("--parameter-default", required=False, help="Set a default parameter value, --parameter-default \"param1=something\" or to remove, --parameter-default \"param1=\"", action='append')
    parser_set_config.add_argument(
        "--allow-template-commands",
        required=False,
        default=None,
        help="Allow template-provided init_commands to run during project init (unsafe unless you trust the template source).",
        action=argparse.BooleanOptionalAction
    )
    parser_set_config.add_argument(
        "--allow-last-updater-email",
        required=False,
        default=None,
        help="Allow requiring templates to use last_updater_email during init or update.",
        action=argparse.BooleanOptionalAction
    )

    parser_init = subparsers.add_parser("init")
    add_common_project_runtime_arguments(parser_init)
    configure_project_init_parser(parser_init)

    parser_update = subparsers.add_parser("update")
    add_common_project_runtime_arguments(parser_update)
    configure_project_update_parser(parser_update)

    parser_verify = subparsers.add_parser("verify")
    add_common_project_runtime_arguments(parser_verify)
    configure_project_verify_parser(parser_verify)

    parser_info = subparsers.add_parser("info")
    add_common_project_runtime_arguments(parser_info, include_prompt_flags=False)
    configure_project_info_parser(parser_info)

    parser_project = subparsers.add_parser("project", help=argparse.SUPPRESS)
    add_common_project_runtime_arguments(parser_project)
    hide_subparser_from_help(subparsers, "project")

    project_subparsers = parser_project.add_subparsers(required=True)
    parser_print_init_json = project_subparsers.add_parser("print-init-json")
    parser_print_init_json.set_defaults(command="project-print-init-json")
    parser_print_init_json.add_argument("source", help="Template source URL")
    parser_print_init_json.add_argument("--dest-folder", required=False, help="sub-folder to init into for prompt export.")
    parser_print_init_json.add_argument(
        "--allow-default-branch",
        required=False,
        default=False,
        help="Allow use of a default branch in a repo reference",
        action=argparse.BooleanOptionalAction
    )
    parser_print_init_json.add_argument(
        "--verbose",
        required=False,
        default=False,
        help="Include descriptive node metadata in the printed JSON output.",
        action="store_true"
    )
    parser_print_update_json = project_subparsers.add_parser("print-update-json")
    parser_print_update_json.set_defaults(command="project-print-update-json")

    legacy_parser_init = project_subparsers.add_parser("init")
    configure_project_init_parser(legacy_parser_init)

    legacy_parser_update = project_subparsers.add_parser("update")
    configure_project_update_parser(legacy_parser_update)

    legacy_parser_verify = project_subparsers.add_parser("verify")
    configure_project_verify_parser(legacy_parser_verify)

    legacy_parser_info = project_subparsers.add_parser("info")
    configure_project_info_parser(legacy_parser_info)

    return arg_parser


def resolve_project_init_source_reference(result) -> str:
    source_reference = result.source or getattr(result, "url", None)

    if result.source and getattr(result, "url", None):
        raise ValueError("Specify exactly one template source URL, either positionally or with -r/--url")

    if not source_reference:
        raise ValueError("Must specify a template source URL, ex: openplate init https://github.com/my-org/ot-template#v1")

    if "#" not in str(source_reference) and not result.allow_default_branch:
        raise ValueError("Must specify a tag or branch name or use --allow-default-branch, ex: openplate init https://github.com/my-org/ot-template#v1")

    return source_reference


def load_prompt_document(result):
    return load_prompt_document_from_args(result)


async def async_main(args):
    arg_parser = create_arg_parser(args)

    if len(args) == 1:
        arg_parser.print_help()
        exit(-1)

    result = arg_parser.parse_args(args[1:])
    if result.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    if result.command == "project-info":
        if getattr(result, "ask_again", False):
            raise ValueError("--ask-again is not supported for 'openplate info'")
        if getattr(result, "ask_hidden", False):
            raise ValueError("Use --show-hidden instead of --ask-hidden with 'openplate info'")

    logging.debug(f"Python version: {platform.python_version()}")
    config_file = result.config_file or open_plate_settings.defaultSettingsLocation

    if result.version:
        if module_semver == module_version:
            print(f"openplate v{module_semver}")
        else:
            print(f"openplate v{module_semver} (PyPI {module_version})")
        exit(0)

    configuration = open_plate_settings.from_file(config_file)
    if configuration is None:
        logging.debug("Using default configuration")
        configuration = open_plate_settings.defaultSettings

    runtime_settings = None
    project_context = None
    prompts_json_input_present = bool(getattr(result, "prompts_json_file", None) or getattr(result, "prompts_json_stdin", False))
    if result.command.startswith("project"):
        runtime_settings = OpenPlateRuntimeSettings(
            getattr(result, "ask_again", False),
            getattr(result, "ask_hidden", False) or getattr(result, "show_hidden", False),
            result.ignore_tool_version,
            result.automation,
            getattr(result, "allow_last_updater_email", False),
            prompts_json_input_present,
            result.command in {"project-init", "project-update"},
            result.command in {"project-init", "project-update"},
        )
        project_context = resolve_project_runtime_context(
            os.getcwd(),
            getattr(result, "project_root", None),
            getattr(result, "dest_folder", None) if result.command in {"project-init", "project-print-init-json"} else None,
        )
    else:
        runtime_settings = OpenPlateRuntimeSettings(False, False, False, result.automation, False)

    if result.command == "config-set":
        defaults = {}

        if (not result.parameter_default
                and result.allow_template_commands is None
                and result.allow_last_updater_email is None):
            raise ValueError("Must set at least one setting (parameter-default, allow-template-commands, allow-last-updater-email)")

        if result.parameter_default:
            for parameter_string in result.parameter_default:
                parts = parameter_string.split("=", 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid parameter default: \"{parameter_string}\", format expected 'key=value'")
                key = parts[0]
                value = parts[1]
                defaults[key] = value

        options = ConfigSetOptions(
            config_file,
            defaults,
            result.allow_template_commands,
            result.allow_last_updater_email,
        )
        await config_set.run(configuration, options)
    elif result.command == "config-get":
        await config_get.run(configuration)
    elif result.command == "project-init":
        ignore_paths = result.ignore or []
        source_reference = resolve_project_init_source_reference(result)
        prompt_document = load_prompt_document(result)

        if result.url and not result.source:
            print(
                "WARNING: The -r/--url syntax is deprecated. Use 'openplate init <url>' instead.",
                file=sys.stderr
            )

        if result.cache is None:
            no_cache = False
        else:
            no_cache = not result.cache

        template = ProjectTemplateConfig(
            source_reference,
            None,
            None,
            project_context.dest_folder,
            None,
            {},
            ignore_paths,
            no_cache,
            raw_dest_folder=project_context.dest_folder,
        )

        options = InitOptions(
            template,
            project_context.project_root_folder,
            result.overwrite,
            result.allow_template_commands,
            prompt_document=prompt_document,
        )
        await project_init.run(configuration, runtime_settings, options)
    elif result.command == "project-print-init-json":
        source_reference = resolve_project_init_source_reference(result)
        template = ProjectTemplateConfig(source_reference, None, None, project_context.dest_folder, None, {}, [], False)
        await project_init.print_prompt_document(
            configuration,
            runtime_settings,
            template,
            project_context.project_root_folder,
            result.verbose,
        )
    elif result.command == "project-print-update-json":
        await project_update.print_prompt_document(
            configuration,
            runtime_settings,
            project_context.project_root_folder,
        )
    elif result.command == "project-verify":
        options = VerifyOptions(project_context.project_root_folder)
        await project_verify.run(configuration, runtime_settings, options)
    elif result.command == "project-info":
        options = InfoOptions(
            project_context.project_root_folder,
            result.offline,
        )
        await project_info.run(configuration, runtime_settings, options)
    elif result.command == "project-update":
        prompt_document = load_prompt_document(result)
        if prompt_document is not None:
            runtime_settings.ask_hidden = True
        options = UpdateOptions(
            project_context.project_root_folder,
            result.update_missing,
            result.update_full,
            prompt_document=prompt_document,
        )
        await project_update.run(configuration, runtime_settings, options)
    else:
        raise Exception(f"Unknown Command: {result.command}")


def main():
    asyncio.run(async_main(sys.argv))


if __name__ == '__main__':
    main()
