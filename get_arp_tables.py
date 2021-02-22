from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.tasks.files import write_file
from nornir.core.inventory import Groups
from nornir.core.filter import F
from nornir_utils.plugins.functions import print_result
from tqdm import tqdm
from modules.utils import rd_from_json, wr_to_json

MASTER_STENT_IP_LIST = {}


def parse_vlan(mac_entry):
    MAC_OUI = "00:13:CB"
    if mac_entry['vlan'] == 400 and MAC_OUI in mac_entry['mac']:
        return mac_entry
    else:
        return False


def consolidate(host):
    return rd_from_json(f"files/arp_tables/{host}.json")


def get_arp_table(task, napalm_get_bar):
    stentofon_ip_list = {}
    result = task.run(task=napalm_get, getters=["mac_address_table"])

    full_mac_table = result.result['mac_address_table']
    for mac_entry in full_mac_table:
        stent_mac_entry = parse_vlan(mac_entry)
        if stent_mac_entry:
            result = task.run(task=napalm_get, getters=[
                              "arp_table"], vrf="Security")
            full_arp_table = result.result['arp_table']
            for arp_entry in full_arp_table:
                if arp_entry['mac'] == stent_mac_entry['mac']:
                    stentofon_ip_list.update(
                        {arp_entry['mac']: arp_entry['ip']})

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: IP's Gathered")

    wr_to_json(full_mac_table, "full_mac.json")
    wr_to_json(full_arp_table, "full_arp.json")
    wr_to_json(stentofon_ip_list, f"files/arp_tables/{str(task.host)}.json")


def main():
    nr = InitNornir("files/config.yaml")
    access_inv = nr.filter(F(groups__contains="Access")).inventory.hosts
    access = nr.filter(F(groups__contains="Access"))

    with tqdm(
        total=len(access_inv), desc="gathering interfaces",
    ) as napalm_get_bar:
        access.run(
            task=get_arp_table,
            napalm_get_bar=napalm_get_bar,
        )

    for host in access_inv:
        MASTER_STENT_IP_LIST.update(consolidate(host))

    wr_to_json(MASTER_STENT_IP_LIST, "master_stent_list.json")

    with open("stent_ip_list.txt", "w+") as f:
        for mac, ip in MASTER_STENT_IP_LIST.items():
            f.write(f"{mac} - {ip}\n")


if __name__ == '__main__':
    main()
