#!/bin/bash

##
##              Copyright 2025 Comcast Cable Communications Management, LLC
##
##              Licensed under the Apache License, Version 2.0 (the "License");
##              you may not use this file except in compliance with the License.
##              You may obtain a copy of the License at
##
##              http://www.apache.org/licenses/LICENSE-2.0
##
##              Unless required by applicable law or agreed to in writing, software
##              distributed under the License is distributed on an "AS IS" BASIS,
##              WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##              See the License for the specific language governing permissions and
##              limitations under the License.
##
##              SPDX-License-Identifier: Apache-2.0
##
##              This product includes software developed at Comcast (https://www.comcast.com/).##


# Install the licenseheaders package if not already installed. Please install them manually
# pip install --quiet licenseheaders

# Add license headers using the LICENSE file in the root directory for python files
python -m licenseheaders -t ../NOTICE -d .. --ext py


# Add license headers using the LICENSE file in the root directory for docker files
python -m licenseheaders -t ../NOTICE -d .. --ext Dockerfile

# Add license headers using the LICENSE file in the root directory for YAML files
python -m licenseheaders -t ../NOTICE --ext .yaml -d ..

# Add license headers using the LICENSE file in the root directory for yml files
python -m licenseheaders -t ../NOTICE --ext .yml -d ..

# Add license headers using the LICENSE file in the root directory for sh files
python -m licenseheaders -t ../NOTICE --ext .sh -d ..