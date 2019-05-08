#! /bin/sh

# Copyright (c) 2019 King's College London created by the Software Development Team
# <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, or the UPL-1.0 license <http://opensource.org/licenses/UPL>
# at your option. This file may not be copied, modified, or distributed except according to those
# terms.

set -e

RENAISSANCE_V="0.9.0"
GRAALCE_V="1.0.0-rc16"
# This is the full list of benchmarks, but some of these are very slow
# BENCHMARKS="actors,apache-spark,database,jdk-concurrent,jdk-streams,neo4j,rx,scala-dotty,scala-stdlib,scala-stm,twitter-finagle"
# The benchmark list we're using below are the somewhat faster ones
BENCHMARKS="chi-square,future-genetic,gauss-mix,naive-bayes,rx-scrabble,scala-stm-bench7,scala-kmeans,scrabble"
PEXECS=10
IPITERS=2000

if [ ! -f renaissance-gpl-${RENAISSANCE_V}.jar ]; then
    wget https://github.com/renaissance-benchmarks/renaissance/releases/download/v${RENAISSANCE_V}/renaissance-gpl-${RENAISSANCE_V}.jar
fi

if [ ! -d graalvm-ce-${GRAALCE_V} ]; then
    wget https://github.com/oracle/graal/releases/download/vm-${GRAALCE_V}/graalvm-ce-${GRAALCE_V}-linux-amd64.tar.gz
    tar xfz graalvm-ce-${GRAALCE_V}-linux-amd64.tar.gz
fi

i=0
while [ $i -lt ${PEXECS} ]; do
    # The following JVM invocations are adopted from those detailed in:
    #  https://github.com/renaissance-benchmarks/measurements/blob/7d3f09e05df3c5477fabe531ec5effc07e33f7aa/README.md

    # Graal CE running the normal HotSpot compiler
    graalvm-ce-${GRAALCE_V}/bin/java -Xms12G -Xmx12G -XX:-EnableJVMCI -XX:-UseJVMCICompiler -jar renaissance-gpl-${RENAISSANCE_V}.jar -r ${IPITERS} --csv openjdk-pexec-${i}.csv $BENCHMARKS

    # Graal CE
    graalvm-ce-${GRAALCE_V}/bin/java -Xms12G -Xmx12G -jar renaissance-gpl-${RENAISSANCE_V}.jar -r ${IPITERS} --csv graalvm-ce-pexec-${i}.csv $BENCHMARKS
    i=$(($i + 1))
done

./convert_to_krun.py -o openjdk.csv openjdk-pexec*.csv
./convert_to_krun.py -o graalvm-ce.csv graalvm-ce-pexec*.csv
