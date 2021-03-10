from os import write
from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure, napalm_cli, napalm_validate
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.tasks.files import write_file
from nornir_utils.plugins.functions import print_result

from modules.utils import pj, wr_to_json, readYAML

from pprint import pprint as pp


class GatherInfrastucture:

    excluded_vlans = ['1', '1002', '1003', '1004', '1005']

    # Modify Exclusion list here
    EXCLUDED_VRFs = ['Mgmt-vrf', '__Platform_iVRF:_ID00_']

    def __init__(self, nr, nr_access=None, nxos_ssh=None):
        self.nr = nr
        self.nr_access = nr_access
        self.nxos_ssh = nxos_ssh

    def get_infrastructureData(self, vrfs):
        # Initialize Data Store
        self.nr.inventory.hosts[str(task.host)]['data'] = {}

        # Retrieve VLAN configurations
        task.run(task=self.get_vlans)

        # Retrieve CDP Neighbors
        task.run(task=self.get_neighbors)

        if str(task.host) in self.nr_access.inventory.hosts:

            # Retrieve Layer 3 interface IPs
            task.run(task=self.get_SVI)

            # Retrieve MAC and ARP tables
            task.run(task=self.get_tables, vrfs=vrfs)

        return True

    def get_coreInfData(self, task, vrfs):
        # Retrieve Layer 3 interface IPs
        task.run(task=self.get_SVI)

        # Retrieve MAC and ARP tables
        task.run(task=self.get_tables, vrfs=vrfs)

    def get_tables(self, task, vrfs):
        task.run(task=self.get_arpTable, vrfs=vrfs)
        task.run(task=self.get_macTable)

    def get_arpTable(self, task, vrfs):
        vrf_arp_table = {}

        for vrf in vrfs:
            # Filter out unnecessary VRFs
            if vrf not in self.EXCLUDED_VRFs:
                vrf_arp_table.update({vrf: {}})

                # Default VRF/Route Table doesn't need a vrf specification
                if vrf == 'default':
                    vrf_arp_table[vrf] = task.run(task=napalm_get, getters=[
                        'arp_table']).result

                # Specify vrf from which to retrieve ARP table
                else:
                    vrf_arp_table[vrf] = task.run(task=napalm_get, getters=[
                        'arp_table'], vrf=vrf).result

        self.nr.inventory.hosts[str(task.host)]['data'].update(
            {
                'arp_tables': vrf_arp_table
            }
        )

    def get_neighbors(self, task):
        self.nr.inventory.hosts[str(task.host)]['data'].update(
            {
                'cdp_neighbors': task.run(
                    task=netmiko_send_command,
                    command_string='show cdp neighbor',
                    enable=True,
                    use_textfsm=True
                ).result
            }
        )

    def get_macTable(self, task):
        self.nr.inventory.hosts[str(task.host)]['data'].update(
            task.run(task=napalm_get, getters=[
                'mac_address_table']).result
        )

    def get_SVI(self, task, vlan=None):
        self.nr.inventory.hosts[str(task.host)]['data'].update(
            task.run(task=napalm_get, getters=['interfaces_ip']).result)

    def get_vlans(self, task):
        self.nr.inventory.hosts[str(task.host)]['data'].update(
            task.run(task=napalm_get, getters=['vlans']).result)

    def get_vrfs(self, task):
        return task.run(task=napalm_get, getters=[
            'network_instances']).result

    def parse_result(self, result):
        return_results = {}
        for i in result:
            return_results.update({i: {}})
            for x in result[i]:
                if isinstance(x.result, dict) or isinstance(x.result, list):
                    nr.inventory.hosts[i]['data'] = x.result
                    return_results[i] = x.result

        return return_results

    def parse_vrfs(self, vrf_result):
        vrf_list = []

        for switch in vrf_result:
            if 'network_instances' in vrf_result[switch]:
                for vrf in vrf_result[switch]['network_instances']:
                    if vrf not in vrf_list:
                        vrf_list.append(vrf)

        return vrf_list

    def return_inventory(self):
        return self.nr

    def write_infrastructureData(self, task):
        wr_to_json(self.nr.inventory.hosts[str(
            task.host)]['data'], f'local_files/full_gather/{str(task.host)}.json')
