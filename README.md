# VizNeuron
[VizTracer](https://github.com/gaogaotiantian/viztracer) plugins for AWS Neuron.
It is inspired by the official VizTracer plugings: [vizplugins](https://github.com/gaogaotiantian/vizplugins).

# Features
VizNeuron currently only supports memory usage tracing via [Neuron Sysfs Filesystem](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/tools/neuron-sys-tools/neuron-sysfs-user-guide.html#neuron-sysfs-filesystem-structure).

# Install
The preferred way to install VizNeuron is via pip:

```sh
git clone git@github.com:clumsy/vizneuron.git && cd vizneuron
pip install -e .
```

# Basic Usage
VizNeuron should be used with VizTracer.

You can use VizNeuron and the plugin via command line:

```sh
viztracer --plugin vizneuron.memory_usage -- my_script.py arg1 arg2
```

Or equivalent syntax:

```sh
viztracer --plugin "vizneuron --memory_usage" -- my_script.py arg1 arg2
```

You can also add the plugin to VizTracer programmatically as described in the [official documentation](https://viztracer.readthedocs.io/en/latest/plugins.html).

Finally, VizNeuron provides a [PyTorch Lightning Callback](https://lightning.ai/docs/pytorch/stable/extensions/callbacks.html) that can be used as part of model training.
