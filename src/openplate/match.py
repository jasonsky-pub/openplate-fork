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
import re
from typing import Optional

from openplate import template_processor
from openplate.cfg.template_config import TemplateConfig


class RegexMultiMatcher:
    def __init__(self, expressions: Optional[list[str]]):
        self._expressions = expressions
        self._patterns = None

    def is_match(
        self,
        value: str,
        template_options: dict[str, str],
        config_template: TemplateConfig
    ) -> bool:
        if self._patterns is None:
            self._patterns = []
            if self._expressions is not None:
                for exp in self._expressions:
                    replaced = template_processor.process(
                        template_options,
                        exp,
                        [],
                        "regex: " + exp,
                        config_template.override_tag_start,
                        config_template.override_tag_end,
                        config_template.override_statement_start,
                        config_template.override_statement_end
                    )
                    self._patterns.append(re.compile(replaced))

        for exp in self._patterns:
            if exp.match(value):
                return True
        return False


class RegexMultiReplacer:
    def __init__(self, replacements: Optional[dict[str, str]]):
        self._replacements = replacements

    def replace(
        self,
        value: str,
        template_options: dict[str, str],
        config_template: TemplateConfig
    ) -> str:
        cur_value = value
        if self._replacements is not None:
            for (key, value) in self._replacements.items():
                replaced_key = template_processor.process(
                    template_options,
                    key,
                    [],
                    "regex: " + key,
                    config_template.override_tag_start,
                    config_template.override_tag_end,
                    config_template.override_statement_start,
                    config_template.override_statement_end
                )
                replaced_value = template_processor.process(
                    template_options,
                    value,
                    [],
                    "value: " + value,
                    config_template.override_tag_start,
                    config_template.override_tag_end,
                    config_template.override_statement_start,
                    config_template.override_statement_end
                )
                cur_value = re.sub(replaced_key, replaced_value, cur_value)

        return cur_value
