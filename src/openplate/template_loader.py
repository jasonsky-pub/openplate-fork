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
from typing import Optional

from liquid import Environment, FileSystemLoader
from liquid import RenderContext
from liquid.loader import BaseLoader, TemplateSource


class OpenPlateTemplateLoader(BaseLoader):
    def __init__(self, template_string: str, paths: list[str]):
        self.template_string = template_string
        self.fs_loader = FileSystemLoader(paths)

    def get_source(
            self,
            environment: Environment,
            template_name: str,
            *,
            context: Optional[RenderContext] = None,
            **kwargs: object
    ) -> TemplateSource:
        if template_name == "":
            return TemplateSource(self.template_string, "", None)

        return self.fs_loader.get_source(environment, template_name, context=context, **kwargs)
