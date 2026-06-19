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
import hashlib
import json

from openplate.cfg.open_plate_settings import OpenPlateSettings
from openplate.walk.recursive_walker import norm_relative_path


def normalize_prompt_dest_folder(dest_folder):
    if dest_folder is None:
        return "."

    stripped_dest_folder = str(dest_folder).strip().replace("\\", "/")
    if not stripped_dest_folder:
        return "."

    normalized_dest_folder = norm_relative_path(stripped_dest_folder)
    return normalized_dest_folder or "."


def canonical_prompt_node_identity(template_reference: str, dest_folder):
    return json.dumps({
        "template": template_reference,
        "dest_folder": normalize_prompt_dest_folder(dest_folder),
    }, sort_keys=True, separators=(",", ":"))


def full_prompt_node_id(template_reference: str, dest_folder) -> str:
    canonical_identity = canonical_prompt_node_identity(template_reference, dest_folder)
    return hashlib.sha256(canonical_identity.encode("utf-8")).hexdigest()


def short_prompt_node_id(full_node_id: str) -> str:
    return full_node_id[:7]


def prompt_template_reference(config_project_template):
    return config_project_template.raw_template_reference


def prompt_dest_folder(config_project_template):
    return normalize_prompt_dest_folder(config_project_template.dest_folder)


def prompt_identity_dest_folder(config_project_template):
    return normalize_prompt_dest_folder(config_project_template.raw_dest_folder)


def prompt_node_id(config_project_template) -> str:
    return full_prompt_node_id(
        prompt_template_reference(config_project_template),
        prompt_identity_dest_folder(config_project_template),
    )


def prompt_condition(config_project_template):
    return config_project_template.raw_condition


def source_cache_key(settings: OpenPlateSettings, config_project_template):
    if config_project_template.src_url:
        return ("url", config_project_template.src_url)
    raise ValueError("Unknown or unsupported template source")