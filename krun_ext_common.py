#!/usr/bin/env python3

import sys
import json
from subprocess import Popen, PIPE
from dataclasses import dataclass
from decimal import Decimal
import tempfile
import csv
import os


PATHS = {}
with open("paths.sh") as f:
    for line in f:
        k, v = line.strip().split("=")
        PATHS[k] = v

# Make sure these limits match those in the Krun config file.
JAVA_MEM_ARGS = ["-Xms12G", "-Xmx12G"]

# Use `java -jar renaissance-gpl-0.10.0.jar --raw-list` to get this list.
RENAISSANCE_BENCHMARKS = ["akka-uct", "als", "chi-square", "db-shootout",
                          "dec-tree", "dotty", "dummy", "finagle-chirper",
                          "finagle-http", "fj-kmeans", "future-genetic",
                          "gauss-mix", "log-regression", "mnemonics",
                          "movie-lens", "naive-bayes", "neo4j-analytics",
                          "page-rank", "par-mnemonics", "philosophers",
                          "reactors", "rx-scrabble", "scala-doku",
                          "scala-kmeans", "scala-stm-bench7", "scrabble"]

# Run `java -jar dacapo.jar -l` to get this list.
DACAPO_BENCHMARKS = ["avrora", "batik", "eclipse", "fop", "h2", "jython",
                     "luindex", "lusearch", "lusearch-fix", "pmd", "sunflow",
                     "tomcat", "tradebeans", "tradesoap", "xalan"]

# This list of benchmarks can be found at the end of the SPECjvm `-h` help
# text. We omit the "startup" benchmarks, designed to measure JVM startup time.
SPECJVM_BENCHMARKS = ["compiler.compiler", "compiler.sunflow", "compress",
                      "crypto.aes", "crypto.rsa", "crypto.signverify", "derby",
                      "mpegaudio", "scimark.fft.large", "scimark.lu.large",
                      "scimark.sor.large", "scimark.sparse.large",
                      "scimark.fft.small", "scimark.lu.small",
                      "scimark.sor.small", "scimark.sparse.small",
                      "scimark.monte_carlo", "serial", "sunflow", "xml.transform",
                      "xml.validation"]

# Let's prefix all of the benchmarks with their suite name, so that we can
# easily identify which suite a benchmark is from.
RENAISSANCE_BENCHMARKS = \
    [f"renaissance__{bm}" for bm in RENAISSANCE_BENCHMARKS]
DACAPO_BENCHMARKS = [f"dacapo__{bm}" for bm in DACAPO_BENCHMARKS]
SPECJVM_BENCHMARKS = [f"specjvm__{bm}" for bm in SPECJVM_BENCHMARKS]

# No benchmark should appear in more than one suite.
assert len(set(RENAISSANCE_BENCHMARKS).intersection(DACAPO_BENCHMARKS)) == 0
assert len(set(RENAISSANCE_BENCHMARKS).intersection(SPECJVM_BENCHMARKS)) == 0

SKIP_RENAISANCE = {
    "graal-ce": [
        # Doesn't do anything.
        "renaissance__dummy",
        # Use loopback networking.
        "renaissance__finagle-chirper", "renaissance__finagle-http",
    ],
    "graal-ce-hotspot": [
        # Doesn't do anything.
        "renaissance__dummy",
        # Use loopback networking.
        "renaissance__finagle-chirper", "renaissance__finagle-http",
    ],
    "openj9": [
        # Doesn't do anything.
        "dummy",
        # Use loopback networking.
        "finagle-chirper", "finagle-http",
    ],
}

# Some SPECjvm benchmarks have bit-rotted, as this person also noted:
# https://github.com/JochenHiller/jvm-perftests/tree/master/SPECjvm2008#running-benchmark
SKIP_SPECJVM = {
    "graal-ce-hotspot": [
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "specjvm__compiler.compiler",
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "specjvm__compiler.sunflow",
    ],
    "graal-ce": [
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "specjvm__compiler.compiler",
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "specjvm__compiler.sunflow",
    ],
    "openj9": [
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "specjvm__compiler.compiler",
        # spec.harness.StopBenchmarkException: Error invoking bmSetupBenchmarkMethod
        "specjvm__compiler.sunflow",
    ]
}

