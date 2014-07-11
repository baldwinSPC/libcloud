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
"""ProfitBricks Compute driver

"""
# TODO:
# - add exception and success responses

import httplib
import base64
import xml.etree.ElementTree as ET
import xml.dom.minidom
import json
from xml.etree.ElementTree import tostring

from libcloud.utils.py3 import urlparse, b
from libcloud.compute.providers import Provider
from libcloud.common.base import ConnectionUserAndKey, XmlResponse, Response
from libcloud.compute.base import Node, NodeDriver, NodeLocation, NodeSize
from libcloud.compute.base import NodeImage, StorageVolume
from libcloud.compute.base import KeyPair, UuidMixin
from libcloud.compute.types import NodeState
from libcloud.common.types import LibcloudError

__version__ = '1.0.0'

"""
ProfitBricks is unique in that they allow the user to define all aspects
of the instance size, i.e. disk size, core size, and memory size. 

These are instance types that match up with what other providers support.

You can configure disk size, core size, and memory size using the ex_
parameters on the create_node method. 
"""
PROFITBRICKS_COMPUTE_INSTANCE_TYPES = {
    'A0': {
        'id': 'A0',
        'name': 'ExtraSmall Instance',
        'ram': 768,
        'disk': 127,
        'bandwidth': None,
        'price': '0.02',
        'max_data_disks': 1,
        'cores': 'Shared'
    },
    'A1': {
        'id': 'A1',
        'name': 'Small Instance',
        'ram': 1792,
        'disk': 127,
        'bandwidth': None,
        'price': '0.09',
        'max_data_disks': 2,
        'cores': 1
    },
    'A2': {
        'id': 'A2',
        'name': 'Medium Instance',
        'ram': 3584,
        'disk': 127,
        'bandwidth': None,
        'price': '0.18',
        'max_data_disks': 4,
        'cores': 2
    },
    'A3': {
        'id': 'A3',
        'name': 'Large Instance',
        'ram': 7168,
        'disk': 127,
        'bandwidth': None,
        'price': '0.36',
        'max_data_disks': 8,
        'cores': 4
    },
    'A4': {
        'id': 'A4',
        'name': 'ExtraLarge Instance',
        'ram': 14336,
        'disk': 127,
        'bandwidth': None,
        'price': '0.72',
        'max_data_disks': 16,
        'cores': 8
    },
    'A5': {
        'id': 'A5',
        'name': 'Memory Intensive Instance',
        'ram': 14336,
        'disk': 127,
        'bandwidth': None,
        'price': '0.40',
        'max_data_disks': 4,
        'cores': 2
    },
    'A6': {
        'id': 'A6',
        'name': 'A6 Instance',
        'ram': 28672,
        'disk': 127,
        'bandwidth': None,
        'price': '0.80',
        'max_data_disks': 8,
        'cores': 4
    },
    'A7': {
        'id': 'A7',
        'name': 'A7 Instance',
        'ram': 57344,
        'disk': 127,
        'bandwidth': None,
        'price': '1.60',
        'max_data_disks': 16,
        'cores': 8
    }    
}

DATACENTER_REGIONS= {
    'NORTH_AMERICA': {'country': 'USA'},
    'EUROPE': {'country': 'DEU'},
}

class ProfitBricksException(LibcloudError):
    """
    Exception class for ProfitBricks driver.
    """
    pass

class ProfitBricksResponse():
    """
    Response class for ProfitBricks driver.
    """
    defaultExceptionCls = ProfitBricksException
    exceptions = {
    }

