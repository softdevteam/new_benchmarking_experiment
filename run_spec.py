#!/usr/bin/env python3

import csv
import os
import sys
from collections import OrderedDict
from subprocess import Popen, PIPE
from bs4 import BeautifulSoup

ITERATIONS = 2000
PROCESSES = 10

PATHS = {}
with open("paths.sh") as f:
    for line in f:
        k, v = line.strip().split("=")
        PATHS[k] = v

# This list of benchmarks can be found at the end of the SPEC JVM `-h` help
# text. We omit the "startup" benchmarks, designed to measure JVM startup time.
BENCHMARKS = [
    "compiler.compiler",
    "compiler.sunflow",
    "compress",
    "crypto.aes",
    "crypto.rsa",
    "crypto.signverify",
    "derby",
    "mpegaudio",
    "scimark.fft.large",
    "scimark.lu.large",
    "scimark.sor.large",
    "scimark.sparse.large",
    "scimark.fft.small",
    "scimark.lu.small",
    "scimark.sor.small",
    "scimark.sparse.small",
    "scimark.monte_carlo",
    "serial",
    "sunflow",
    "xml.transform",
    "xml.validation",
]

# Benchmarks which appear to be broken on certain VMs.
# Some benchmarks have bit-rotted, as this person also noted:
# https://github.com/JochenHiller/jvm-perftests/tree/master/SPECjvm2008#running-benchmark
BROKEN = {
    "graal-ce-hotspot": [
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "compiler.compiler",
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "compiler.sunflow",
    ],
    "graal-ce": [
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "compiler.compiler",
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "compiler.sunflow",
    ],
    "openj9": [
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "compiler.compiler",
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "compiler.sunflow",
    ]
}

# Each entry is a list of arguments used to invoke the VM.
JAVA_VMS = OrderedDict()
JAVA_VMS["graal-ce-hotspot"] = [os.path.join(PATHS["GRAALCE_DIR"],
                                             "bin", "java")]
JAVA_VMS["graal-ce"] = [os.path.join(PATHS["GRAALCE_DIR"], "bin", "java"),
                        "-XX:-EnableJVMCI", "-XX:-UseJVMCICompiler"]
JAVA_VMS["openj9"] = [os.path.join(PATHS["OPENJ9_DIR"], "bin", "java")]


def main():
    # Spec cannot be run outside of its install dir.
    os.chdir(PATHS["SPEC_DIR"])

    for jvm_name, jvm_args in JAVA_VMS.items():
        csvp = os.path.join("..", "spec.%s.results" % jvm_name)
        with open(csvp, 'w') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(
                ['processnum', 'benchmark'] + list(range(ITERATIONS)))

            for benchmark in BENCHMARKS:
                if benchmark in BROKEN[jvm_name]:
                    print("!!! %s::%s -- Skipping all. Marked broken." %
                          (jvm_name, benchmark))
                    sys.stdout.flush()
                    continue

                for pexec_idx in range(PROCESSES):
                    print(">>> %s::%s::%s" %
                          (jvm_name, benchmark, str(pexec_idx)))
                    sys.stdout.flush()

                    # Flush the CSV writing, and then give the OS some time to
                    # write stuff out to disk before running the next process
                    # execution.
                    csvf.flush()
                    os.fsync(csvf.fileno())

                    args = jvm_args + \
                        ["-Xms12G", "-Xmx12G", "-jar", PATHS["SPEC_JAR"],
                         # Measure fixed-load rather than throughput.
                         "--lagom",
                         # Skip "check" benchmarks that would normally run
                         # first.
                         "-ict", "-ikv",
                         # The benchmarks are quite long-running. We can make
                         # them faster by setting a smaller number of
                         # "operations"
                         "--operations", "1",
                         "-i", str(ITERATIONS),
                         benchmark]
                    p = Popen(args, stderr=PIPE, stdout=PIPE)
                    stdout, stderr = p.communicate()
                    stdout, stderr = stdout.decode(), stderr.decode()

                    # SPEC benchmarks exit status zero, even on failure. So we
                    # have to check the stdout for errors.
                    if p.returncode != 0 or "Iteration failed" in stdout:
                        sys.stderr.write(
                            "\nWARNING: process execution crashed\n")
                        sys.stderr.write("stdout:\n")
                        sys.stderr.write(stdout + "\n")
                        sys.stderr.write("\nstderr:\n")
                        sys.stderr.write(stderr + "\n")
                        sys.stderr.flush()
                        writer.writerow([pexec_idx, benchmark, "crash"])
                        continue

                    # Spec writes the results to an XML file at a path
                    # indicated on stdout.
                    next = False  # True when the next line contains the path.
                    xml_path = None
                    for line in stdout.splitlines():
                        if line.strip() == "Results are stored in:":
                            assert not next
                            next = True
                        elif next:
                            xml_path = line.strip()
                            break

                    assert xml_path is not None
                    output = parse_iteration_times(xml_path)
                    assert len(output) == ITERATIONS
                    writer.writerow([pexec_idx, benchmark] + output)


def parse_iteration_times(xml_path):
    with open(xml_path) as f:
        soup = BeautifulSoup(f, 'lxml')

    expect_iter = 1
    times = []
    for ir in soup.find_all("iteration-result"):
        assert expect_iter == int(ir.get("iteration"))
        expect_iter += 1

        start = int(ir.get("starttime"))
        end = int(ir.get("endtime"))
        delta = end - start
        assert delta > 0

        # The units are not documented anywhere, but looks like milliseconds.
        # Example:
        #   Iteration 1 (1 operation) begins: Tue Dec 10 16:05:18 GMT 2019
        #   Iteration 1 (1 operation) ends:   Tue Dec 10 16:05:20 GMT 2019
        #   delta = 1478, can only be milliseconds.
        times.append(delta / 1000.0)
    return times


if __name__ == '__main__':
    main()
