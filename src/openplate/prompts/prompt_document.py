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
import json
import re
from dataclasses import dataclass
from typing import Optional

from openplate.project_template_identity import full_prompt_node_id, normalize_prompt_dest_folder, short_prompt_node_id


_NODE_ID_PATTERN = re.compile(r"^(?:[0-9a-f]{7}|[0-9a-f]{64})$")


def _require_optional_string(value, field_name: str):
    if value is not None and not isinstance(value, str):
        raise TypeError(f"Prompt parameter '{field_name}' must be a string or null")


def _require_optional_bool(value, field_name: str):
    if value is not None and not isinstance(value, bool):
        raise TypeError(f"Prompt parameter '{field_name}' must be a boolean or null")


@dataclass
class PromptParameterValue:
    default: Optional[str]
    existing: Optional[str]
    description: Optional[str]
    choices: Optional[list[str]]
    hidden: Optional[bool]
    required: Optional[bool]

    @classmethod
    def from_json_data(cls, data):
        if not isinstance(data, dict):
            raise TypeError("Prompt parameter entry must be an object")

        choices = data.get("choices")
        if choices is not None and not isinstance(choices, list):
            raise TypeError("Prompt parameter 'choices' must be a list when provided")
        if choices is not None:
            for choice in choices:
                if not isinstance(choice, str):
                    raise TypeError("Prompt parameter 'choices' entries must be strings")

        _require_optional_string(data.get("default"), "default")
        _require_optional_string(data.get("existing"), "existing")
        _require_optional_string(data.get("description"), "description")
        _require_optional_bool(data.get("hidden"), "hidden")
        _require_optional_bool(data.get("required"), "required")

        return cls(
            data.get("default"),
            data.get("existing"),
            data.get("description"),
            choices,
            data.get("hidden"),
            data.get("required"),
        )

    def to_json_data(self):
        return {
            "default": self.default,
            "existing": self.existing,
            "description": self.description,
            "choices": self.choices,
            "hidden": self.hidden,
            "required": self.required,
        }


@dataclass
class PromptSiblingTemplateInfo:
    template: str
    dest_folder: str
    condition: Optional[str] = None

    @classmethod
    def from_json_data(cls, data):
        if not isinstance(data, dict):
            raise TypeError("Prompt sibling entry must be an object")

        template = data.get("template")
        if not isinstance(template, str) or not template.strip():
            raise ValueError("Prompt sibling entry must include a non-empty 'template' field")

        dest_folder = data.get("dest_folder")
        if not isinstance(dest_folder, str) or not dest_folder.strip():
            raise ValueError("Prompt sibling entry must include a non-empty 'dest_folder' field")

        condition = data.get("condition")
        if condition is not None and not isinstance(condition, str):
            raise TypeError("Prompt sibling 'condition' must be a string when provided")

        return cls(template.strip(), normalize_prompt_dest_folder(dest_folder), condition)

    def to_json_data(self):
        result = {
            "template": self.template,
            "dest_folder": self.dest_folder,
        }
        if self.condition is not None:
            result["condition"] = self.condition
        return result


@dataclass
class PromptNodeInfo:
    template: str
    dest_folder: str
    parameters: Optional[dict[str, PromptParameterValue]]
    require_sibling_templates: Optional[list[PromptSiblingTemplateInfo]] = None
    condition: Optional[str] = None

    @classmethod
    def from_json_data(cls, data):
        if not isinstance(data, dict):
            raise TypeError("Prompt node 'info' must be an object")

        template = data.get("template")
        if not isinstance(template, str) or not template.strip():
            raise ValueError("Prompt node 'info' must include a non-empty 'template' field")

        dest_folder = data.get("dest_folder")
        if not isinstance(dest_folder, str) or not dest_folder.strip():
            raise ValueError("Prompt node 'info' must include a non-empty 'dest_folder' field")

        raw_parameters = data.get("parameters")
        parameters = None
        if raw_parameters is not None:
            if not isinstance(raw_parameters, dict):
                raise TypeError("Prompt node 'info.parameters' must be an object or null")
            parameters = {}
            for name, parameter_data in raw_parameters.items():
                if not isinstance(name, str) or not name:
                    raise ValueError("Prompt parameter names must be non-empty strings")
                parameters[name] = PromptParameterValue.from_json_data(parameter_data)

        raw_required_siblings = data.get("require_sibling_templates")
        require_sibling_templates = None
        if raw_required_siblings is not None:
            if not isinstance(raw_required_siblings, list):
                raise TypeError("Prompt node 'info.require_sibling_templates' must be a list when provided")
            require_sibling_templates = [
                PromptSiblingTemplateInfo.from_json_data(entry)
                for entry in raw_required_siblings
            ]

        condition = data.get("condition")
        if condition is not None and not isinstance(condition, str):
            raise TypeError("Prompt node 'info.condition' must be a string when provided")

        return cls(
            template.strip(),
            normalize_prompt_dest_folder(dest_folder),
            parameters,
            require_sibling_templates,
            condition,
        )

    def to_json_data(self):
        result = {
            "template": self.template,
            "dest_folder": self.dest_folder,
            "parameters": None,
        }
        if self.parameters is not None:
            result["parameters"] = {
                name: parameter.to_json_data()
                for name, parameter in self.parameters.items()
            }
        if self.require_sibling_templates is not None:
            result["require_sibling_templates"] = [
                sibling.to_json_data()
                for sibling in self.require_sibling_templates
            ]
        if self.condition is not None:
            result["condition"] = self.condition
        return result


