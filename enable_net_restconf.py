#! /bin/python3

from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure, napalm_cli, napalm_validate
from nornir_netmiko.tasks import netmiko_send_config
from nornir_utils.plugins.tasks.files import write_file
from tqdm import tqdm

from pprint import pprint as pp

# nr = InitNornir("files/config.yaml")
nr = InitNornir("files/gns_config.yaml")
cib_infra = nr.filter(F(groups__contains='infrastructure'))
core = nr.filter(F(groups__contains='core'))
access = nr.filter(F(groups__contains='access'))


# miko_nr = InitNornir("files/netmiko_config.yaml")
miko_nr = InitNornir("files/gnsmiko_config.yaml")
miko_core = miko_nr.filter(F(groups__contains='core'))
miko_access = miko_nr.filter(F(groups__contains='access'))


def run_tasks(task, *args, **kwargs):
    def wrapper(*args, **kwargs):
        devices = args[0]
        with tqdm(
            total=len(devices.inventory.hosts), desc=f'Running task {task.__name__}',
        ) as napalm_get_bar:
            if 'pre' in kwargs or 'post' in kwargs:
                pre = kwargs['pre']
                post = kwargs['post']

                r = devices.run(
                    task=task,
                    pre=pre,
                    post=post,
                    napalm_get_bar=napalm_get_bar,
                )
            else:
                r = devices.run(
                    task=task,
                    napalm_get_bar=napalm_get_bar
                )

        return r

    return wrapper


@run_tasks
def save_config(task, napalm_get_bar=None, pre=False, post=False):
    """Saves configurations during specific phases of change.
    Pre or Post flag is required

    Args:
        task (class-object): Iterates over instanced Devices to run tasks against
        pre (bool, optional): Flag for pre-implementaion. Defaults to False.
        post (bool, optional): Flag for post-implementation. Defaults to False.
    """
    if pre:
        phase = 'pre_implementation'

    elif post:
        phase = 'post_implementation'

    r = task.run(task=napalm_get, getters=['config'])

    task.run(
        task=write_file,
        content=r.result['config']['running'],
        filename=f'local_files/implementation/{phase}/{task.host}.txt'
    )

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: {phase} running-config gathered")


@run_tasks
def enable_net_restconf(task, napalm_get_bar=None):
    """[summary]

    Args:
        task (class-object): Iterates over instanced Devices to run tasks against
        napalm_get_bar (class-object): Progress Bar
    """
    if str(task.host) in nr.filter(F(groups__contains='core')).inventory.hosts:
        commands = [
            'feature nxapi',
            # 'nxapi http port 8080',
            # 'nxapi https port 8443',
            'feature netconf',
            'feature restconf',
            'nxapi http port 80',
            'nxapi https port 443',
            'nxapi sandbox'
        ]

    elif str(task.host) in nr.filter(F(groups__contains='access')).inventory.hosts:
        commands = [
            'netconf-yang',
            'netconf-yang feature candidate-datastore',
            'restconf',
            'ip http secure-server'
        ]

    r = task.run(task=netmiko_send_config, config_commands=commands)

    with open(f'local_files/implementation/changes/{str(task.host)}.txt', 'w') as f:
        f.write(r.result)

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: Commands ({commands}) gathered.")


@run_tasks
def post_net_restconf(task, napalm_get_bar=None):
    """Writes show commands after implementation

    Args:
        task (class-object): Iterates over instanced Devices to run tasks against
        napalm_get_bar (class-object): Progress Bar
    """

    if str(task.host) in nr.filter(F(groups__contains='core')).inventory.hosts:
        commands = [
            'show run | grep nxapi',
            'show nxapi',
            'show feature | grep nxapi',
            'show feature | grep netconf',
            'show feature | grep restconf'
        ]

    elif str(task.host) in nr.filter(F(groups__contains='access')).inventory.hosts:
        commands = [
            'show netconf-yang datastores',
            'show netconf-yang sessions',
            'show netconf-yang sessions detail',
            'show netconf-yang statistics',
            'show platform software yang-management process'
        ]

    r = task.run(task=napalm_cli, commands=commands)

    with open(f'local_files/implementation/validation/{str(task.host)}.txt', 'w') as f:
        for command in commands:
            f.write(f'{str(task.host)}# {command}\n')
            f.write(f'{r.result[command]}\n!\n')

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: Commands ({commands}) gathered.")


def main():
    ##############################################
    ######## Pre-Implementation copy-run  ########
    ##############################################

    # Get pre-implementation running-configs
    save_config(cib_infra, pre=True, post=False)

    ##############################################
    ####### Configure NETCONF and RESTCONF #######
    ##############################################

    ##// Enable for Core devices //##
    enable_net_restconf(miko_core)

    ##// Enable for Access devices //##
    enable_net_restconf(miko_access)

    ##############################################
    ####### Validate  NETCONF and RESTCONF #######
    ##############################################

    ##// Validate for Core devices //##
    post_net_restconf(core)

    ##// Validate for Access devices //##
    post_net_restconf(access)

    ##############################################
    ######## Post-Implementation copy-run ########
    ##############################################

    # Get post-implementation running-configs
    save_config(cib_infra, pre=False, post=True)


if __name__ == '__main__':
    main()
