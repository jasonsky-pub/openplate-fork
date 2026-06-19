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
import os.path
from typing import Optional, Any

import yaml


def _to_serializable_data(value):
    if value is None or isinstance(value, (str, int, float, bool, bytes)):
        return value

    if isinstance(value, dict):
        return {
            _to_serializable_data(key): _to_serializable_data(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_to_serializable_data(item) for item in value]

    if isinstance(value, tuple):
        return tuple(_to_serializable_data(item) for item in value)

    if hasattr(value, "__getstate__") and type(value).__module__ != "builtins":
        return _to_serializable_data(value.__getstate__())

    return value


def raw_from_file(file_name: str) -> str:
    if file_name is None:
        raise TypeError
    real_file = os.path.expanduser(file_name)

    if not os.path.isfile(real_file):
        logging.debug(f"file doesn't exist: {real_file}")
        return None

    try:
        with open(real_file) as stream:
            data = stream.read()
            logging.debug(f"loaded file: {real_file}")
            return data

    except Exception as e:
        logging.debug(f"Error reading file: {real_file}")
        raise e


def from_file(file_name: str) -> Optional[Any]:
    data_str = raw_from_file(file_name)
    if data_str is None:
        return None

    try:
        data = yaml.safe_load(data_str)
        return data

    except Exception as e:
        logging.debug(f"Error reading yaml file: {file_name}")
        raise e


def from_string(data_str: str, from_name: str) -> Optional[Any]:
    try:
        data = yaml.safe_load(data_str)
        return data
    except Exception as e:
        logging.debug(f"Error deserializing yaml: {from_name}")
        raise e


def to_file(data: object, file_name: str):
    if file_name is None:
        raise TypeError

    try:
        real_file = os.path.expanduser(file_name)
        serializable_data = _to_serializable_data(data)

        # not sure how to get clean yaml without this:
        yaml.emitter.Emitter.prepare_tag = lambda self, tag: ''
        with open(real_file, "w") as file:
            yaml.dump(serializable_data, file)

        logging.debug(f"Yaml file written: {file_name}")
    except Exception as e:
        logging.debug(f"Error writing yaml to file: {file_name}")
        raise e


def to_string(self):
    # not sure how to get clean yaml without this:
    yaml.emitter.Emitter.prepare_tag = lambda self, tag: ''
    return yaml.dump(_to_serializable_data(self))


def deserialize_string_list(data, field_name: str):
    strings = []

    if data is not None:
        for value in data:
            if not isinstance(value, str):
                raise TypeError(field_name + " in project configuration is not a string: " + value)
            strings.append(value)

    return strings


def deserialize_string_dictionary(data, field_name: str):
    strings = {}

    if data is not None:
        for key in data.keys():
            if not isinstance(key, str):
                raise TypeError("key in dictionary: " + field_name + " in project configuration is not a string")
            value = data[key]
            if value is None:
                value = ""

            if isinstance(value, int):
                value = value.__str__()
            if isinstance(value, float):
                value = value.__str__()
            if not isinstance(value, str):
                raise TypeError("value in dictionary: " + field_name + " for key: "
                                + key + " in project configuration is not a string")
            strings[key] = value

    return strings

