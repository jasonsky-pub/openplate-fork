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
import sys

from openplate.prompts.prompt_document import PromptDocument


def add_prompt_document_input_arguments(parser):
    parser.add_argument(
        "--prompts-json-file",
        required=False,
        help="Load prompt answers from a JSON file."
    )
    parser.add_argument(
        "--prompts-json-stdin",
        required=False,
        default=False,
        help="Load prompt answers from JSON on standard input.",
        action="store_true"
    )


def load_prompt_document(result) -> PromptDocument | None:
    prompt_input_flags = int(bool(getattr(result, "prompts_json_file", None))) + int(bool(getattr(result, "prompts_json_stdin", False)))

    if prompt_input_flags > 1:
        raise ValueError("Specify only one prompts JSON input source, either --prompts-json-file or --prompts-json-stdin")

    if getattr(result, "prompts_json_file", None):
        with open(result.prompts_json_file, encoding="utf-8") as prompts_json_file:
            return PromptDocument.from_json_string(prompts_json_file.read())

    if getattr(result, "prompts_json_stdin", False):
        return PromptDocument.from_json_string(sys.stdin.read())

    return None