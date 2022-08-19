import os

from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.simpoint import SimPoint
from gem5.isas import ISA
from gem5.resources.resource import CustomResource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5.stats import dump, reset
from pathlib import Path
from gem5.simulate.exit_event_generators import (
    simpoint_save_checkpoint_generator,
)
import argparse
import m5
from gem5.components.boards.simple_board import SimpleBoard

parser = argparse.ArgumentParser(
    description="An fs checkpoint checkpoint scrpit."
)

parser.add_argument(
    "--checkpoint_dir",
    type=str,
    required=True,
)

parser.add_argument(
    "--warmup",
    type=int,
    required=True,
)

args = parser.parse_args()

cache_hierarchy = NoCache()

memory = SingleChannelDDR3_1600(size = "3GB")

processor = SimpleProcessor(
    cpu_type=CPUTypes.ATOMIC,
    num_cores= 1,
    isa = ISA.X86,
)

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

simpoint = SimPoint(
    simpoint_file_path = Path("/home/studyztp/others/auto_se_test/basicmath/basicmath_large.simpts"),
    weight_file_path = Path("/home/studyztp/others/auto_se_test/basicmath/basicmath_large.weights"),
    simpoint_interval = 100000000,
    warmup_interval = args.warmup
    
)

board.set_se_binary_workload(
    binary = CustomResource("/home/studyztp/others/auto_se_test/basicmath/binary/basicmath_large"),
    simpoint = simpoint
)

dir = Path(args.checkpoint_dir)
dir.mkdir(exist_ok=True)

def simpoint_gen():
    count = 0
    while True:
        m5.checkpoint((dir / str(count)).as_posix())
        count += 1
        if count < len(simpoint.get_simpoint_start_insts()):
            yield False
        else:
            yield True

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.SIMPOINT_BEGIN: simpoint_gen()
    }
)

simulator.run()

print(f"simpoint_insts: {simpoint.get_simpoint_start_insts()}\n")
print(f"simpoint_length: {simpoint.get_simpoint_interval()}\n")
print(f"simpoint_warmup: {simpoint.get_warmup_list()}\n")
print(f"simpoint_weight: {simpoint.get_weight_list()}\n")