import argparse

from .monitor import NeuronMonitor


def get_vizplugin(arg):
    parser = argparse.ArgumentParser(prog="vizneuron.memory_usage")
    parser.add_argument("-f", help="The frequency of sampling", default=50)
    inputs = parser.parse_args(arg.split()[1:])
    options = {"memory_usage": True}
    interval = 1 / float(inputs.f)
    return NeuronMonitor(options, interval)
