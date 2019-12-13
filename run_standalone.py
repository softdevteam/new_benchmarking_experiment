#! /usr/bin/env python3

import csv
import os
import sys
from krun_ext_common import ExecError, run

JAVA_VMS = ["graal-ce-hotspot", "graal-ce", "openj9"]


def main(suite, num_pexecs, num_ipis):
    if suite == "renaissance":
        from krun_ext_common import RENAISSANCE_BENCHMARKS as benchmarks
        from krun_ext_common import SKIP_RENAISANCE as skip
    elif suite == "dacapo":
        from krun_ext_common import DACAPO_BENCHMARKS as benchmarks
        from krun_ext_common import SKIP_DACAPO as skip
    elif suite == "spec":
        from krun_ext_common import SPEC_BENCHMARKS as benchmarks
        from krun_ext_common import SKIP_SPEC as skip
    else:
        raise ValueError(f"invalid suite: {suite}")

    for jvm_name in JAVA_VMS:
        csvp = "dacapo.%s.results" % jvm_name
        with open(csvp, 'w') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(
                ['processnum', 'benchmark'] + list(range(num_ipis)))

            for benchmark in benchmarks:
                if benchmark in skip[jvm_name]:
                    print("!!! %s::%s -- Skipping all. "
                          "Marked skipped/broken." % (jvm_name, benchmark))
                    sys.stdout.flush()
                    continue

                for pexec_idx in range(num_pexecs):
                    print(">>> %s::%s::%s" %
                          (jvm_name, benchmark, str(pexec_idx)))
                    sys.stdout.flush()

                    # Flush the CSV writing, and then give the OS some time to
                    # write stuff out to disk before running the next process
                    # execution.
                    csvf.flush()
                    os.fsync(csvf.fileno())

                    try:
                        wcts = run(jvm_name, benchmark, num_ipis)
                    except ExecError as e:
                        sys.stderr.write(str(e))
                        sys.stderr.flush()
                        writer.writerow([pexec_idx, benchmark, "crash"])
                        continue

                    assert len(wcts) == num_ipis
                    writer.writerow([pexec_idx, benchmark] + wcts)


if __name__ == '__main__':
    try:
        suite, num_pexecs, num_ipis = sys.argv[1:]
        num_pexecs, num_ipis = int(num_pexecs), int(num_ipis)
    except (IndexError, ValueError):
        print("usage: run_standalone <suite> <#process-executions> "
              "<#in-process-iterations>")
        sys.exit(1)

    main(suite, num_pexecs, num_ipis)
