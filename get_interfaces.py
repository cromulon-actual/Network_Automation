from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.tasks.files import write_file
from nornir.core.inventory import Groups
from nornir.core.filter import F
from nornir_utils.plugins.functions import print_result
from tqdm import tqdm
from modules.utils import rd_from_json, wr_to_json
from pathlib import Path
from pprint import pprint as pp


def collect_interfaces(task, napalm_get_bar):
    unused_interfaces = {}
    available_interfaces = {}
    trunk_interfaces = {}
    demo_interfaces = {}
    r = task.run(task=napalm_get, getters=["interfaces"])
    interfaces = dict(r.result["interfaces"])
    for interface, info in interfaces.items():
        if ("Ethernet" and "/0/") in interface:
            if info["is_up"] is False:
                if info["description"] == "Demo":
                    demo_interfaces.update({interface: info})
                elif info["description"] not in ["IT - Video",
                                               "IT - Employee",
                                               "IT - Voice",
                                               "IT - Infrastructure AP",
                                               "BMS",
                                               "Media",
                                               "Security",
                                               "Security - Camera",
                                               "Media subnet #2"]:
                    unused_interfaces.update({interface: info})
                else:
                    available_interfaces.update({interface: info})
        elif "TenGigabitEthernet" in interface and ("/1/3" in interface or "/1/4" in interface) and info["is_up"]:
            
            trunk_interfaces.update({interface: info})
    
    wr_to_json(unused_interfaces,
               f"files/interfaces/unused_interfaces/{task.host}.json")
    wr_to_json(available_interfaces,
               f"files/interfaces/avail_interfaces/{task.host}.json")
    wr_to_json(trunk_interfaces,
               f"files/interfaces/trunk_interfaces/{task.host}.json")
    wr_to_json(demo_interfaces,
               f"files/interfaces/demo_interfaces/{task.host}.json")
    napalm_get_bar.update()
    tqdm.write(f"{task.host}: interfaces gathered")

def detect_demo_interfaces(task, napalm_get_bar):
    demo_interfaces = {}
    r = task.run(task=napalm_get, getters=["interfaces"])
    interfaces = dict(r.result["interfaces"])
    for interface, info in interfaces.items():
        if "Demo" in info["description"] and "Ethernet" in interface and info["is_up"] is True:
            demo_interfaces.update({interface: info})
    
    wr_to_json(demo_interfaces,
               f"files/demo_configs/demo_interfaces/{task.host}.json")
    napalm_get_bar.update()
    tqdm.write(f"{task.host}: interfaces gathered")
    
# def collect_interfaces():
#     devices = rd_from_json("demo_build.json")
#     with open("demo_interfaces.txt", "w+") as f:
#         for device in devices:
#             if device != "CIB-Internet-FW":
#                 f.write(f"{device}:\n")
#                 interfaces = rd_from_json(f"files/demo_configs/demo_interfaces/{device}.json")
#                 if interfaces:
#                     for interface in interfaces:
#                         f.write(f"{interface}\n")
#             f.write(f"!\n")
            
