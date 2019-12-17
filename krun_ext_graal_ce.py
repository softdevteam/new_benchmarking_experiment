#!/usr/bin/env python3

"""
Graal CE script for use with Krun's ExternalSuiteVMDef.
"""

import sys
from krun_ext_common import run, emit_process_exec_json


_, benchmark, num_iters, param, instr = sys.argv
emit_process_exec_json(run("graal-ce", benchmark, int(num_iters)))
