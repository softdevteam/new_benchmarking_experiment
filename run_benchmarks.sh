#! /bin/sh

# Copyright (c) 2019 King's College London created by the Software Development Team
# <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, or the UPL-1.0 license <http://opensource.org/licenses/UPL>
# at your option. This file may not be copied, modified, or distributed except according to those
# terms.

# This script runs the benchmarks (outside of Krun). For a version of the
# experiment you can run under Krun, see renaissance.krun.

set -e

sh setup.sh

RENAISSANCE_V="0.9.0"
GRAALCE_V="1.0.0-rc16"
# We run all benchmarks. Some of these are very slow.
# For a reduced set of fast benchmarks, use:
#BENCHMARKS="chi-square,future-genetic,gauss-mix,naive-bayes,rx-scrabble,scala-stm-bench7,scala-kmeans,scrabble"
BENCHMARKS="akka-uct,als,chi-square,db-shootout,dec-tree,dotty,dummy,finagle-chirper,finagle-http,fj-kmeans,future-genetic,gauss-mix,log-regression,mnemonics,movie-lens,naive-bayes,neo4j-analytics,page-rank,par-mnemonics,philosophers,reactors,rx-scrabble,scala-kmeans,scala-stm-bench7,scrabble"

PEXECS=10
IPITERS=2000

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
