from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure, napalm_cli, napalm_validate
from nornir_utils.plugins.tasks.files import write_file
from tqdm import tqdm

nr = InitNornir('files/config.yaml')


def run_tasks(task, *args, **kwargs):
    def wrapper(*args, **kwargs):
        devices = args[0]
        with tqdm(
            total=len(devices.inventory.hosts), desc="gathering running-configs",
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
def enable_net_restconf(task, napalm_get_bar):
    """[summary]

    Args:
        task (class-object): Iterates over instanced Devices to run tasks against
        napalm_get_bar (class-object): Progress Bar
        core (bool, optional): Flag for Nexus switches. Defaults to False.
        access (bool, optional): Flag for access switches. Defaults to False.
    """

    if task.host in nr.filter(F(groups__contains="NX-OS")).inventory.hosts:
        commands = [
            'show clock',
            'show ssh server'
        ]

        r = task.run(task=napalm_cli, commands=commands)

    elif task.host in nr.filter(F(groups__contains="c3850")).inventory.hosts:
        # commands = [
        #     'netconf-yang',
        #     'netconf-yang feature candidate-datastore',
        #     'restconf',
        #     'ip http secure-server'
        # ]
        commands = [
            'show clock'
        ]

        r = task.run(task=napalm_cli, commands=commands)

    for result in r.result:
        print(r.result[result])

    # task.run(
    #     task=write_file,
    #     content=r.result
    # )

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: running-config gathered")


def main():

    cib_infra = nr.filter(F(groups__contains='infrastructure'))

    # print(cib_infra.inventory.hosts)

    # Get pre-implementation running-configs
    # save_config(cib_infra, pre=True, post=False)
    switches_nexus = nr.filter(F(groups__contains="NX-OS"))
    # Configure NETCONF and RESTCONF
    enable_net_restconf(switches_nexus)

    switches_3850 = nr.filter(F(groups__contains="c3850"))

    # Get post-implementation running-configs
    # save_config(cib_infra, pre=False, post=True)


if __name__ == '__main__':
    main()
