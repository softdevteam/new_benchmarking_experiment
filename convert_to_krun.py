#! /usr/bin/env python3

# Copyright (c) 2019 King's College London created by the Software Development Team
# <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, or the UPL-1.0 license <http://opensource.org/licenses/UPL>
# at your option. This file may not be copied, modified, or distributed except according to those
# terms.

import csv, decimal, sys

if len(sys.argv) < 4 or sys.argv[1] != "-o":
    sys.stderr.write("Usage: process.py -o out.csv <file1.csv> ... <file2.csv>")
    sys.exit(1)

benchmark_data = {}
for p in sys.argv[3:]:
    with open(p, newline='') as csvf:
        local_benchmark = {}
        for row in csv.DictReader(csvf):
            bn = row["benchmark"]
            if bn not in local_benchmark:
                if bn not in benchmark_data:
                    benchmark_data[bn] = []
                local_benchmark[bn] = len(benchmark_data[bn])
                benchmark_data[bn].append([])
            time_s = decimal.Decimal(row["nanos"]) / 1000000000
            benchmark_data[bn][local_benchmark[bn]].append(str(time_s))

pexecs = len(benchmark_data[list(benchmark_data.keys())[0]])
iters = len(benchmark_data[list(benchmark_data.keys())[0]][0])

with open(sys.argv[2], "w") as f:
    f.write("process_exec_num, bench_name, %s\n" % ", ".join([str(x) for x in range(iters)]))
    for bn in benchmark_data:
        if len(benchmark_data[bn]) != pexecs:
            sys.stderr.write("%s doesn't have %d pexecs" % (bn, pexecs))
            sys.exit(1)
        for pexec in range(pexecs):
            if len(benchmark_data[bn][pexec]) != iters:
                sys.stderr.write("%s, pexec %d doesn't have %d in-process iterations" % (bn, pexec, iters))
                sys.exit(1)
            f.write("%d, %s, %s\n" % (pexec, bn, ", ".join(benchmark_data[bn][pexec])))
