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
import os
import sys
from typing import Callable, TextIO

from openplate import template_processor
from openplate.cfg import template_config
from openplate.walk.recursive_walker import norm_relative_path


def _render_init_command(
    command_index: int,
    init_command: template_config.InitCommand,
    template_options,
    config_template: template_config.TemplateConfig,
    project_folder: str,
) -> str:
    rendered_command = template_processor.process(
        template_options,
        str(init_command.command),
        [],
        f"init_commands[{command_index}]",
        config_template.override_tag_start,
        config_template.override_tag_end,
        config_template.override_statement_start,
        config_template.override_statement_end,
    )

    if not init_command.folder:
        rendered_folder = project_folder
    else:
        folder_processed = template_processor.process(
            template_options,
            str(init_command.folder),
            [],
            f"init_commands[{command_index}]",
            config_template.override_tag_start,
            config_template.override_tag_end,
            config_template.override_statement_start,
            config_template.override_statement_end,
        )
        relative_folder = norm_relative_path(folder_processed)
        rendered_folder = os.path.join(project_folder, relative_folder)

    return f"- (cwd: {rendered_folder}) {rendered_command}"


def _render_init_command_raw(
    command_index: int,
    init_command: template_config.InitCommand,
    project_folder: str,
) -> str:
    command = str(init_command.command)

    if not init_command.folder:
        rendered_folder = project_folder
    else:
        # Folder may include template tokens; show a best-effort cwd.
        relative_folder = norm_relative_path(str(init_command.folder))
        rendered_folder = os.path.join(project_folder, relative_folder)

    return f"- (cwd: {rendered_folder}) {command}"


def _render_init_commands_for_error_raw(
    init_commands: list[template_config.InitCommand],
    project_folder: str,
) -> str:
    rendered_commands = []
    for idx, init_command in enumerate(init_commands):
        rendered_commands.append(_render_init_command_raw(idx, init_command, project_folder))

    return "\n".join(rendered_commands) if len(rendered_commands) > 0 else "- (none)"


def _get_template_reference(source) -> str:
    return source.template_url() or source.template_folder() or source.__str__()


def _prompt_yes_no(
    prompt: str,
    *,
    input_func: Callable[[str], str],
    output: TextIO,
) -> bool:
    while True:
        answer = input_func(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("", "n", "no"):
            return False
        print("Please answer 'yes' or 'no'.", file=output)


def confirm_continue_with_template_init_commands(
    *,
    source,
    init_commands: list[template_config.InitCommand],
    project_folder: str,
    allow_template_commands: bool,
    fail_on_prompt: bool,
    stdin_isatty: Callable[[], bool] = sys.stdin.isatty,
    input_func: Callable[[str], str] = input,
    stderr: TextIO = sys.stderr,
) -> bool:
    if allow_template_commands:
        return True

    template_ref = _get_template_reference(source)
    init_commands_block = _render_init_commands_for_error_raw(init_commands, project_folder)

    if fail_on_prompt or not stdin_isatty():
        print(
            "Template init_commands require confirmation but prompting is disabled.\n"
            f"Template: {template_ref}\n"
            "This template defines init_commands that would run later:\n"
            f"{init_commands_block}\n\n"
            "To allow for this init only, re-run with: openplate init --allow-template-commands ...\n"
            "To allow permanently, run: openplate config set --allow-template-commands\n",
            file=stderr,
        )
        return False

    prompt = (
        "Template init_commands are disabled by default for safety.\n"
        f"Template: {template_ref}\n"
        "This template defines init_commands that would run later:\n"
        f"{init_commands_block}\n\n"
        "To allow for this init only and skip prompts, re-run with: openplate init --allow-template-commands ...\n"
        "To allow permanently and skip prompts, run: openplate config set --allow-template-commands\n\n"
        "Continue processing this template? (yes/no) [no]: "
    )

    should_continue = _prompt_yes_no(prompt, input_func=input_func, output=stderr)
    if not should_continue:
        print("Aborted.", file=stderr)
    return should_continue


def confirm_run_init_command(
    *,
    source,
    init_command: template_config.InitCommand,
    command_index: int,
    template_options,
    config_template: template_config.TemplateConfig,
    project_folder: str,
    allow_template_commands: bool,
    fail_on_prompt: bool,
    stdin_isatty: Callable[[], bool] = sys.stdin.isatty,
    input_func: Callable[[str], str] = input,
    stderr: TextIO = sys.stderr,
) -> bool:
    if allow_template_commands:
        return True

    template_ref = _get_template_reference(source)
    rendered_command_line = _render_init_command(
        command_index,
        init_command,
        template_options,
        config_template,
        project_folder,
    )

    if fail_on_prompt or not stdin_isatty():
        print(
            "Template init_commands require confirmation but prompting is disabled.\n"
            f"Template: {template_ref}\n"
            f"Command: {rendered_command_line}\n\n"
            "To allow for this init only, re-run with: openplate init --allow-template-commands ...\n"
            "To allow permanently, run: openplate config set --allow-template-commands\n",
            file=stderr,
        )
        return False

    prompt = (
        "Template init_commands are disabled by default for safety.\n"
        f"Template: {template_ref}\n"
        "About to run:\n"
        f"{rendered_command_line}\n\n"
        "To allow for this init only and skip prompts, re-run with: openplate init --allow-template-commands ...\n"
        "To allow permanently and skip prompts, run: openplate config set --allow-template-commands\n\n"
        "Run this command? (yes/no) [no]: "
    )

    should_run = _prompt_yes_no(prompt, input_func=input_func, output=stderr)
    if not should_run:
        print("Aborted.", file=stderr)
    return should_run