class ProfitBricksConnection(ConnectionUserAndKey):
    host = 'api.profitbricks.com'
    responseCls = XmlResponse
    api_prefix = '/1.2/' # https://api.profitbricks.com/1.2


    def add_default_headers(self, headers):
        headers['Content-Type'] = 'text/xml'
        headers['Authorization'] = 'Basic %s' % (base64.b64encode(
            b('%s:%s' % (self.user_id, self.key))).decode('utf-8'))

        return headers

    def encode_data(self, data):
        soap_env = ET.Element('soapenv:Envelope',{
            'xmlns:soapenv' : 'http://schemas.xmlsoap.org/soap/envelope/',
            'xmlns:ws' : 'http://ws.api.profitbricks.com/'
            })
        soap_header = ET.SubElement(soap_env, 'soapenv:Header')
        soap_body = ET.SubElement(soap_env, 'soapenv:Body')
        soap_req_body = ET.SubElement(soap_body, 'ws:' + data['action'] + '' )

        if 'request' in data.keys():
            soap_req_body = ET.SubElement(soap_req_body, 'request')
            for key, value in data.iteritems():
                if not (key == 'action' or key == 'request'):
                    child = ET.SubElement(soap_req_body, key)
                    child.text = value
        else:
            for key, value in data.iteritems():
                if not (key == 'action'):
                    child = ET.SubElement(soap_req_body, key)
                    child.text = value

        #print xml.dom.minidom.parseString(tostring(soap_env)).toprettyxml(indent='    ')
        soap_post = ET.tostring(soap_env)

        return soap_post

    def request(self, action, params=None, data=None, headers=None,
                method='POST', raw=False):
        action = self.api_prefix + action

        return super(ProfitBricksConnection, self).request(action=action,
                                                              params=params,
                                                              data=data,
                                                              headers=headers,
                                                              method=method,
                                                              raw=raw)

class Datacenter(UuidMixin):
    """ Datacenter Ojbect
    """
    def __init__(self, id, name, datacenter_version, driver, extra=None):
        """
        :param id: Datacenter ID.
        :type id: ``str``

        :param name: Datacenter name.
        :type name: ``str``

        :param datacenter_version: Datacenter version.
        : type datacenter_version: ``str``

        :param driver: Driver this image belongs to.
        :type driver: :class:`.NodeDriver`
        """
        self.id = str(id)
        if name is None:
            self.name = None
        else:
            self.name = name
        #self.name = name
        self.datacenter_version = datacenter_version
        self.driver = driver
        self.extra = extra or {}
        UuidMixin.__init__(self)

    def __repr__(self):
        return (('<Datacenter: id=%s, name=%s, datacenter_version=%s, driver=%s> ...>')
                % (self.id, self.name, self.datacenter_version, self.driver.name))

