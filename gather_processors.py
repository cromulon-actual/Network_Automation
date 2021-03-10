from typing import Dict
from nornir.core import Nornir
from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, MultiResult, Result, Task

from modules.utils import pj


class PrintResult:
    def task_started(self, task: Task) -> None:
        print(f">>> starting: {task.name}\n")

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        print(f">>> completed: {task.name}\n")

    def task_instance_started(self, task: Task, host: Host) -> None:
        print(f">>> Task Instance starting: {task.name} on Host: {host.name}\n")

    def task_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        print(f">>> Task Instance completed: {task.name} on Host: {host.name}\n")

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        print(f"Starting Sub-Task: {task} - {host.name}\n")

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        print(f"Completed Sub-Task: {task} - {host.name}\n")


class SaveResultToDict:
    def __init__(self, data: Dict[str, None]) -> None:
        self.data = data

    def task_started(self, task: Task) -> None:
        self.data[task.name] = {}
        self.data[task.name]["started"] = True

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        self.data[task.name]["completed"] = True

    def task_instance_started(self, task: Task, host: Host) -> None:
        self.data[task.name][host.name] = {"started": True}

    def task_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        self.data[task.name][host.name] = {
            "completed": True,
            "result": result.result,
        }

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        sub_task = {task.name: {host.name: {'started': True}}}

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        sub_task = {task.name: {host.name: {
            'completed': True, 'result': result.result}}}
