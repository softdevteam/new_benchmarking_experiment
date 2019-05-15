#!/usr/bin/env python3

# Copyright (c) 2019 King's College London
# Created by the Software Development Team <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT
# or http://opensource.org/licenses/MIT>, or the UPL-1.0 license
# <http://opensource.org/licenses/UPL> at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import sys
import json
import subprocess
import tempfile
import csv
import os


def make_temp_file():
    """Make a temproary file and return its path"""
    with tempfile.NamedTemporaryFile() as f:
        return f.name


def run(args, benchmark, num_iters, tmp_file):
    """Runs the process execution and prints result JSON to stdout"""

    # Krun expects to see the results printed in JSON format to stdout. We
    # redirect anything the benchmarks print on stdout to stderr.
    subprocess.run(args, shell=False, stdout=sys.stderr.fileno())

    wallclock_times = [-0.0] * num_iters
    with open(tmp_file) as f:
        rows = iter(csv.reader(f))

        headers = rows.__next__()
        assert headers[0] == "benchmark"
        assert headers[1] == "nanos"

        for i, row in enumerate(rows):
            assert row[0] == benchmark
            wallclock_times[i] = int(row[1]) / 1000000000  # nanos -> seconds.

    assert len(wallclock_times) == num_iters

    js = {
        "wallclock_times": wallclock_times,
        "core_cycle_counts": [],
        "aperf_counts": [],
        "mperf_counts": [],
    }

    sys.stdout.write("%s\n" % json.dumps(js))

    os.unlink(tmp_file)