class ProfitBricksNodeDriver(NodeDriver):
    connectionCls = ProfitBricksConnection
    name = "ProfitBricks Node Provider"
    website = 'http://profitbricks.com'
    type = Provider.PROFIT_BRICKS
    _instance_types = PROFITBRICKS_COMPUTE_INSTANCE_TYPES

    PROVISIONING_STATE = {
        'INACTIVE': NodeState.PENDING,
        'INPROCESS': NodeState.PENDING,
        'AVAILABLE': NodeState.RUNNING,
        'DELETED': NodeState.TERMINATED,
    }

    NODE_STATE_MAP = {
        'NOSTATE': NodeState.UNKNOWN,
        'RUNNING': NodeState.RUNNING,
        'BLOCKED': NodeState.STOPPED,
        'PAUSE': NodeState.STOPPED,
        'SHUTDOWN': NodeState.PENDING,
        'SHUTOFF': NodeState.STOPPED,
        'CRASHED': NodeState.STOPPED,
    }

    """ Core Functions    
    """

    def list_sizes(self):
        return

    def list_images(self, location=None):
        action = 'getAllImages'
        body = {'action': action}

        # xml ='''
        # <soapenv:Envelope \
        # xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' \
        # xmlns:ws='http://ws.api.profitbricks.com/'>               \
        # <soapenv:Header />           \
        # <soapenv:Body>               \
        # <ws:getAllImages /> \
        # </soapenv:Body>              \
        # </soapenv:Envelope>              \
        # '''

        return self._to_images(self.connection.request(action=action,data=body,method='POST').object)

    def list_locations(self):
        return

    def list_nodes(self, ex_cloud_service_name=None):
        return

    def reboot_node(self, node=None, ex_cloud_service_name=None,
                    ex_deployment_slot=None):
        return

    def create_node(self, ex_cloud_service_name=None, **kwargs):
        return

    def destroy_node(self, node=None, ex_cloud_service_name=None,
                     ex_deployment_slot=None):
        return

    """ Volume Functions
    """

    def list_volumes(self, node=None):
        return

    def attach_volume(self):
        raise NotImplementedError(
            'attach_volume is not supported '
            'at this time.')

    def create_volume(self):
        raise NotImplementedError(
            'create_volume is not supported '
            'at this time.')

    def detach_volume(self):
        raise NotImplementedError(
            'detach_volume is not supported '
            'at this time.')

    def destroy_volume(self):
        raise NotImplementedError(
            'destroy_volume is not supported '
            'at this time.')

    """ Extension Methods
    """

    def ex_stop_node(self, node):
        return True

    def ex_start_node(self, node):
        return True

    def ex_create_datacenter(self, name, region="DEFAULT"):
        action = 'createDataCenter'

        body = {'action': action,
                'dataCenterName': name,
                'region': region.upper()
                }        

        if not name:
            raise ValueError("You must provide a datacenter name.")

        return self._to_datacenters(self.connection.request(action=action,data=body,method='POST').object)

    def ex_destroy_datacenter(self, datacenter):
        action = 'deleteDataCenter'
        body = {'action': action,
                'dataCenterId': datacenter.id
                }

        request = self.connection.request(action=action,data=body,method='POST').object

        return True

    def ex_describe_datacenter(self, datacenter):
        action = 'getDataCenter'
        body = {'action': action,
                'dataCenterId': datacenter.id
                }
        
        return self._to_datacenters(self.connection.request(action=action,data=body,method='POST').object)

    def ex_list_datacenters(self):
        action = 'getAllDataCenters'
        body = {'action': action}

        return self._to_datacenters(self.connection.request(action=action,data=body,method='POST').object)

    def ex_update_datacenter(self, datacenter, name):
        action = 'updateDataCenter'
        body = {'action': action,
                'request': 'true',
                'dataCenterId': datacenter.id,
                'dataCenterName': name
                }

        request = self.connection.request(action=action,data=body,method='POST').object

        return

    def ex_clear_datacenter(self, datacenter):
        action = 'clearDataCenter'
        body = {'action': action,
                'dataCenterId': datacenter.id
                }

        request = self.connection.request(action=action,data=body,method='POST').object
        
        return True

    def ex_list_network_interfaces(self):
        return

    def ex_describe_network_interface(self):
        return

    def ex_create_network_interface(self):
        return

    def ex_update_network_interface(self):
        return

    def ex_destroy_network_interface(self):
        return

    """ Snapshot Functions Not Implemented
    """
    def create_volume_snapshot(self):
        raise NotImplementedError(
            'While supported, this is '
            'not implemented at this time.')

    """Private Functions
    """

    def _to_datacenters(self, object):
        return [self._to_datacenter(datacenter) for datacenter in object.findall('.//return')]

    def _to_datacenter(self, datacenter):
        elements = list(datacenter.iter())
        datacenter_id = elements[0].find('dataCenterId').text
        if ET.iselement(elements[0].find('dataCenterName')):
            datacenter_name = elements[0].find('dataCenterName').text
        else:
            datacenter_name = None
        datacenter_version = elements[0].find('dataCenterVersion').text
        if ET.iselement(elements[0].find('provisioningState')):
            provisioning_state = elements[0].find('provisioningState').text
        else:
            provisioning_state = None
        if ET.iselement(elements[0].find('region')):
            region = elements[0].find('region').text
        else:
            region = None

        return Datacenter(id=datacenter_id,
                        name=datacenter_name,
                        datacenter_version=datacenter_version,
                        driver=self.connection.driver,
                        extra={
                            'provisioning_state': provisioning_state,
                            'region': region}
                        )

    def _to_images(self, object):
        return [self._to_image(image) for image in object.findall('.//return')]

    def _to_image(self, image):
        elements = list(image.iter())
        image_id = elements[0].find('imageId').text
        image_name = elements[0].find('imageName').text
        image_size = elements[0].find('imageSize').text
        image_type = elements[0].find('imageType').text
        cpu_hotpluggable = elements[0].find('cpuHotpluggable').text
        memory_hotpluggable = elements[0].find('memoryHotpluggable').text
        os_type = elements[0].find('osType').text
        public = elements[0].find('public').text
        region = elements[0].find('region').text
        writeable = elements[0].find('writeable').text

        return NodeImage(id=image_id,
                        name=image_name,
                        driver=self.connection.driver,
                        extra={
                                'image_size': image_size,
                                'image_type': image_type,
                                'cpu_hotpluggable': cpu_hotpluggable,
                                'memory_hotpluggable': memory_hotpluggable,
                                'os_type': os_type,
                                'public': public,
                                'region': region,
                                'writeable': writeable
                            }
                        )