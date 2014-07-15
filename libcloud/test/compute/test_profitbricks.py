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

    ''' Server Function Tests
    '''
    def test_list_nodes(self):
        nodes = self.driver.list_nodes()

        self.assertEqual(len(nodes), 3)

        node = nodes[0]
        self.assertEquals(node.id,"c8e57d7b-e731-46ad-a913-1828c0562246")
        self.assertEquals(node.name,"server001")
        self.assertEquals(node.state, 0)
        self.assertEquals(node.public_ips, ['162.254.25.197'])
        self.assertEquals(node.private_ips, ['10.10.108.12', '10.13.198.11'])
        self.assertEquals(node.extra['datacenter_id'], "e1e8ec0d-b47f-4d39-a91b-6e885483c899")
        self.assertEquals(node.extra['datacenter_version'], "5")
        self.assertEquals(node.extra['provisioning_state'], 0)
        self.assertEquals(node.extra['creation_time'], "2014-07-14T20:52:20.839Z")
        self.assertEquals(node.extra['last_modification_time'], "2014-07-14T22:11:09.324Z")
        self.assertEquals(node.extra['os_type'], "LINUX")
        self.assertEquals(node.extra['availability_zone'], "ZONE_1")

    def test_reboot_node(self):
        node = type('Node', (object,), 
            dict(id="c8e57d7b-e731-46ad-a913-1828c0562246"))
        reboot = self.driver.reboot_node(node=node)

        self.assertTrue(reboot)

    def test_ex_stop_node(self):
        node = type('Node', (object,), 
            dict(id="c8e57d7b-e731-46ad-a913-1828c0562246"))
        stop = self.driver.ex_stop_node(node=node)

        self.assertTrue(stop)

    def test_ex_start_node(self):
        node = type('Node', (object,), 
            dict(id="c8e57d7b-e731-46ad-a913-1828c0562246"))
        start = self.driver.ex_start_node(node=node)

        self.assertTrue(start)

    def test_destroy_node(self):
        node = type('Node', (object,), 
            dict(id="c8e57d7b-e731-46ad-a913-1828c0562246"))
        destroy = self.driver.destroy_node(node=node)

        self.assertTrue(destroy)

    def test_ex_update_node(self):
        node = type('Node', (object,), 
            dict(id="c8e57d7b-e731-46ad-a913-1828c0562246"))

        zone = type('ExProfitBricksAvailabilityZone', (object,),
            dict(name="ZONE_2"))

        update = self.driver.ex_update_node(node=node, ram=2048, cores=2, name="server002", availability_zone=zone)

        self.assertTrue(update)

    ''' Volume Function Tests
    '''
    def test_list_volumes(self):
        volumes = self.driver.list_volumes()

        self.assertEqual(len(volumes), 4)

        volume = volumes[0]
        self.assertEquals(volume.id,"453582cf-8d54-4ec8-bc0b-f9962f7fd232")
        self.assertEquals(volume.name,"storage001")
        self.assertEquals(volume.size, 50)
        self.assertEquals(volume.extra['server_id'], "ebee7d83-912b-42f1-9b62-b953351a7e29")
        self.assertEquals(volume.extra['provisioning_state'], 0)
        self.assertEquals(volume.extra['creation_time'], "2014-07-15T03:19:38.252Z")
        self.assertEquals(volume.extra['last_modification_time'], "2014-07-15T03:28:58.724Z")
        self.assertEquals(volume.extra['image_id'], "d2f627c4-0289-11e4-9f63-52540066fee9")
        self.assertEquals(volume.extra['image_name'], "CentOS-6-server-2014-07-01")

    def test_create_volume(self):
        datacenter = type('Datacenter', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        image = type('NodeImage', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        create = self.driver.create_volume(name="StackPointCloudStorage001",
            size=50,ex_datacenter=datacenter,ex_image=image)

        self.assertTrue(create)

    def test_attach_volume_general(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        node = type('Node', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        attach = self.driver.attach_volume(node=node, volume=volume, device=None, bus_type=None)

        self.assertTrue(attach)

    def test_attach_volume_device_defined(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        node = type('Node', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        attach = self.driver.attach_volume(node=node, volume=volume, device=1, bus_type=None)

        self.assertTrue(attach)

    def test_attach_volume_bus_type_defined(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        node = type('Node', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        attach = self.driver.attach_volume(node=node, volume=volume, device=None, bus_type="IDE")

        self.assertTrue(attach)

    def test_attach_volume_options_defined(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        node = type('Node', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        attach = self.driver.attach_volume(node=node, volume=volume, device=1, bus_type="IDE")

        self.assertTrue(attach)

    def test_detach_volume(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        node = type('Node', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        attach = self.driver.detach_volume(node=node, volume=volume)

        self.assertTrue(attach)

    def test_destroy_volume(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        destroy = self.driver.destroy_volume(volume=volume)

        self.assertTrue(destroy)

    def test_update_volume(self):
        volume = type('StorageVolume', (object,), 
            dict(id="8669a69f-2274-4520-b51e-dbdf3986a476"))

        destroy = self.driver.ex_update_volume(volume=volume)

        self.assertTrue(destroy)

    ''' Image Function Tests
    '''
    def test_list_images(self):
        images = self.driver.list_images()

        self.assertEqual(len(images), 3)

        image = images[0]
        self.assertEqual(image.extra['cpu_hotpluggable'], "false")
        self.assertEqual(image.id, "03b6c3e7-f2ad-11e3-a036-52540066fee9")
        self.assertEqual(image.name, "windows-2012-r2-server-2014-06")
        self.assertEqual(image.extra['image_size'], "11264")
        self.assertEqual(image.extra['image_type'], "HDD")
        self.assertEqual(image.extra['memory_hotpluggable'], "false")
        self.assertEqual(image.extra['os_type'], "WINDOWS")
        self.assertEqual(image.extra['public'], "true")
        self.assertEqual(image.extra['region'], "NORTH_AMERICA")
        self.assertEqual(image.extra['writeable'], "true")

    ''' Datacenter Function Tests
    '''
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

    def test_list_locations(self):
        locations = self.driver.list_locations()
        self.assertEqual(len(locations), 2)

        locationNamesResult = list(a.name for a in locations)
        locationNamesExpected = ['NORTH_AMERICA','EUROPE']

        self.assertListEqual(locationNamesResult, locationNamesExpected)

        matchedLocation = next(location for location in locations
                               if location.name == 'NORTH_AMERICA')

    ''' Availability Zone Tests
    '''

    def test_ex_list_availability_zones(self):
        zones = self.driver.ex_list_availability_zones()
        self.assertEqual(len(zones), 3)

        zoneNamesResult = list(a.name for a in zones)
        zoneNamesExpected = ['AUTO', 'ZONE_2','ZONE_1']

        self.assertListEqual(zoneNamesResult, zoneNamesExpected)

        matchedLocation = next(zone for zone in zones
                               if zone.name == 'ZONE_1')

    ''' Interface Tests
    '''

    def test_ex_list_interfaces(self):
        interfaces = self.driver.ex_list_network_interfaces()

        self.assertEqual(len(interfaces), 3)

        interface = interfaces[0]
        self.assertEquals(interface.id,"6b38a4f3-b851-4614-9e3a-5ddff4727727")
        self.assertEquals(interface.name, "StackPointCloud")
        self.assertEquals(interface.state, 0)
        self.assertEquals(interface.extra['server_id'], "234f0cf9-1efc-4ade-b829-036456584116")
        self.assertEquals(interface.extra['lan_id'], '3')
        self.assertEquals(interface.extra['internet_access'], 'false')
        self.assertEquals(interface.extra['mac_address'], "02:01:40:47:90:04")
        self.assertEquals(interface.extra['dhcp_active'], "true")
        self.assertEquals(interface.extra['gateway_ip'], None)                 
        self.assertEquals(interface.extra['ips'], ['10.14.96.11', '10.14.96.11', '10.14.96.11'])

    def test_ex_create_network_interface(self):
        node = type('Node', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        attach = self.driver.ex_create_network_interface(node=node)

        self.assertTrue(attach)

    def test_ex_destroy_network_interface(self):
        network_interface = type('ProfitBricksNetworkInterface', (object,),
            dict(id="cd59b162-0289-11e4-9f63-52540066fee9"))
        
        destroy = self.driver.ex_destroy_network_interface(
            network_interface=network_interface)

        self.assertTrue(destroy)

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

    def _1_2_getAllImages(self, method, url, body, headers):
        body = self.fixtures.load('list_images.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_getAllServers(self, method, url, body, headers):
        body = self.fixtures.load('list_nodes.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_resetServer(self, method, url, body, headers):
        body = self.fixtures.load('reboot_node.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_stopServer(self, method, url, body, headers):
        body = self.fixtures.load('ex_stop_node.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_startServer(self, method, url, body, headers):
        body = self.fixtures.load('ex_start_node.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_deleteServer(self, method, url, body, headers):
        body = self.fixtures.load('destroy_node.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_getAllStorages(self, method, url, body, headers):
        body = self.fixtures.load('list_volumes.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_createStorage(self, method, url, body, headers):
        body = self.fixtures.load('create_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_connectStorageToServer(self, method, url, body, headers):
        body = self.fixtures.load('attach_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_disconnectStorageFromServer(self, method, url, body, headers):
        body = self.fixtures.load('detach_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_deleteStorage(self, method, url, body, headers):
        body = self.fixtures.load('destroy_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_updateStorage(self, method, url, body, headers):
        body = self.fixtures.load('ex_update_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_updateServer(self, method, url, body, headers):
        body = self.fixtures.load('ex_update_node.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_getAllNic(self, method, url, body, headers):
        body = self.fixtures.load('ex_list_network_interfaces.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_createNic(self, method, url, body, headers):
        body = self.fixtures.load('ex_list_network_interfaces.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _1_2_deleteNic(self, method, url, body, headers):
        body = self.fixtures.load('ex_destroy_network_interface.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())