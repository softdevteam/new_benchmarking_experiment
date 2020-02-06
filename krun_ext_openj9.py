#!/usr/bin/env python3

"""
OpenJ9 script for use with Krun's ExternalSuiteVMDef.
"""

import sys
from krun_ext_common import run, emit_process_exec_json


_, benchmark, num_iters, param, instr = sys.argv
emit_process_exec_json(run("openj9", benchmark, int(num_iters)))
