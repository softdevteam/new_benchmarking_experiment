#!/usr/bin/env python3

"""
Graal CE (running the normal HotSpot compiler) script for use with Krun's
ExternalSuiteVMDef.
"""

import sys
from krun_ext_common import make_temp_file, run

RENAISSANCE_V = "0.9.0"
GRAALCE_V = "1.0.0-rc16"

_, benchmark, num_iters, param, instr = sys.argv
temp_file = make_temp_file()

# Ensure the -Xms/-Xmx args match the stack/heap values in the Krun config!
args = [
    "graalvm-ce-%s/bin/java" % GRAALCE_V,
    "-Xms12G", "-Xmx12G", "-XX:-EnableJVMCI", "-XX:-UseJVMCICompiler",
    "-jar", "renaissance-gpl-%s.jar" % RENAISSANCE_V,
    "-r", num_iters, "--csv", temp_file, benchmark
]

run(args, benchmark, int(num_iters), temp_file)
