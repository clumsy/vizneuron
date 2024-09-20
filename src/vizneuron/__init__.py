import argparse

from .monitor import NeuronMonitor

__version__ = "0.0.1"


def get_vizplugin(arg):
    parser = argparse.ArgumentParser(prog="vizneuron")
    parser.add_argument("-f", help="The frequency of sampling", default=50)
    parser.add_argument("--memory_usage", action="store_true")
    inputs = parser.parse_args(arg.split()[1:])
    options = {}
    if inputs.memory_usage:
        options["memory_usage"] = True
    interval = 1 / float(inputs.f)
    return NeuronMonitor(options, interval)