# Batik requires the proprietary Oracle JDK (OpenJDK and Graal Community
# Edition won't work):
# https://sourceforge.net/p/dacapobench/mailman/message/36012149/
#
# Eclipse benchmark has bitrotted and no longer works on modern JVMs:
# https://sourceforge.net/p/dacapobench/mailman/message/36013609/
# https://github.com/jon-bell/dacapo-eclipse-hacker
SKIP_DACAPO = {
    "graal-ce-hotspot": [
        # java.lang.NoClassDefFoundError: com/sun/image/codec/jpeg/TruncatedFileException
        "dacapo__batik",
        # java.lang.IllegalStateException: Unable to acquire application service.
        # Ensure that the org.eclipse.core.runtime bundle is resolved and started.
        "dacapo__eclipse",
        # URL /examples/jsp/jsp2/el/basic-arithmetic.jsp returned status 500 (expected 200)
        "dacapo__tomcat",
    ],
    "graal-ce": [
        # java.lang.NoClassDefFoundError: com/sun/image/codec/jpeg/TruncatedFileException
        "dacapo__batik",
        # java.lang.IllegalStateException: Unable to acquire application service.
        # Ensure that the org.eclipse.core.runtime bundle is resolved and started.
        "dacapo__eclipse",
        # URL /examples/jsp/jsp2/el/basic-arithmetic.jsp returned status 500 (expected 200)
        "dacapo__tomcat",
        # javax.ejb.FinderException: Cannot find account forPRGS
        "dacapo__tradesoap",
    ],
    "openj9": [
        # java.lang.NoClassDefFoundError: com.sun.image.codec.jpeg.TruncatedFileException
        "dacapo__batik",
        # java.lang.IllegalStateException: Unable to acquire application service.
        # Ensure that the org.eclipse.core.runtime bundle is resolved and started.
        "dacapo__eclipse",
        # URL /examples/jsp/jsp2/el/basic-arithmetic.jsp returned status 500 (expected 200)
        "dacapo__tomcat",
        # java.lang.ArrayIndexOutOfBoundsException: Array index out of range: -12
        "dacapo__tradebeans",
        # java.lang.ArrayIndexOutOfBoundsException: Array index out of range: -14
        "dacapo__tradesoap",
    ]
}


@dataclass
class DoneExec:
    suite: str
    benchmark: str
    args: str
    num_iters: int
    return_code: int
    stdout: str
    stderr: str


class ExecError(Exception):
    """We raise this when the child benchmark has crashed, to crash us in turn.
    Krun will detect our non-zero exit status and in-turn mark the run as
    crashed."""

    def __str__(self):
        done_exec = self.args[0]

        return ("\nWARNING: process execution crashed\n"
                f"\nexit status:\n{done_exec.return_code}\n"
                f"\nargs: {done_exec.args}\n"
                f"\nstdout:\n{done_exec.stdout}\n"
                f"\nstderr:\n{done_exec.stderr}\n")


def make_temp_file():
    """Make a temproary file and return its path"""
    with tempfile.NamedTemporaryFile() as f:
        return f.name


def run(vm, benchmark, num_iters):
    suite, benchmark = benchmark.split("__", maxsplit=1)

    args = get_vm_args(vm)
    temp_file, suite_args = get_suite_args(suite, benchmark, num_iters)
    args.extend(suite_args)

    done_exec = execute(args, suite, benchmark, num_iters)

    if done_exec.return_code != 0:
        raise ExecError(done_exec)

    res = post_process(done_exec, temp_file)

    if temp_file is not None:
        os.unlink(temp_file)

    return res


def execute(args, suite, benchmark, num_iters):
    """Runs the process execution and prints result JSON to stdout"""

    p = Popen(args, stderr=PIPE, stdout=PIPE)
    stdout, stderr = p.communicate()
    stdout, stderr = stdout.decode(), stderr.decode()

    return DoneExec(suite, benchmark, args, num_iters, p.returncode,
                    stdout, stderr)


