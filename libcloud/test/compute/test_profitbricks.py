# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import httplib
import unittest
import libcloud.security

import libcloud

from libcloud.common.types import LibcloudError
from libcloud.compute.base import NodeAuthPassword
from libcloud.test import MockHttp
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

class ProfitBricksNodeDriver(unittest.TestCase) :

    #required otherwise we get client side SSL verification
    libcloud.security.VERIFY_SSL_CERT = False

    USER_ID = '3761b98b-673d-526c-8d55-fee918758e6e'
    KEY = 'fixtures/azure/libcloud.pem' #empty file is fine

    def setUp(self):
        ProfitBricks = get_driver(Provider.AZURE)
        ProfitBricks.connectionCls.conn_classes = (None, ProfitBricksMockHttp)
        self.driver = ProfitBricks(self.USER_ID, self.KEY )