from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.tasks.files import write_file
from tqdm import tqdm

from modules.utils import wr_to_json


def get_running_configs(task, napalm_get_bar):
    """Writes running configs to text file

    Args:
        task (object): Devices.run to iterate through
        napalm_get_bar (object): Updates TQDM Progress Bar
    """
    r = task.run(task=napalm_get, getters=["config"])

    task.run(
        task=write_file,
        content=r.result["config"]["running"],
        filename=f"local_files/running_configs/txt/{task.host}.txt",
    )

    napalm_get_bar.update()
    tqdm.write(f"{task.host}: running-config gathered")


def main():
    nr = InitNornir("files/gns_config.yaml")
    print(nr.inventory.hosts)

    with tqdm(
        total=len(nr.inventory.hosts), desc="gathering running-configs",
    ) as napalm_get_bar:
        nr.run(
            task=get_running_configs,
            napalm_get_bar=napalm_get_bar,
        )


if __name__ == "__main__":
    main()