def main():
    # collect_interfaces()
    nr = InitNornir("files/config.yaml")
    Demo_Proj_inv = nr.filter(F(groups__contains="Demo-Proj")).inventory.hosts
    Demo_Proj = nr.filter(F(groups__contains="Demo-Proj"))
    with tqdm(
        total=len(Demo_Proj_inv), desc="gathering interfaces",
    ) as napalm_get_bar:
        Demo_Proj.run(
            task=collect_interfaces,
            napalm_get_bar=napalm_get_bar,
        )

    nexus = ["CIB-N210-7706-1", "CIB-N210-7706-2"]
    demo_switches = rd_from_json("demo_build.json")
    switches = [switch for switch in demo_switches if switch not in nexus]

    potential_ports = {}

    for switch in switches:
        if switch == "CIB-Internet-FW":
            pass
        else:
            potential_ports.update({switch: {}})
            interfaces = rd_from_json(
                f"files/interfaces/unused_interfaces/{switch}.json")
            demo_interfaces = rd_from_json(
                f"files/interfaces/demo_interfaces/{switch}.json")
            for interface in demo_interfaces:
                potential_ports[switch].update({interface: demo_interfaces[interface]})
            if interfaces:
                for interface in interfaces:
                    if switch in ["CIB-112-3850-1",
                                "CIB-S114-3850-1",
                                "CIB-N107-3850-1",
                                "CIB-N107-3850-2",
                                "CIB-S213-3850-1",
                                "CIB-S213-3850-2",
                                "CIB-N210-3850-1",
                                "CIB-N210-3850-2"]:
                        if len(potential_ports[switch]) < 4:
                            potential_ports[switch].update(
                                {interface: interfaces[interface]})
                    else:
                        if len(potential_ports[switch]) < 8:
                            potential_ports[switch].update(
                                {interface: interfaces[interface]})
            if (switch in ["CIB-112-3850-1",
                            "CIB-S114-3850-1",
                            "CIB-N107-3850-1",
                            "CIB-N107-3850-2",
                            "CIB-S213-3850-1",
                            "CIB-S213-3850-2",
                            "CIB-N210-3850-1",
                            "CIB-N210-3850-2"] and len(potential_ports[switch]) < 4):
                
                interfaces = rd_from_json(
                    f"files/interfaces/avail_interfaces/{switch}.json")
                for interface in interfaces:
                    if len(potential_ports[switch]) < 4:
                        potential_ports[switch].update(
                            {interface: interfaces[interface]})
            elif (switch not in ["CIB-112-3850-1",
                            "CIB-S114-3850-1",
                            "CIB-N107-3850-1",
                            "CIB-N107-3850-2",
                            "CIB-S213-3850-1",
                            "CIB-S213-3850-2",
                            "CIB-N210-3850-1",
                            "CIB-N210-3850-2"] and len(potential_ports[switch]) < 8):
                interfaces = rd_from_json(
                    f"files/interfaces/avail_interfaces/{switch}.json")
                for interface in interfaces:
                    if len(potential_ports[switch]) < 8:
                        potential_ports[switch].update(
                            {interface: interfaces[interface]})
    
    wr_to_json(potential_ports, "demo_ports.json")

    demo_build = rd_from_json("demo_build.json")
    demo_ports = rd_from_json("demo_ports.json")
    port_info = {
        "description": "description Demo",
        "switchport mode": "switchport mode access",
        "switchport access": "switchport access vlan 300",
        "ip access-group": "ip access-group PREAUTH_ACL_IN in",
        "load-interval": "load-interval 30",
        "authentication 1": "authentication control-direction in",
        "authentication 2": "authentication event fail action next-method",
        "authentication 3": "authentication event server dead action reinitialize vlan 300",
        "authentication 4": "authentication event server dead action authorize voice",
        "authentication 5": "authentication event server alive action reinitialize",
        "authentication 6": "authentication host-mode multi-auth",
        "authentication 7": "authentication open",
        "authentication 8": "authentication order dot1x mab",
        "authentication 9": "authentication priority dot1x mab",
        "authentication 10": "authentication port-control auto",
        "authentication 11": "authentication periodic",
        "authentication 12": "authentication timer reauthenticate server",
        "authentication 13": "authentication violation restrict",
        "mab": "mab",
        "snmp 1": "snmp trap mac-notification change added",
        "snmp 2": "snmp trap mac-notification change removed",
        "dot1x 1": "dot1x pae authenticator",
        "dot1x 2": "dot1x timeout tx-period 3",
        "spanning-tree": "spanning-tree portfast"
    }

    for switch in demo_ports:
        for interface, value in demo_ports[switch].items():
            demo_build[switch]["interfaces"].update({interface: port_info})

    wr_to_json(demo_build, "demo_build.json")


if __name__ == "__main__":
    main()



