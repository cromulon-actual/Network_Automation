from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.tasks.files import write_file
from tqdm import tqdm

from modules.utils import wr_to_json


def get_running_configs(task, napalm_get_bar):
    r = task.run(task=napalm_get, getters=["facts"])
    task.host["facts"] = r.result
    # task.run(
    #     task=write_file,
    #     content=r.result["config"]["running"],
    #     filename=f"files/running_configs/{task.host}.txt",
    # )
    wr_to_json(r.result, f"files/running_configs/{task.host}.json") 
    napalm_get_bar.update()
    tqdm.write(f"{task.host}: running-config gathered")

def main():
    nr = InitNornir("files/config.yaml")
    with tqdm(
        total=len(nr.inventory.hosts), desc="gathering running-configs",
    ) as napalm_get_bar:
        nr.run(
            task=get_running_configs,
            napalm_get_bar=napalm_get_bar,
        )
        
if __name__ == "__main__":
    main()