def post_process(done_exec, temp_file):
    """For renaissance, `temp_file` is a path to a CSV file into which the
    results were written. For other suites, it is `None`."""

    if done_exec.suite == "renaissance":
        assert temp_file is not None
        return post_process_renaissance(done_exec, temp_file)
    elif done_exec.suite == "dacapo":
        assert temp_file is None
        return post_process_dacapo(done_exec)
    elif done_exec.suite == "specjvm":
        assert temp_file is None
        return post_process_specjvm(done_exec)
    else:
        raise ValueError("unknown suite %s" % done_exec.suite)


def post_process_renaissance(done_exec, tmp_file):
    """In renaissance, the results are simply written to a CSV file, which we
    now read back in."""

    wallclock_times = [-0.0] * done_exec.num_iters
    with open(tmp_file) as f:
        rows = iter(csv.reader(f))

        headers = rows.__next__()
        assert headers[0] == "benchmark"
        assert headers[1] == "nanos"

        for i, row in enumerate(rows):
            assert row[0] == done_exec.benchmark
            # nanos -> seconds.
            wallclock_times[i] = int(row[1]) / 1000000000

    assert len(wallclock_times) == done_exec.num_iters
    return wallclock_times


def post_process_dacapo(done_exec):
    wallclock_times = [-0.0] * done_exec.num_iters
    idx = 0

    # Dacapo offers no way to write the results to a file, so we have to scrape
    # the timings from stderr.
    for line in done_exec.stderr.splitlines():
        if not line.startswith("====="):
            continue
        if "completed warmup" not in line:
            continue
        assert done_exec.benchmark in line
        line = line.split()
        index = line.index("in")
        assert line[index + 2] == "msec"
        wallclock_times[idx] = float(Decimal(line[index + 1]) / 1000)
        idx += 1

    return wallclock_times


def post_process_specjvm(done_exec):
    # Although at this point we've already checked that the benchmark process
    # exited with zero, that isn't very helpful. Surprisingly, SPECjvm exits
    # with zero even when there were errors. We have to check stdout in order
    # to spot errors.
    if "Iteration failed" in done_exec.stdout:
        raise ExecError(done_exec)

    # Spec writes the results to an XML file at a path indicated on stdout.
    next = False  # True when the next line contains the path.
    xml_path = None
    for line in done_exec.stdout.splitlines():
        if line.strip() == "Results are stored in:":
            assert not next
            next = True
        elif next:
            xml_path = line.strip()
            break

    # We do this here because the XML parser is only required for SPECjvm
    # benchmarks.
    from bs4 import BeautifulSoup

    assert xml_path is not None
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


def emit_process_exec_json(wallclock_times):
    js = {
        "wallclock_times": wallclock_times,
        "core_cycle_counts": [],
        "aperf_counts": [],
        "mperf_counts": [],
    }

    sys.stdout.write("%s\n" % json.dumps(js))


def get_suite_args(suite, benchmark, num_iters):
    tmp_file = None  # Not used in all suites.

    jar = PATHS["%s_JAR" % suite.upper()]
    args = ["-jar", jar]

    if suite == "renaissance":
        tmp_file = make_temp_file()
        args.extend(["-r", str(num_iters), "--csv", tmp_file, benchmark])
    elif suite == "dacapo":
        args.extend([benchmark, "-n", str(num_iters + 1)])
    elif suite == "specjvm":
        specjvm_dir = os.path.dirname(PATHS["SPECJVM_JAR"])
        # See run_spec.py for the meaning of these flags.
        args.extend(["-Dspecjvm.home.dir=%s" % specjvm_dir, "--lagom", "-ict",
                     "-ikv", "--operations", "1", "-i", str(num_iters),
                     benchmark])
    else:
        raise ValueError("bad benchmark name: %s" % benchmark)

    return tmp_file, args


def get_vm_args(vm):
    if vm == "graal-ce":
        return [
            os.path.join(PATHS["GRAALCE_DIR"], "bin", "java")] + JAVA_MEM_ARGS
    elif vm == "graal-ce-hotspot":
        return [os.path.join(PATHS["GRAALCE_DIR"], "bin", "java")] + \
                JAVA_MEM_ARGS + ["-XX:-EnableJVMCI", "-XX:-UseJVMCICompiler"]
    elif vm == "openj9":
        return [
            os.path.join(PATHS["OPENJ9_DIR"], "bin", "java")] + JAVA_MEM_ARGS
    else:
        raise ValueError("bad vm: %s" % vm)
