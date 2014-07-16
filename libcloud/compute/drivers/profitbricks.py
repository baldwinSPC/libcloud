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
import copy
from xml.etree.ElementTree import tostring

from libcloud.utils.networking import is_private_subnet
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

        print('REQUEST')
        print xml.dom.minidom.parseString(tostring(soap_env)).toprettyxml(indent='    ')
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

class ProfitBricksNetworkInterface(object):
    def __init__(self, id, name, state, extra=None):
        self.id = id
        self.name = name
        self.state = state
        self.extra = extra or {}

    def __repr__(self):
        return (('<ProfitBricksNetworkInterface: id=%s, name=%s')
                % (self.id, self.name))

class ExProfitBricksAvailabilityZone(object):
    """
    Extension class which stores information about a ProfitBricks 
    availability zone.

    Note: This class is ProfitBricks specific.
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return (('<ExProfitBricksAvailabilityZone: name=%s>')
                % (self.name))

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

    REGIONS = {
        '1': {'region': 'NORTH_AMERICA','country': 'USA'},
        '2': {'region': 'EUROPE', 'country': 'DEU'},
    }

    AVAILABILITY_ZONE = {
        '1': {'name': 'AUTO'},
        '2': {'name': 'ZONE_1'},
        '3': {'name': 'ZONE_2'},
    }

    """ Core Functions    
    """

    def list_sizes(self):
        return

    def list_images(self, region=None):
        '''
        :keyword     region: Filter the list by region. (optional)
        :type        region:  ``str``
        '''

        action = 'getAllImages'
        body = {'action': action}

        return self._to_images(self.connection.request(action=action,data=body,method='POST').object, region)

    def list_locations(self):
        locations = []

        for key, values in self.REGIONS.items():
            location = self._to_location(copy.deepcopy(values))
            locations.append(location)

        return locations

    def list_nodes(self):
        action = 'getAllServers'
        body = {'action': action}

        return self._to_nodes(self.connection.request(action=action,data=body,method='POST').object)

    def reboot_node(self, node=None):
        action = 'resetServer'
        body = {'action': action,
                'serverId': node.id
                }

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def create_node(self, ex_cloud_service_name=None, **kwargs):
        return

    def destroy_node(self, node, remove_attached_disks=None):
        action = 'deleteServer'
        body = {'action': action,
                'serverId': node.id
                }

        self.connection.request(action=action,data=body,method='POST').object

        return True

    """ Volume Functions
    """

    def list_volumes(self, node=None):
        action = 'getAllStorages'
        body = {'action': action}

        return self._to_volumes(self.connection.request(action=action,data=body,method='POST').object)

    def attach_volume(self, node, volume, device=None, bus_type=None):
        action = 'connectStorageToServer'
        body = {'action': action,
                'request': 'true',
                'storageId': volume.id,
                'serverId': node.id,
                'busType': bus_type,
                'deviceNumber': str(device)
                }

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def create_volume(self, name, size, ex_datacenter=None, ex_image=None, ex_password=None):
        action = 'createStorage'
        body = {'action': action,
                'request': 'true',
                'size': str(size),
                'storageName': name,
                'mountImageId': ex_image.id,
                'dataCenterId': ex_datacenter.id
                }

        if ex_password:
            body['profitBricksImagePassword'] = ex_password

        return self._to_volumes(self.connection.request(action=action,data=body,method='POST').object)

    def detach_volume(self, node, volume):
        action = 'disconnectStorageFromServer'
        body = {'action': action,
                'storageId': volume.id,
                'serverId': node.id
                }

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def destroy_volume(self, volume):
        action = 'deleteStorage'
        body = {'action': action,
                'storageId': volume.id}

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def ex_update_volume(self, volume, storage_name=None, size=None):
        action = 'updateStorage'
        body = {'action': action,
                'request': 'true',
                'storageId': volume.id
                }

        if storage_name:
            body['storageName'] = storage_name
        if size:
            body['size'] = str(size)

        self.connection.request(action=action,data=body,method='POST').object
        
        return True

    """ Extension Functions
    """
    ''' Server Extension Functions
    '''
    def ex_stop_node(self, node):
        action = 'stopServer'
        body = {'action': action,
                'serverId': node.id
                }

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def ex_start_node(self, node):
        action = 'startServer'
        body = {'action': action,
                'serverId': node.id
                }

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def ex_list_availability_zones(self):
        availability_zones = []

        for key, values in self.AVAILABILITY_ZONE.items():
            name = copy.deepcopy(values)["name"]

            availability_zone = ExProfitBricksAvailabilityZone(
                name=name
            )
            availability_zones.append(availability_zone)

        return availability_zones

    def ex_get_node(self, node):
        return

    def ex_update_node(self, node, name=None, cores=None, 
        ram=None, availability_zone=None):
        action = 'updateServer'

        body = {'action': action,
                'request': 'true',
                'serverId': node.id
                }

        if name:
            body['serverName'] = name

        if cores:
            body['cores'] = str(cores)

        if ram:
            body['ram'] = str(ram)

        if availability_zone:
            body['availabilityZone'] = availability_zone.name

        self.connection.request(action=action,data=body,method='POST').object

        return True

    ''' Datacenter Extension Functions
    '''

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

        return True

    def ex_clear_datacenter(self, datacenter):
        action = 'clearDataCenter'
        body = {'action': action,
                'dataCenterId': datacenter.id
                }

        self.connection.request(action=action,data=body,method='POST').object
        
        return True

    ''' Network Interface Extension Functions
    '''

    def ex_list_network_interfaces(self):
        action = 'getAllNic'
        body = {'action': action}

        return self._to_interfaces(self.connection.request(action=action,data=body,method='POST').object)

    def ex_describe_network_interface(self):
        return

    def ex_create_network_interface(self, node, 
        lan_id=None, ip=None, nic_name=None, dhcp_active=True):
        action = 'createNic'
        body = {'action': action,
                'request': 'true',
                'serverId': node.id,
                'dhcpActive': str(dhcp_active)
                }

        if lan_id:
            body['lanId'] = str(lan_id)
        else:
            body['lanId'] = str(1)

        if ip:
            body['ip'] = ip

        if nic_name:
            body['nicName'] = nic_name

        return self._to_interfaces(self.connection.request(action=action,data=body,method='POST').object)

    def ex_update_network_interface(self, network_interface, name=None, 
        lan_id=None, ip=None, dhcp_active=None):
        action = 'updateNic'
        body = {'action': action,
                'request': 'true',
                'nicId': network_interface.id
                }

        if name:
            body['nicName'] = name

        if lan_id:
            body['lanId'] = str(lan_id)

        if ip:
            body['ip'] = ip

        if dhcp_active is not None:
            body['dhcpActive'] = str(dhcp_active).lower()

        self.connection.request(action=action,data=body,method='POST').object

        return True

    def ex_destroy_network_interface(self, network_interface):
        action = 'deleteNic'
        body = {'action': action,
                'nicId': network_interface.id}

        self.connection.request(action=action,data=body,method='POST').object

        return True

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

    def _to_images(self, object, region=None):
        return [self._to_image(image, region) for image in object.findall('.//return')]

    def _to_image(self, image, region=None):
        elements = list(image.iter())
        image_id = elements[0].find('imageId').text
        image_name = elements[0].find('imageName').text
        image_size = elements[0].find('imageSize').text
        image_type = elements[0].find('imageType').text
        cpu_hotpluggable = elements[0].find('cpuHotpluggable').text
        memory_hotpluggable = elements[0].find('memoryHotpluggable').text
        os_type = elements[0].find('osType').text
        public = elements[0].find('public').text
        image_region = elements[0].find('region').text
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
                                'region': image_region,
                                'writeable': writeable
                            }
                        )

    def _to_nodes(self, object):
        return [self._to_node(n) for n in object.findall('.//return')]

    def _to_node(self, node):
        """
        Convert the request into a node Node
        """
        elements = list(node.iter())
        datacenter_id = elements[0].find('dataCenterId').text
        datacenter_version = elements[0].find('dataCenterVersion').text
        node_id = elements[0].find('serverId').text
        node_name = elements[0].find('serverName').text
        cores = elements[0].find('cores').text
        ram = elements[0].find('ram').text
        internet_access = elements[0].find('internetAccess').text
        provisioning_state = elements[0].find('provisioningState').text
        virtual_machine_state = elements[0].find('virtualMachineState').text
        creation_time = elements[0].find('creationTime').text
        last_modification_time = elements[0].find('lastModificationTime').text
        os_type = elements[0].find('osType').text
        availability_zone = elements[0].find('availabilityZone').text

        public_ips = []
        private_ips = []

        if ET.iselement(elements[0].find('nics')):
            for nic in elements[0].findall('.//nics'):
                n_elements = list(nic.iter())
                if ET.iselement(n_elements[0].find('ips')):
                    ip = n_elements[0].find('ips').text
                    if is_private_subnet(ip):
                        private_ips.append(ip)
                    else:
                        public_ips.append(ip)

        return Node(
            id=node_id,
            name=node_name,
            state=self.NODE_STATE_MAP.get(
                virtual_machine_state, NodeState.UNKNOWN),
            public_ips=public_ips,
            private_ips=private_ips,
            driver=self.connection.driver,
            extra={
                'datacenter_id': datacenter_id,
                'datacenter_version': datacenter_version,
                'provisioning_state': self.PROVISIONING_STATE.get(
                    provisioning_state, NodeState.UNKNOWN),
                'creation_time': creation_time,
                'last_modification_time': last_modification_time,
                'os_type': os_type,
                'availability_zone': availability_zone})

    def _to_volumes(self, object):
        return [self._to_volume(volume) for volume in object.findall('.//return')]

    def _to_volume(self, volume, node=None):
        elements = list(volume.iter())

        if node:
            if node.id == elements[0].find('server_id').text:
                print('Filtering by nodeid ' + node.id)

        datacenter_id = elements[0].find('dataCenterId').text
        datacenter_version = elements[0].find('dataCenterVersion').text
        storage_id = elements[0].find('storageId').text

        if ET.iselement(elements[0].find('storageName')):
            storage_name = elements[0].find('storageName').text
        else:
            storage_name = None

        if ET.iselement(elements[0].find('serverIds')):
            server_id = elements[0].find('serverIds').text
        else:
            server_id = None

        if ET.iselement(elements[0].find('creationTime')):
            creation_time = elements[0].find('creationTime').text
        else:
            creation_time = None

        if ET.iselement(elements[0].find('lastModificationTime')):
            last_modification_time = elements[0].find('lastModificationTime').text
        else:
            last_modification_time = None

        if ET.iselement(elements[0].find('provisioningState')):
            provisioning_state = elements[0].find('provisioningState').text
        else:
            provisioning_state = None

        if ET.iselement(elements[0].find('size')):
            size = elements[0].find('size').text
        else:
            size = 0

        if ET.iselement(elements[0].find('mountImage')):
            image_id = elements[0].find('mountImage')[0].text
        else:
            image_id = None

        if ET.iselement(elements[0].find('mountImage')):
            image_name = elements[0].find('mountImage')[1].text
        else:
            image_name = None

        return StorageVolume(id=storage_id, 
                            name=storage_name,
                            size=int(size), 
                            driver=self.connection.driver,
                            extra={
                                    'creation_time': creation_time,
                                    'last_modification_time': last_modification_time,
                                    'provisioning_state': self.PROVISIONING_STATE.get(
                                        provisioning_state, NodeState.UNKNOWN),
                                    'server_id': server_id,
                                    'image_id': image_id,
                                    'image_name': image_name
                                }
                            )

    def _to_interfaces(self, object):
        return [self._to_interface(interface) for interface in object.findall('.//return')]

    def _to_interface(self, interface):
        elements = list(interface.iter())

        nic_id = elements[0].find('nicId').text
        
        if ET.iselement(elements[0].find('nicName')):
            nic_name = elements[0].find('nicName').text
        else:
            nic_name = None

        if ET.iselement(elements[0].find('serverId')):
            server_id = elements[0].find('serverId').text
        else:
            server_id = None

        if ET.iselement(elements[0].find('lanId')):
            lan_id = elements[0].find('lanId').text
        else:
            lan_id = None

        if ET.iselement(elements[0].find('internetAccess')):
            internet_access = elements[0].find('internetAccess').text
        else:
            internet_access = None

        if ET.iselement(elements[0].find('macAddress')):
            mac_address = elements[0].find('macAddress').text
        else:
            mac_address = None

        if ET.iselement(elements[0].find('dhcpActive')):
            dhcp_active = elements[0].find('dhcpActive').text
        else:
            dhcp_active = None

        if ET.iselement(elements[0].find('gatewayIp')):
            gateway_ip = elements[0].find('gatewayIp').text
        else:
            gateway_ip = None

        if ET.iselement(elements[0].find('provisioningState')):
            provisioning_state = elements[0].find('provisioningState').text
        else:
            provisioning_state = None

        ips = []

        if ET.iselement(elements[0].find('ips')):
            for ip in elements[0].findall('.//ips'):
                ip = elements[0].find('ips').text
                ips.append(ip)
                
        return ProfitBricksNetworkInterface(id=nic_id, 
                            name=nic_name,
                            state=self.PROVISIONING_STATE.get(
                                        provisioning_state, NodeState.UNKNOWN),
                            extra={
                                    'server_id': server_id,
                                    'lan_id': lan_id,
                                    'internet_access': internet_access,
                                    'mac_address': mac_address,
                                    'dhcp_active': dhcp_active,
                                    'gateway_ip': gateway_ip,
                                    'ips': ips
                                }
                            )

    def _to_location(self, data):

        return NodeLocation(
            id=data["region"],
            name=data["region"],
            country=data["country"],
            driver=self.connection.driver)