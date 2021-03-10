
from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get, napalm_cli
from nornir_netmiko.tasks import netmiko_send_command
from genie.conf import Genie

from modules.utils import pj, wr_to_json, readYAML
from gather_processors import PrintResult, SaveResultToDict

from pprint import pprint as pp


FILE = 'host_files/inventory.yaml'
genie_devices = Genie.init(FILE)

nr = InitNornir("files/config.yaml")
nx_nr = InitNornir("files/config.yaml")
infrastructure = nr.filter(F(groups__contains='infrastructure'))
core = nr.filter(F(groups__contains='core'))
access = nr.filter(F(groups__contains='access'))

nx_ssh = nx_nr.filter(F(groups__contains='core'))
for switch in nx_ssh.inventory.hosts:
    nx_ssh.inventory.hosts[switch].platform = 'nxos_ssh'

miko_nr = InitNornir("files/netmiko_config.yaml")
miko_infra = miko_nr.filter(F(groups__contains='infrastructure'))
miko_core = miko_nr.filter(F(groups__contains='core'))
miko_access = miko_nr.filter(F(groups__contains='access'))

excluded_vlans = ['1', '1002', '1003', '1004', '1005']

hosts = readYAML('inventory/hosts.yaml')


def init(host):
    device = genie_devices.devices[str(host.host)]
    return device


def execute(fn, *args):

    def wrapper(fn, *args):
        device = args[0]
        command = args[-1]
        device.connect(log_stdout=False)

        return device.parse(command)

    return wrapper


def get_infrastructureData(task, vrfs):
    host = init(task)
    host.connect(log_stdout=False)

    # Init the Host data key
    infrastructure.inventory.hosts[str(task.host)]['data'] = {}

    # Retrieve VLAN configurations
    get_vlans(task, host)

    # Retrieve CDP Neighbors
    # get_neighbors(task, host)

    # Retrieve Layer 3 interface IPs
    # get_SVI(task, host)

    # Retrieve MAC and ARP tables
    # get_arpTable(task, host, vrfs)
    # get_macTable(task, host)
    
    # Write Infrastucture data to files
    write_infrastructureData(task)



def get_arpTable(task, host, vrfs):
    result = host.parse('show ip arp')
    vrf_arp_table = {}

    # Modify Exclusion list here
    EXCLUDED_VRFs = ['Mgmt-vrf', '__Platform_iVRF:_ID00_']

    for vrf in vrfs:
        # Filter out unnecessary VRFs
        if vrf not in EXCLUDED_VRFs:
            vrf_arp_table.update({vrf: {}})

            # Default VRF/Route Table doesn't need a vrf specification
            if vrf == 'default':
                vrf_arp_table[vrf]  = host.parse('show ip arp')

            # Specify vrf from which to retrieve ARP table
            else:
                vrf_arp_table[vrf]  = host.parse(f'show ip arp vrf {vrf}')

    
    infrastructure.inventory.hosts[str(task.host)]['data'].update(vrf_arp_table)


def get_neighbors(task, host):
    result = host.parse('show cdp neighbor')
    infrastructure.inventory.hosts[str(task.host)]['data'].update(result)


def get_macTable(task, host):
    result = host.parse('show mac address-table')
    infrastructure.inventory.hosts[str(task.host)]['data'].update(result)


def get_SVI(task, host):
    if ('7706' or '5672') in str(host):
        result = host.parse('show interface')
    else:
        result = host.parse('show interfaces')

    infrastructure.inventory.hosts[str(task.host)]['data'].update(result)


def get_trunkPorts(task, host):
    if ('7706' or '5672') in str(host):
        result = host.parse('show interface switchport')
    else:
        result = host.parse('show interface trunk')

    infrastructure.inventory.hosts[str(task.host)]['data'].update(result)


def get_vlans(task, host):
    result = host.parse('show vlan')
    infrastructure.inventory.hosts[str(task.host)]['data'].update(result)


def get_vrfs(task):
    return task.run(task=napalm_get, getters=[
        'network_instances']).result


def parse_result(result):
    return_results = {}
    for i in result:
        return_results.update({i: {}})
        for x in result[i]:
            if isinstance(x.result, dict) or isinstance(x.result, list):
                nr.inventory.hosts[i]['data'] = x.result
                return_results[i] = x.result

    return return_results


def parse_vrfs(vrf_result):
    vrf_list = []

    for switch in vrf_result:
        if 'network_instances' in vrf_result[switch]:
            for vrf in vrf_result[switch]['network_instances']:
                if vrf not in vrf_list:
                    vrf_list.append(vrf)

    return vrf_list


def write_infrastructureData(task):
    wr_to_json(infrastructure.inventory.hosts[str(
        task.host)]['data'], f'local_files/full_gather/{str(task.host)}.json')


"""
Topology mapping of Core to Access layer
Structure will be in JSON format, and will look similar to:

{
    "Core": {
        "switch": {
            "VLANS": {
                "100": "NAME_VLAN",
                "200": "NAME_VLAN"
            },
            "VLAN_SVI": {
                "VLAN_100": {
                    "description": "desciption of interface",
                    "ip_address": "127.0.0.1 255.255.255.255"
                }
            },
            "Trunk_Ports": {
                "interface": [
                    "VLAN_100",
                    "VLAN_200"
                ],
                "Quantity": 4 # Type: Integer
            },
            "Access_Ports": {
                "VLAN_100": [
                    "interface_one",
                    "interface_two",
                    "interface_three"
                ],
                "Quantity": 20 # Type: Integer

            },
            "Neighbors": {
                "switch": {
                    "Interfaces": [
                        "interface_one",
                        "interface_two"
                    ]
                }
            }
        },
    "Access": {
        "switch": {
            "VLANS": {
                "100": "NAME_VLAN",
                "200": "NAME_VLAN"
            },
            "VLAN_SVI": {
                "VLAN_100": {
                    "description": "desciption of interface",
                    "ip_address": "127.0.0.1 255.255.255.255"
                }
            },
            "Trunk_Ports": {
                "interface": [
                    "VLAN_100",
                    "VLAN_200"
                ],
                "Quantity": 4 # Type: Integer
            },
            "Access_Ports": {
                "VLAN_100": [
                    "interface_one",
                    "interface_two",
                    "interface_three"
                ],
                "Quantity": 20 # Type: Integer

            },
            "Neighbors": {
                "switch": {
                    "Interfaces": [
                        "interface_one",
                        "interface_two"
                    ]
                }
            }
        }
    }
}


"""


def main():
    # hosts = readYAML('inventory/hosts.yaml')

    # # vrfs = parse_vrfs(parse_result(access.run(task=get_vrfs)))
    vrfs = ['default', 'BMS', 'Media', 'Security']
    data = {}
    infra_with_processors = nr.with_processors([SaveResultToDict(data), PrintResult()])
    infra_with_processors.run(task=get_infrastructureData, vrfs=vrfs)


if __name__ == "__main__":
    main()
