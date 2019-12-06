#! /usr/bin/env python3

import csv
import os
import sys
from decimal import Decimal
from collections import OrderedDict
from subprocess import Popen, PIPE

ITERATIONS = 2000
PROCESSES = 10

PATHS = {}
with open("paths.sh") as f:
    for line in f:
        k, v = line.strip().split("=")
        PATHS[k] = v

# Run `java -jar dacapo.jar -l` to get this list.
BENCHMARKS = ["avrora", "batik", "eclipse", "fop", "h2", "jython",
              "luindex", "lusearch", "lusearch-fix", "pmd", "sunflow",
              "tomcat", "tradebeans", "tradesoap", "xalan"]

# Benchmarks which appear to be broken on certain VMs.
#
# Batik requires the proprietary Oracle JDK (OpenJDK and Graal Community
# Edition won't work):
# https://sourceforge.net/p/dacapobench/mailman/message/36012149/
#
# Eclipse benchmark has bitrotted and no longer works on modern JVMs:
# https://sourceforge.net/p/dacapobench/mailman/message/36013609/
# https://github.com/jon-bell/dacapo-eclipse-hacker
BROKEN = {
    "graal-ce-hotspot": [
        # java.lang.NoClassDefFoundError: com/sun/image/codec/jpeg/TruncatedFileException
        "batik",
        # java.lang.IllegalStateException: Unable to acquire application service.
        # Ensure that the org.eclipse.core.runtime bundle is resolved and started.
        "eclipse",
        # URL /examples/jsp/jsp2/el/basic-arithmetic.jsp returned status 500 (expected 200)
        "tomcat",
    ],
    "graal-ce": [
        # java.lang.NoClassDefFoundError: com/sun/image/codec/jpeg/TruncatedFileException
        "batik",
        # java.lang.IllegalStateException: Unable to acquire application service.
        # Ensure that the org.eclipse.core.runtime bundle is resolved and started.
        "eclipse",
        # URL /examples/jsp/jsp2/el/basic-arithmetic.jsp returned status 500 (expected 200)
        "tomcat",
        # javax.ejb.FinderException: Cannot find account forPRGS
        "tradesoap",
    ],
    "openj9": [
        # java.lang.NoClassDefFoundError: com.sun.image.codec.jpeg.TruncatedFileException
        "batik",
        # java.lang.IllegalStateException: Unable to acquire application service.
        # Ensure that the org.eclipse.core.runtime bundle is resolved and started.
        "eclipse",
        # URL /examples/jsp/jsp2/el/basic-arithmetic.jsp returned status 500 (expected 200)
        "tomcat",
        # java.lang.ArrayIndexOutOfBoundsException: Array index out of range: -12
        "tradebeans",
        # java.lang.ArrayIndexOutOfBoundsException: Array index out of range: -14
        "tradesoap",
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
    for jvm_name, jvm_args in JAVA_VMS.items():
        csvp = "dacapo.%s.results" % jvm_name
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

                    args = jvm_args + ["-Xms12G", "-Xmx12G", "-jar",
                                       PATHS["DACAPO_JAR"], benchmark, "-n",
                                       str(ITERATIONS + 1)]
                    p = Popen(args, stderr=PIPE, stdout=PIPE)
                    stdout, stderr = p.communicate()
                    stdout, stderr = stdout.decode(), stderr.decode()

                    if p.returncode != 0:
                        sys.stderr.write(
                            "\nWARNING: process execution crashed\n")
                        sys.stderr.write("stdout:\n")
                        sys.stderr.write(stdout + "\n")
                        sys.stderr.write("\nstderr:\n")
                        sys.stderr.write(stderr + "\n")
                        sys.stderr.flush()
                        writer.writerow([pexec_idx, benchmark, "crash"])
                        continue

                    # Dacapo offers no way to write the results to a file, so
                    # we have to scrape the timings from stderr.
                    output = []
                    for line in stderr.splitlines():
                        if not line.startswith("====="):
                            continue
                        if "completed warmup" not in line:
                            continue
                        assert benchmark in line
                        line = line.split()
                        index = line.index("in")
                        assert line[index + 2] == "msec"
                        output.append(str(Decimal(line[index + 1]) / 1000))

                    assert len(output) == ITERATIONS
                    writer.writerow([pexec_idx, benchmark] + output)


if __name__ == '__main__':
    main()
