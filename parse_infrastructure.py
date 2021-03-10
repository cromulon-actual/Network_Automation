from nornir import InitNornir
from nornir.core.filter import F
from modules.utils import rd_from_json, wr_to_json, pj


class Parse:

    excluded_vlans = ['1', '1002', '1003', '1004', '1005']

    def __init__(self, unparsed):
        self.infrastructure = self.collect_infra_info(unparsed)
        self.all_vlans = self.__total_VLANs()
        self.vlan_groups = self.group_all_vlans()
        self.trunk_ports = self.get_trunkPorts()

    def collect_host_info(self, host):
        host_info = rd_from_json(
            f'local_files/full_gather/{host}.json')
        return host_info

    def collect_infra_info(self, unparsed):
        parsed = {}
        for host in unparsed.inventory.hosts:
            parsed.update({host: self.collect_host_info(host)})

            # filter vlans
            vlans = parsed[host]['vlans']
            parsed[host]['vlans'] = self.__filter_vlans(vlans)

            #
        return parsed

    def __filter_vlans(self, host_vlans):
        for vlan in self.excluded_vlans:
            if vlan in host_vlans:
                del host_vlans[vlan]

        return host_vlans

    def __total_VLANs(self):
        all_vlans = []
        for host in self.infrastructure:
            for vlan in self.infrastructure[host]['vlans']:
                all_vlans.append(vlan)

        return set(all_vlans)

    def group_all_vlans(self):
        vlan_groups = {}
        v100 = list(range(100, 200, 1))
        v200 = list(range(200, 300, 1))
        v300 = list(range(300, 400, 1))
        v400 = list(range(400, 500, 1))
        v500 = list(range(500, 600, 1))
        v600 = list(range(600, 700, 1))
        v700 = list(range(700, 800, 1))
        v3000 = list(range(3000, 3100, 1))

        vlan_groups.update(
            {'group_100': [vlan for vlan in self.all_vlans if int(vlan) in v100]})
        vlan_groups.update(
            {'group_200': [vlan for vlan in self.all_vlans if int(vlan) in v200]})
        vlan_groups.update(
            {'group_300': [vlan for vlan in self.all_vlans if int(vlan) in v300]})
        vlan_groups.update(
            {'group_400': [vlan for vlan in self.all_vlans if int(vlan) in v400]})
        vlan_groups.update(
            {'group_500': [vlan for vlan in self.all_vlans if int(vlan) in v500]})
        vlan_groups.update(
            {'group_600': [vlan for vlan in self.all_vlans if int(vlan) in v600]})
        vlan_groups.update(
            {'group_700': [vlan for vlan in self.all_vlans if int(vlan) in v700]})
        vlan_groups.update(
            {'group_3000': [vlan for vlan in self.all_vlans if int(vlan) in v3000]})

        for vlans in vlan_groups:
            vlan_groups[vlans].sort()

        return vlan_groups

    def get_trunkPorts(self):
        trunk_ports = {}
        for host in self.infrastructure:
            trunk_ports.update({host: {}})
            vlans = []
            for vlan in self.infrastructure[host]['vlans']:
                for interface in self.infrastructure[host]['vlans'][vlan]['interfaces']:
                    if 'Port-channel' in interface or '1/25' in interface or '1/26' in interface:
                        if interface in self.infrastructure[host]['vlans'][vlan]['interfaces']:
                            if vlan not in vlans:
                                vlans.append(vlan)
                            trunk_ports[host].update({interface: vlans})

        return trunk_ports


def main():
    infrastructure = InitNornir(
        'files/config.yaml').filter(F(groups__contains='infrastructure'))

    parsed = Parse(infrastructure)

    wr_to_json(parsed.trunk_ports, 'trunk_ports.json')


if __name__ == '__main__':
    main()
