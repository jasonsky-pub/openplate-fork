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
import logging
from typing import Optional

from openplate.prompts.prompt_document import PromptInputTracker


def log_ignored_prompt_templates(prompt_input_tracker: Optional[PromptInputTracker]):
    if prompt_input_tracker is None:
        return

    for ignored_template in prompt_input_tracker.ignored_templates():
        logging.warning(
            "Ignoring supplied prompt template because it was not processed: node-id=%r template=%r dest_folder=%r",
            ignored_template.node_id,
            ignored_template.template,
            ignored_template.dest_folder,
        )