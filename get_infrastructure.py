from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure, napalm_cli, napalm_validate
from nornir_netmiko.tasks import netmiko_send_config
from nornir_utils.plugins.tasks.files import write_file
from nornir_utils.plugins.functions import print_result

from modules.utils import pj

from pprint import pprint as pp


nr = InitNornir("files/config.yaml")
core = nr.filter(F(groups__contains='core'))
access = nr.filter(F(groups__contains='access'))
miko_nr = InitNornir("files/netmiko_config.yaml")
miko_core = miko_nr.filter(F(groups__contains='core'))
miko_access = miko_nr.filter(F(groups__contains='access'))


def Test_Functions(task):
    # Test getting VLAN DB
    result = task.run(task=napalm_get, getters=[
                      'network_instances'], getters_options={'name': ''})

    return result


def parse_result(result):
    return_results = {}
    for i in result:
        return_results.update({i: {}})
        for x in result[i]:
            if isinstance(x.result, dict):
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


def get_arpTable(task, vrfs):
    vrf_arp_table = {str(task.host): {}}
    for vrf in vrfs:
        if vrf == 'default':
            vrf_arp_table[str(task.host)] = task.run(task=napalm_get, getters=[
                'arp_table']).result
        else:

            vrf_arp_table[str(task.host)] = task.run(task=napalm_get, getters=[
                'arp_table'], vrf=vrf).result
        print(vrf_arp_table)
    return task.run(task=napalm_get, getters=['arp_table'])


def get_vlans(task):
    return task.run(task=napalm_get, getters=['vlans'])


def get_SVI(task, vlan):
    return task.run(task=napalm_get, getters=['interfaces_ip'])


def get_vrfs(task):
    return task.run(task=napalm_get, getters=[
        'network_instances'])


def get_trunkPorts(task, vlan):

    pass


def get_accessPorts(task, vlan):

    pass


def get_neighbors(task, interfaces, vlan=None):

    pass


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
    vrfs = parse_vrfs(parse_result(access.run(task=get_vrfs)))

    arp_table = access.run(task=get_arpTable, vrfs=vrfs)

    result = parse_result(access.run(task=Test_Functions))

    # pj(result)


if __name__ == "__main__":
    main()
