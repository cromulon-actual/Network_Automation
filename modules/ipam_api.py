import phpipamsdk
import warnings
from phpipamsdk.controllers.addresses_api import AddressesApi
from phpipamsdk.controllers.devices_api import DevicesApi
from phpipamsdk.controllers.vlans_api import VlansApi
from phpipamsdk.phpipam import PhpIpamException
from phpipamsdk.utils import *

from modules.nice import ipam_creds  # personal credentials


class ApiIpam(object):
    warnings.filterwarnings("ignore")
    IPAM = phpipamsdk.PhpIpamApi(
        api_uri=ipam_creds.url, api_appcode=ipam_creds.api, api_verify_ssl=True
    )

    IPAM.login()

    def __init__(self, ip=None):
        self.ip = ip

    def get_info(self):

        ip_info = AddressesApi(
            phpipam=self.IPAM).search_address(address=self.ip)
        if ip_info["data"][0]["mac"] is None or ip_info["data"][0]["mac"] == "":
            missing_mac = ip_info["data"][0]["ip"]
            return missing_mac
        else:
            try:

                mac = ip_info["data"][0]["mac"]
                mac = mac.split(" ")
                mac = ("").join(mac).lower()
                mac = (".").join(mac[i: i + 4] for i in range(0, len(mac), 4))

                deviceID = ip_info["data"][0]["deviceId"]
                switch = self.get_switch(deviceId=deviceID)

                interface = ip_info["data"][0]["port"]

                ip_info = {"ip": self.ip, "mac": mac,
                           "switch": switch, "interface": interface}
                return ip_info
            except AttributeError as err:
                print(err, ip_info)

    def get_switch(self, deviceId=None):
        device_info = DevicesApi(
            phpipam=self.IPAM).get_device(device_id=deviceId)
        try:
            switch = device_info["data"]["hostname"]
            return switch
        except TypeError:
            return None

    def get_id_vlan(self, name, number, l2domain_id=None):
        return get_vlan_id(ipam=self.IPAM, name=None, number=None, l2domain_id=None)

    def get_id_section(self, section_name):
        return get_section_id(ipam=self.IPAM, name=section_name)

    def get_id_tools_location(self, location):
        return get_tools_location_id(ipam=self.IPAM, name=location)

    def get_id_subnet(self, name, net_cidr, section_id):
        return get_subnet_id(ipam=self.IPAM, name=name, cidr=net_cidr, section_id=section_id)

    def get_id_device(self, name):
        return get_device_id(ipam=self.IPAM, name=name)

    def get_id_vrf(self, vlan):
        vrf_names = {200: "BMS", 300: "Demo", 400: "Security", 500: "Media"}
        return get_vrf_id(ipam=self.IPAM, name=vrf_names[vlan]), vrf_names[vlan]

    def get_id_address(self, ip_address, subnet_id):
        return get_address_id(ipam=self.IPAM, ip_addr=ip_address, subnet_id=subnet_id)
