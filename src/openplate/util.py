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
def str_to_bool(value: str) -> bool:
    """
    Converts a string to a boolean.
    Accepts: 'y', 'yes', 't', 'true', 'on', '1' as True;
             'n', 'no', 'f', 'false', 'off', '0' as False.
    Raises ValueError for anything else.
    """
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        raise ValueError(f"Invalid type: {type(value)}")
    value = value.strip().lower()
    true_set = {'y', 'yes', 't', 'true', 'on', '1'}
    false_set = {'n', 'no', 'f', 'false', 'off', '0'}
    if value in true_set:
        return True
    if value in false_set:
        return False
    raise ValueError(f"Invalid truth value: {value}")