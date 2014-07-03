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
import httplib

from libcloud.compute.providers import Provider
from libcloud.common.base import ConnectionUserAndKey
from libcloud.compute.base import Node, NodeDriver, NodeLocation, NodeSize
from libcloud.compute.base import NodeImage, StorageVolume
from libcloud.compute.base import KeyPair
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

class ProfitBricksResponse(]):
    """
    Response class for ProfitBricks driver.
    """
    defaultExceptionCls = ProfitBricksException
    exceptions = {
    }

class ProfitBricksConnection(ConnectionUserAndKey):
    responseCls = ProfitBricksResponse  
    host = 'api.profitbricks.com/1.2'
    endpoint = '/1.2'

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
        'SHUTDOWN': NodeState.PENDING
        'SHUTOFF': NodeState.STOPPED,
        'CRASHED': NodeState.STOPPED,
    }

    """ Core Functions    
    """

    def list_sizes(self):
        return

    def list_images(self, location=None):
        return

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

    def ex_create_datacenter(self):
        return

    def ex_destroy_datacenter(self):
        return

    def ex_describe_datacenter(self):
        return

    def ex_list_datacenters(self):
        return

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