@dataclass
class PromptTemplateNode:
    node_id: str
    answers: dict[str, Optional[str]]
    info: Optional[PromptNodeInfo] = None

    @classmethod
    def from_json_data(cls, data):
        if not isinstance(data, dict):
            raise TypeError("Prompt node entry must be an object")

        node_id = data.get("node-id")
        if not isinstance(node_id, str) or not _NODE_ID_PATTERN.fullmatch(node_id):
            raise ValueError("Prompt node entry must include a valid 'node-id' field")

        if "answers" not in data:
            raise ValueError("Prompt node entry must include an 'answers' field")
        raw_answers = data.get("answers")
        if not isinstance(raw_answers, dict):
            raise TypeError("Prompt node 'answers' must be an object")

        answers = {}
        for name, value in raw_answers.items():
            if not isinstance(name, str) or not name:
                raise ValueError("Prompt answer names must be non-empty strings")
            _require_optional_string(value, name)
            answers[name] = value

        raw_info = data.get("info")
        info = None
        if raw_info is not None:
            info = PromptNodeInfo.from_json_data(raw_info)

        return cls(node_id, answers, info)

    @property
    def template(self) -> Optional[str]:
        if self.info is None:
            return None
        return self.info.template

    @property
    def dest_folder(self) -> Optional[str]:
        if self.info is None:
            return None
        return self.info.dest_folder

    @property
    def parameters(self) -> Optional[dict[str, PromptParameterValue]]:
        if self.info is None:
            return None
        return self.info.parameters

    def to_json_data(self, verbose: bool):
        result = {
            "node-id": self.node_id,
            "answers": self.answers,
        }
        if verbose and self.info is not None:
            result["info"] = self.info.to_json_data()
        return result


@dataclass
class PromptDocument:
    nodes: list[PromptTemplateNode]

    @property
    def templates(self):
        return self.nodes

    @classmethod
    def from_json_string(cls, json_string: str):
        raw_data = json.loads(json_string)
        if not isinstance(raw_data, list):
            raise TypeError("Prompt document must be a JSON array")

        nodes = []
        seen_node_ids = set()
        for entry in raw_data:
            node = PromptTemplateNode.from_json_data(entry)
            if node.node_id in seen_node_ids:
                raise ValueError(f"Duplicate prompt node entry: node-id={node.node_id!r}")
            seen_node_ids.add(node.node_id)
            nodes.append(node)

        return cls(nodes)

    def to_json_string(self, verbose: bool = False) -> str:
        return json.dumps([node.to_json_data(verbose) for node in self.nodes], indent=2)


