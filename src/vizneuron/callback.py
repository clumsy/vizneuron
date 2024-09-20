import atexit
import signal
from typing import Optional

import pytorch_lightning as pl
from viztracer import VizTracer

from .monitor import NeuronMonitor


class VizNeuron(pl.Callback):
    def __init__(self, output_path_prefix: str, save_every_n_steps: Optional[int] = None):
        self.output_path_prefix = output_path_prefix
        self.save_every_n_steps = save_every_n_steps
        self.tracer: Optional[VizTracer] = None
        self.rank: Optional[int] = None
        self.oprimizer_step = False

        signal.signal(signal.SIGTERM, self.teardown)  # terminate signal
        signal.signal(signal.SIGINT, self.teardown)  # keyboard interrupt
        atexit.register(self._terminate)

    def on_train_start(self, trainer: pl.Trainer, *args, **kwargs) -> None:
        self._start(trainer)
        self.rank = trainer.global_rank

    def on_train_batch_end(self, trainer: pl.Trainer, *args, **kwargs):
        if self.optimizer_step:
            if (trainer.global_step + 1) % self.save_every_n_steps == 0:
                self._stop(trainer)
                self._start(trainer)
            self.optimizer_step = False

    def on_before_optimizer_step(self, *args, **kwargs) -> None:
        self.optimizer_step = True

    def teardown(self, *args, **kwargs) -> None:
        self._terminate()

    def on_exception(self, *args, **kwargs) -> None:
        self._terminate()

    def _start(self, trainer: pl.Trainer) -> None:
        if not self.tracer:
            self.tracer = VizTracer(plugins=[NeuronMonitor(options={"memory_usage": True}, interval=1. / 50, local_ranks=[trainer.local_rank])])
        self.tracer.start()

    def _stop(self, trainer: Optional["pl.Trainer"] = None) -> None:
        if not self.tracer:
            return
        self.tracer.stop()
        suffix = trainer.global_step + 1 if trainer else "last"
        output_file = f"{self.output_path_prefix}_rank{self.rank}_{suffix}.json"
        self.tracer.save(output_file=output_file)

    def _terminate(self) -> None:
        if self.tracer:
            self._stop()
            self.tracer.terminate()
            self.tracer = None
