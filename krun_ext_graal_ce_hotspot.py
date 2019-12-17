#!/usr/bin/env python3

"""
Graal CE (running the normal HotSpot compiler) script for use with Krun's
ExternalSuiteVMDef.
"""

import sys
from krun_ext_common import run, emit_process_exec_json


_, benchmark, num_iters, param, instr = sys.argv
emit_process_exec_json(run("graal-ce-hotspot", benchmark, int(num_iters)))
