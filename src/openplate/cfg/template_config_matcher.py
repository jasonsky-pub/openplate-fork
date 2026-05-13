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
from openplate.cfg.project_config import ProjectTemplateConfig
from openplate.cfg.template_config import TemplateConfig
from openplate.match import RegexMultiMatcher, RegexMultiReplacer


class TemplateConfigMatcher:
    def __init__(self, template_config: TemplateConfig, project_config: ProjectTemplateConfig):
        self.ignore_paths_matcher = RegexMultiMatcher(template_config.ignore_paths or [])
        self.replacement_paths_matcher = RegexMultiMatcher(template_config.replacement_paths or [])
        self.user_paths_matcher = RegexMultiMatcher(template_config.user_paths or [])
        self.readonly_paths_matcher = RegexMultiMatcher(template_config.readonly_paths or [])
        self.optional_paths_matcher = RegexMultiMatcher(template_config.optional_paths or [])
        self.rename_rules_replacer = RegexMultiReplacer(template_config.rename_rules or {})
        self.project_template_ignore_paths = RegexMultiMatcher(project_config.template_ignore_paths or {})
        self.remove_paths_matcher = RegexMultiMatcher(template_config.remove_files or [])

