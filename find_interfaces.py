#!usr/bin/env python

import sys
from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import *
from nornir_utils.plugins.functions import print_result
from pprint import pprint as pp

nr = InitNornir("files/config.yaml")

def find_interfaces(task, vlan):
    available_interfaces = {str(task.host): []}
    vlans = task.run(task=napalm_get, getters="vlans").result
    vlan_interfaces = vlans['vlans'][vlan]['interfaces']
        
    interfaces = task.run(task=napalm_get, getters="interfaces").result['interfaces']
    
    for interface in vlan_interfaces:
        if not interfaces[interface]['is_up']:
            available_interfaces[str(task.host)].append(interface)
    
    return available_interfaces
    
def main(switches, vlan):
    available_interfaces = {}
    if len(switches) > 1:
        for switch in switches:
            interfaces = nr.filter(name=switch)
            interfaces = interfaces.run(task=find_interfaces, vlan=vlan)
            
            for info in interfaces:
                available_interfaces.update(interfaces[info].result)
                
                
        pp(available_interfaces)
    
    elif len(switches) ==1:
        pass    
    
if __name__ == "__main__":
    inventory = []
    for k,v in nr.inventory.hosts.items():
        inventory.append(k)
        
    
    # Taking on more than one argument for multiple devices maxed out at
    # two. Modify index for more devices
    if len(sys.argv[1:-1]) > 1:
        switches = list(sys.argv[1:-1])
        vlan = sys.argv[-1]
        switches = [x.upper() for x in switches]
        
        
        if (switches[0] and switches[1]) in inventory:
            print("\n" + "=" * 100 + "\n" + "=" * 100 + "\n")
            print(f"You have selected {switches[0]} and {switches[-1]}. Please wait.")
            main(switches, vlan)
        else:
            sys.exit(f"{switches} not in Inventory")

    else:
        switch = sys.argv[1]
        switch = switch.upper()
        if switch in inventory:
            main(switch)
        else:
            sys.exit(f"{switch} not in Inventory")
            
    
