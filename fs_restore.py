import os
import argparse
from xmlrpc.client import MAXINT
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import \
    PrivateL1PrivateL2CacheHierarchy
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.simpoint import SimPoint
from gem5.isas import ISA
from gem5.resources.resource import CustomDiskImageResource, Resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5.stats import dump, reset
from pathlib import Path
from gem5.simulate.exit_event_generators import (
    simpoint_save_checkpoint_generator,
)
from gem5.components.processors.simple_switchable_processor import(
    SimpleSwitchableProcessor,
)

parser = argparse.ArgumentParser(
    description="An fs restore checkpoint scrpit."
)

parser.add_argument(
    "--checkpoint_dir",
    type=str,
    required=True,
)

parser.add_argument(
    "--N",
    type=int,
    required=True,
)

parser.add_argument(
    "--warmup",
    type=int,
    required=True,
)

args = parser.parse_args()

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size = "32kB",
    l1i_size="32kB",
    l2_size="256kB",
)

memory = DualChannelDDR4_2400(size = "3GB")

# processor = SimpleSwitchableProcessor(
#     starting_core_type=CPUTypes.KVM,
#     switch_core_type=CPUTypes.O3,
#     num_cores= 1,
#     isa = ISA.X86,
# )

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    num_cores= 1,
    isa = ISA.X86,
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

command= "/home/gem5/single_thread_binaries/basicmath/basicmath_large;"\
    +"sleep 5;" \
    + "m5 exit;"

simpoint = SimPoint(
    simpoint_file_path = Path("simpointsFile.simpts"),
    weight_file_path = Path("weightsFile.weights"),
#     SimPoints information can also pass in manually with
#     simpoint_list = [#list of SimPoints]
#     weight_list = [#list of Weights]
    simpoint_interval = 100000000,
    warmup_interval = 100000000
)

board.set_kernel_disk_workload(
    # The x86 linux kernel will be automatically downloaded to the
    # `~/.cache/gem5` directoary if not already present.
    # npb benchamarks was tested with kernel version 4.19.83
    kernel=Resource(
        "x86-linux-kernel-5.4.49",
    ),
    # The x86-npb image will be automatically downloaded to the
    # `~/.cache/gem5` directory if not already present.
    disk_image=CustomDiskImageResource(
    os.path.join(
        os.path.expanduser("~"),
        "/home/studyztp/disk/disk-image/ubuntu-x86-single-thread-binaries-image/ubuntu-x86-single-thread-binaries"),
    disk_root_partition = "1"
    ),
    readfile_contents=command,
)

dir = Path(args.checkpoint_dir).as_posix()

def max_inst():
    warmed_up = False
    while True:
        if warmed_up:
            print("end of SimPoint interval")
            yield True
        else:
            print("end of warmup, starting to simulate SimPoint")
            warmed_up = True
            # schedule a MAX_INSTS exit event during the simulation
            simulator.schedule_max_insts(simpoint.get_simpoint_interval())
            dump()
            reset()
            yield False


simulator = Simulator(
    full_system= True,
    board=board,
    checkpoint_path=dir,
    on_exit_event={
        ExitEvent.MAX_INSTS: max_inst()
    }
)
warmup_len = simpoint.get_warmup_list()[args.N]
if warmup_len == 0:
    warmup_len = 1
simulator.schedule_max_insts(warmup_len , True)
simulator.run()

print(f"simpoint_insts: {simpoint.get_simpoint_start_insts()}\n")
print(f"simpoint_length: {simpoint.get_simpoint_interval()}\n")
print(f"simpoint_warmup: {simpoint.get_warmup_list()}\n")
print(f"simpoint_weight: {simpoint.get_weight_list()}\n")
