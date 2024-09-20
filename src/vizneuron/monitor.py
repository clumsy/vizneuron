import multiprocessing as mp
import os
import time

from typing import Optional, Iterable, List, Dict, Any
from collections import defaultdict

from viztracer.vizplugin import VizPluginBase

NEURON_SYSFS_PATH = "/sys/devices/virtual/neuron_device"


def device_count(dir_path: str = NEURON_SYSFS_PATH) -> int:
    return sum(os.path.isdir(os.path.join(dir_path, e)) for e in os.listdir(dir_path))


def core_count(device_id: int = 0) -> int:
    num_cores = sysfs(f"{NEURON_SYSFS_PATH}/neuron{device_id}/core_count")
    assert num_cores is not None, "cannot determine the number of cores per Neuron device"
    return int(num_cores)


def data_paths(local_ranks: Optional[Iterable[int]]) -> List[int]:
    if not local_ranks:
        return [NEURON_SYSFS_PATH]
    num_cores = core_count()
    return ["{}/neuron{}/neuron_core{}/stats/memory_usage".format(NEURON_SYSFS_PATH, *divmod(i, num_cores)) for i in local_ranks]


def sysfs(path: str) -> Optional[str]:
    try:
        with open(path, "r") as f:
            return f.read()
    except BaseException as e:
        # the file could be gone before we get a chance to see the contents
        print("failed to parse", path, e)
        return None


class NeuronMonitor(VizPluginBase):
    def __init__(self, options: Dict[str, Any], interval: float, local_ranks: Optional[Iterable[int]] = None):
        super().__init__()
        self.data_paths = data_paths(local_ranks)
        self.action_queue = mp.Queue()
        self.data_queue = mp.Queue()
        self.options = options
        self.interval = interval
        self.recordings = []
        self.pid = os.getpid()

    def support_version(self):
        return "0.15.6"

    def message(self, m_type, payload):
        if m_type == "event":
            if payload["when"] == "initialize":
                return self.generate_process()
            elif payload["when"] == "post-stop":
                return self.stop_recording()
            elif payload["when"] == "pre-save":
                return self.save_data()
            elif payload["when"] == "pre-start":
                return self.start_recording()
        elif m_type == "command":
            if payload["cmd_type"] == "terminate":
                return self.terminate()
        return {}

    def generate_process(self):
        self.process = mp.Process(
            target=NeuronMonitorProcess(
                self.action_queue, self.data_queue, self.options, self.interval, self.data_paths
            ),
            daemon=True,
        )
        self.process.start()
        return {}

    def start_recording(self):
        return self.send_action("start")

    def stop_recording(self):
        self.recordings.append(self.send_action("stop"))
        return {}

    def save_data(self):
        self.recordings.append(self.send_action("get-data"))
        return {"action": "handle_data", "handler": self.append_data}

    def append_data(self, data):
        assert isinstance(data, dict)
        for recording in self.recordings:
            for k in recording.keys():
                for data_point in recording[k]:
                    d = {
                        # required by viztracer
                        "name": k,
                        "ph": "C",
                        "ts": data_point["ts"] * (1e6),
                        "args": data_point["arg"],
                        "pid": self.pid,
                        "tid": self.pid,
                    }
                    data["traceEvents"].append(d)
        self.recordings = []

    def terminate(self):
        self.send_action("terminate")
        self.process.join()
        return {"success": True}

    def send_action(self, message):
        if not self.process.is_alive():
            return {}
        self.action_queue.put(message)
        data = self.data_queue.get()
        return data


class NeuronMonitorProcess:
    def __init__(self, actions, data, options, interval: float, data_paths: List[str]):
        self.actions = actions
        self.data = data
        self.interval = interval
        self.options = options
        self.state = "stopped"
        self.record_handlers = {"memory_usage": self.memory_usage_handler}
        self.pack_handlers = {"memory_usage": self.memory_usage_pack}
        self.recordings = {}
        self.data_paths = data_paths
        self.init_recording()

    def __call__(self):
        while True:
            data = {}
            if not self.actions.empty():
                action = self.actions.get()
                if action == "start":
                    self.state = "running"
                    self.recordings["ts"].append(time.monotonic())
                elif action == "stop":
                    self.state = "stopped"
                    # to indicate the end of recording(otherwise the last data point will not be shown)
                    self.record_data()
                    # Every time we get a stop, record the data and send it back
                    # because we may never get the get-data command due to
                    # early process termination
                    data = self.pack_data()
                    self.init_recording()
                elif action == "get-data":
                    if self.state != "stopped":
                        self.state = "stopped"
                        self.record_data()
                    data = self.pack_data()
                    self.init_recording()
                elif action == "terminate":
                    break
                self.data.put(data)
            time.sleep(self.interval)
            if self.state == "running":
                self.record_data()
                self.recordings["ts"].append(time.monotonic())
        self.data.put({})

    def record_data(self):
        for k in self.options.keys():
            self.record_handlers[k]()

    def memory_usage_handler(self):
        for data_path in self.data_paths:
            for root, _, files in os.walk(data_path):
                if "memory_usage" not in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    counter_name = file_path[len(NEURON_SYSFS_PATH) + 1 :].replace(os.path.sep, ".")
                    if sysfs_val := sysfs(file_path):
                        self.recordings["memory_usage"][counter_name].append(float(sysfs_val))

    def pack_data(self):
        data = {k: self.pack_handlers[k]() for k in self.options.keys()}
        return data

    def memory_usage_pack(self):
        zipped = [
            {
                "ts": self.recordings["ts"][i],
                "arg": {k: v[i] for k, v in self.recordings["memory_usage"].items()},
            }
            for i in range(len(self.recordings["ts"]))
        ]
        return zipped

    def init_recording(self):
        self.recordings = {"memory_usage": defaultdict(list), "ts": []}
