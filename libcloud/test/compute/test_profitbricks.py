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

    USER_ID = 'user@profitbricks.com'
    KEY = 'password' #empty file is fine

    def setUp(self):
        ProfitBricks = get_driver(Provider.PROFIT_BRICKS)
        ProfitBricks.connectionCls.conn_classes = (None, ProfitBricksMockHttp)
        self.driver = ProfitBricks(self.USER_ID, self.KEY )

    def test_ex_create_datacenter(self):
    	datacenter = self.driver.ex_create_datacenter(name="StackPointCloud")

    	self.assertEqual(datacenter[0].id, '625f3dc8-4061-422d-b633-9efebe4344d9')
    	self.assertEqual(datacenter[0].extra['region'], 'EUROPE')
    	self.assertEqual(datacenter[0].datacenter_version, '1')

    def test_ex_destroy_datacenter(self):
    	datacenter = type('Datacenter', (object,),
    		dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))
    	destroy = self.driver.ex_destroy_datacenter(datacenter=datacenter)

    	self.assertTrue(destroy)

    def test_ex_describe_datacenter(self):
    	datacenter = type('Datacenter', (object,),
    		dict(id="d96dfafc-9a8c-4c0e-8a0c-857a15db572d"))
    	describe = self.driver.ex_describe_datacenter(datacenter=datacenter)

    	self.assertEqual(describe[0].id, 'd96dfafc-9a8c-4c0e-8a0c-857a15db572d')
    	self.assertEqual(describe[0].name, 'StackPointCloud')
    	self.assertEqual(describe[0].datacenter_version, '1')
    	self.assertEqual(describe[0].extra['region'], 'NORTH_AMERICA')
    	self.assertEqual(describe[0].extra['provisioning_state'], 'AVAILABLE')

    def test_ex_clear_datacenter(self):
    	datacenter = type('Datacenter', (object,), 
    		dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))
        clear = self.driver.ex_clear_datacenter(datacenter=datacenter)

        self.assertTrue(clear)

    def test_ex_list_datacenters(self):
    	datacenters = self.driver.ex_list_datacenters()

        self.assertEqual(len(datacenters), 3)

        dc1 = datacenters[0]
        self.assertEquals(dc1.id,"6571ecd4-8602-4692-ae14-2f85eedbc403")
        self.assertEquals(dc1.name,"StackPointCloud")
        self.assertEquals(dc1.datacenter_version,"1")

    def test_ex_update_datacenter(self):
    	datacenter = type('Datacenter', (object,),
    		dict(id="d96dfafc-9a8c-4c0e-8a0c-857a15db572d"))

    	update = self.driver.ex_update_datacenter(datacenter=datacenter,
    		name="StackPointCloud")

    	self.assertTrue(update)

class ProfitBricksMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('profitbricks')

    def _1_2_clearDataCenter(self, method, url, body, headers):
        body = self.fixtures.load('ex_clear_datacenter.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_createDataCenter(self, method, url, body, headers):
        body = self.fixtures.load('ex_create_datacenter.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_deleteDataCenter(self, method, url, body, headers):
        body = self.fixtures.load('ex_destroy_datacenter.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_getDataCenter(self, method, url, body, headers):
        body = self.fixtures.load('ex_describe_datacenter.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_getAllDataCenters(self, method, url, body, headers):
    	body = self.fixtures.load('ex_list_datacenters.xml')
    	return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_updateDataCenter(self, method, url, body, headers):
    	body = self.fixtures.load('ex_update_datacenter.xml')
    	return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())