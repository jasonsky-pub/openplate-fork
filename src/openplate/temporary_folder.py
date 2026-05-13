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
import os
import shutil
import stat
import tempfile
import uuid


class TemporaryFolder:

    def __enter__(self):
        self._folder_path = os.path.join(tempfile.gettempdir(), uuid.uuid4().__str__())
        logging.debug(f"Creating Temporary Folder: {self._folder_path}")
        os.mkdir(self._folder_path)
        return self

    def remove_sub_path(self, sub_path):
        logging.debug(f"Removing sub-path on folder: {self._folder_path}, sub_path: {sub_path}")
        newPath = os.path.join(self._folder_path, sub_path)
        shutil.rmtree(newPath, onerror=on_rm_error)

    def __exit__(self, exception_type, exception_value, traceback):
        logging.debug(f"Cleaning up Source from folder: {self._folder_path}")
        shutil.rmtree(self._folder_path, onerror=on_rm_error)

    def folder_path(self):
        return self._folder_path


# Due to the problem where some Source control files are readonly
# need to mark writable before deleting on some OSs
def on_rm_error(func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)
