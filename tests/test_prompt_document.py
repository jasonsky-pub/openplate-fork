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
import pytest

from openplate.prompts.prompt_document import PromptDocument, PromptInputTracker


pytestmark = pytest.mark.unit


def test_prompt_document_rejects_duplicate_node_ids():
    json_string = """
    [
      {"node-id": "123abcd", "answers": {}},
      {"node-id": "123abcd", "answers": {}}
    ]
    """

    with pytest.raises(ValueError, match="Duplicate prompt node entry"):
        PromptDocument.from_json_string(json_string)


def test_prompt_document_rejects_invalid_node_id_format():
    json_string = """
    [
      {
        "node-id": "INVALID",
        "answers": {}
      }
    ]
    """

    with pytest.raises(ValueError, match="valid 'node-id'"):
        PromptDocument.from_json_string(json_string)


def test_prompt_document_rejects_non_string_answer_value():
    json_string = """
    [
      {
        "node-id": "123abcd",
        "answers": {
          "service_name": 123
        }
      }
    ]
    """

    with pytest.raises(TypeError, match="must be a string or null"):
        PromptDocument.from_json_string(json_string)


def test_prompt_document_rejects_non_boolean_hidden_flag_in_info_metadata():
    json_string = """
    [
      {
        "node-id": "123abcd",
        "answers": {
          "service_name": null
        },
        "info": {
          "template": "repo#main",
          "dest_folder": ".",
          "parameters": {
            "service_name": {
              "hidden": "yes"
            }
          }
        }
      }
    ]
    """

    with pytest.raises(TypeError, match="'hidden' must be a boolean or null"):
        PromptDocument.from_json_string(json_string)


def test_prompt_document_round_trips_verbose_info_metadata():
    json_string = """
    [
      {
        "node-id": "123abcd",
        "answers": {
          "service_name": null
        },
        "info": {
          "template": "repo#main",
          "dest_folder": ".",
          "parameters": null,
          "condition": "{{ include_api }}"
        }
      }
    ]
    """

    document = PromptDocument.from_json_string(json_string)

    assert document.templates[0].parameters is None
    assert '"info"' not in document.to_json_string()
    assert '"parameters": null' in document.to_json_string(verbose=True)


def test_prompt_input_tracker_treats_null_answer_as_unresolved():
    tracker = PromptInputTracker.from_json_string(
        """
        [
          {
            "node-id": "123abcd",
            "answers": {
              "service_name": null
            }
          }
        ]
        """
    )

    value, found = tracker.get_parameter_value("123abcd", "service_name")

    assert value is None
    assert found is True


def test_prompt_input_tracker_reports_unused_supplied_parameters():
    tracker = PromptInputTracker.from_json_string(
        """
        [
          {
            "node-id": "123abcd",
            "answers": {
              "used": "x",
              "unused": "y",
              "null_value": null
            }
          }
        ]
        """
    )

    value, found = tracker.get_parameter_value("123abcd", "used")

    assert value == "x"
    assert found is True
    assert tracker.unused_parameters("123abcd") == ["unused"]


def test_prompt_input_tracker_reports_ignored_nodes():
    tracker = PromptInputTracker.from_json_string(
        """
        [
          {"node-id": "123abcd", "answers": {}},
          {"node-id": "abcdef0", "answers": {}}
        ]
        """
    )

    tracker.get_template("123abcd")

    ignored = tracker.ignored_templates()

    assert len(ignored) == 1
    assert ignored[0].node_id == "abcdef0"