class PromptDocumentBuilder:
    def __init__(self):
        self._nodes = []
        self._nodes_by_full_id = {}
        self._short_ids = {}

    def add_template(
        self,
        template: str,
        dest_folder: Optional[str],
        parameters: Optional[dict[str, PromptParameterValue]],
        require_sibling_templates: Optional[list[PromptSiblingTemplateInfo]] = None,
        identity_dest_folder: Optional[str] = None,
    ):
        normalized_dest_folder = normalize_prompt_dest_folder(dest_folder)
        normalized_identity_dest_folder = normalize_prompt_dest_folder(
            identity_dest_folder if identity_dest_folder is not None else dest_folder
        )
        full_node_id = full_prompt_node_id(template, normalized_identity_dest_folder)
        existing_node = self._nodes_by_full_id.get(full_node_id)
        if existing_node is None:
            preferred_short_id = short_prompt_node_id(full_node_id)
            node_id = preferred_short_id
            if preferred_short_id in self._short_ids and self._short_ids[preferred_short_id] != full_node_id:
                node_id = full_node_id
            else:
                self._short_ids[preferred_short_id] = full_node_id

            info = PromptNodeInfo(
                template=template,
                dest_folder=normalized_dest_folder,
                parameters=parameters,
                require_sibling_templates=require_sibling_templates,
            )
            answers = {}
            if parameters is not None:
                answers = {name: None for name in parameters.keys()}

            existing_node = PromptTemplateNode(node_id, answers, info)
            self._nodes.append(existing_node)
            self._nodes_by_full_id[full_node_id] = existing_node
            return True

        if parameters is not None:
            existing_node.answers = {name: None for name in parameters.keys()}
            if existing_node.info is not None:
                existing_node.info.parameters = parameters
        if existing_node.info is not None and require_sibling_templates is not None:
            existing_node.info.require_sibling_templates = require_sibling_templates

        return False

    def build(self) -> PromptDocument:
        return PromptDocument(list(self._nodes))


class PromptInputTracker:
    def __init__(self, document: Optional[PromptDocument]):
        self._document = document
        self._by_node_id = {}
        self._by_info_key = {}
        self._used_node_ids = set()
        self._used_parameter_names = {}
        self._resolved_runtime_nodes = {}

        if document is None:
            return

        for node in document.nodes:
            self._by_node_id[node.node_id] = node
            self._used_parameter_names[node.node_id] = set()
            if node.info is not None:
                self._by_info_key[(node.info.template, node.info.dest_folder)] = node.node_id

    @classmethod
    def from_json_string(cls, json_string: str):
        return cls(PromptDocument.from_json_string(json_string))

    def _resolve_supplied_node_id(self, runtime_node_id: str) -> Optional[str]:
        cached_node_id = self._resolved_runtime_nodes.get(runtime_node_id)
        if cached_node_id is not None:
            return cached_node_id

        if runtime_node_id in self._by_node_id:
            self._resolved_runtime_nodes[runtime_node_id] = runtime_node_id
            return runtime_node_id

        runtime_short_node_id = short_prompt_node_id(runtime_node_id)
        if runtime_short_node_id in self._by_node_id:
            self._resolved_runtime_nodes[runtime_node_id] = runtime_short_node_id
            return runtime_short_node_id

        return None

    def get_template(self, template_or_node_id: str, dest_folder: Optional[str] = None) -> Optional[PromptTemplateNode]:
        if dest_folder is None:
            node_id = self._resolve_supplied_node_id(template_or_node_id) or template_or_node_id
        else:
            node_id = self._by_info_key.get((template_or_node_id, normalize_prompt_dest_folder(dest_folder)))

        node = self._by_node_id.get(node_id)
        if node is not None:
            self._used_node_ids.add(node_id)
        return node

    def mark_template_used(self, template_or_node_id: str, dest_folder: Optional[str] = None):
        node = self.get_template(template_or_node_id, dest_folder)
        if node is not None:
            self._used_node_ids.add(node.node_id)

    def get_parameter_value(self, template_or_node_id: str, dest_folder_or_name: Optional[str], name: Optional[str] = None):
        if name is None:
            node = self.get_template(template_or_node_id)
            parameter_name = dest_folder_or_name
        else:
            node = self.get_template(template_or_node_id, dest_folder_or_name)
            parameter_name = name

        if node is None or parameter_name is None:
            return None, False

        if parameter_name not in node.answers:
            return None, False

        self._used_parameter_names[node.node_id].add(parameter_name)
        return node.answers.get(parameter_name), True

    def ignored_templates(self) -> list[PromptTemplateNode]:
        if self._document is None:
            return []
        return [
            node for node in self._document.nodes
            if node.node_id not in self._used_node_ids
        ]

    def unused_parameters(self, template_or_node_id: str, dest_folder: Optional[str] = None) -> list[str]:
        node = self.get_template(template_or_node_id, dest_folder)
        if node is None:
            return []

        used_names = self._used_parameter_names.get(node.node_id, set())
        unused = []
        for answer_name, answer_value in node.answers.items():
            if answer_value is None:
                continue
            if answer_name not in used_names:
                unused.append(answer_name)
        return unused