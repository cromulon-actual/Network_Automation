#! /bin/python3

from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure, napalm_cli, napalm_validate
from nornir_netmiko.tasks import netmiko_send_config, netmiko_send_command
from nornir_utils.plugins.tasks.files import write_file
from tqdm import tqdm

from pprint import pprint as pp


def get_running_configs(task, napalm_get_bar):
    r = task.run(task=netmiko_send_command, command_string='show clock')

    print(r.result)


def main():
    nr = InitNornir("files/gns_config.yaml")

    with tqdm(
        total=len(nr.inventory.hosts), desc="gathering running-configs",
    ) as napalm_get_bar:
        nr.run(
            task=get_running_configs,
            napalm_get_bar=napalm_get_bar,
        )


if __name__ == "__main__":
    main()
