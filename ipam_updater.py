from modules.ipam_api import ApiIpam
from nornir import InitNornir
from nornir.core.inventory import Groups
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.tasks.files import write_file
from nornir_utils.plugins.functions import print_result
from tqdm import tqdm
import requests
import urllib3
import time
import multiprocessing
from pprint import pprint as pp

from modules.utils import *
from modules.nice import *


def get_prtg_devices(method, content):
    urllib3.disable_warnings()
    userName = prtg_creds.username
    userPass = prtg_creds.userpass
    prtg_base_url = prtg_creds.url
    auth_string = f"&username={userName}&password={userPass}"
    prtg_url = f"{prtg_base_url}{content}{auth_string}"

    if method == "get":
        r = requests.get(prtg_url, verify=False)
        return r.json()
    elif method == "post":
        r = requests.post(prtg_url, verify=False)
        return f"Auto-Acknowledged status code: {r.status_code}"


def parse_prtg_devices(prtg_devices):
    for info in prtg_devices.values():
        if type(info) is list:
            device_list = info
            device_list = list(
                item
                for item in device_list
                for (k, v) in item.items()
                if (k == "group" and v == "Lenel Security Cameras")
                or (k == "group" and v == "Stentophones")
            )
    security_devices = {"Security Devices": device_list}
    return security_devices


def get_arp_data(task, vlanid, napalm_get_bar):
    ipam = ApiIpam()
    toBeUpdated = {str(task.host): {'deviceID': ipam.get_id_device(str(task.host)),
                                    'devices': []}}
    result = task.run(task=napalm_get, getters=["mac_address_table"])

    full_mac_table = result.result['mac_address_table']
    for mac_entry in full_mac_table:
        if mac_entry['vlan'] == vlanid:
            result = task.run(task=napalm_get, getters=[
                              "arp_table"], vrf="Security")
            full_arp_table = result.result['arp_table']
            for arp_entry in full_arp_table:
                if arp_entry['mac'] == mac_entry['mac']:
                    if 'Vl' not in mac_entry['interface']:
                        toBeUpdated[str(task.host)]['devices'].append(
                            {
                                'mac address': mac_entry['mac'],
                                'ip': arp_entry['ip'],
                                'vlan': mac_entry['vlan'],
                                'interface': mac_entry['interface']
                            }
                        )

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: IP's Gathered")
    if toBeUpdated:
        wr_to_json(toBeUpdated, f"files/arp_tables/{str(task.host)}.json")


def consolidate(host):
    try:
        updates = rd_from_json(f"files/arp_tables/{host}.json")
        return updates

    except FileNotFoundError:
        return


def update_ipam():
    pass


def main():
    MASTER_UPDATE_LIST = {}

    vlanid = 400
    ipam = ApiIpam()

    prtg_devices_api = "table.json?content=devices&columns=objid,group,device,host&output=json"
    prtg_devices = get_prtg_devices("get", prtg_devices_api)
    filter_devices = parse_prtg_devices(prtg_devices)

    nr = InitNornir("files/config.yaml")
    access_inv = nr.filter(F(groups__contains="Access")).inventory.hosts
    access = nr.filter(F(groups__contains="Access"))

    with tqdm(
        total=len(access_inv), desc="gathering interfaces",
    ) as napalm_get_bar:
        access.run(
            task=get_arp_data,
            vlanid=vlanid,
            napalm_get_bar=napalm_get_bar
        )

    for host in access_inv:
        updates = consolidate(host)
        if updates:
            pp(updates)
            MASTER_UPDATE_LIST.update(updates)
    wr_to_json(MASTER_UPDATE_LIST, "master_update_list.json")

    secID = ipam.get_id_section("Carrier_CIB")
    vrf_vlan = ipam.get_id_vrf(vlanid)
    vrfID = vrf_vlan[0]
    # vlanID = ipam.get_id_vlan(vrf_vlan[-1], vlanid)


if __name__ == '__main__':
    main()
