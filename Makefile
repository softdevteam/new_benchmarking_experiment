# Copyright (c) 2019 King's College London
# Created by the Software Development Team <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT
# or http://opensource.org/licenses/MIT>, or the UPL-1.0 license
# <http://opensource.org/licenses/UPL> at your option. This file may not be
# copied, modified, or distributed except according to those terms.

FETCH=wget
PYTHON=python3

RENAISSANCE_V=0.10.0
RENAISSANCE_JAR=renaissance-gpl-${RENAISSANCE_V}.jar

DACAPO_V=9.12
DACAPO_JAR=dacapo-${DACAPO_V}-MR1-bach.jar

SPECJVM_INSTALL_JAR=SPECjvm2008_1_01_setup.jar
SPECJVM_DIR=SPECjvm2008_1_01
SPECJVM_JAR=SPECjvm2008.jar

# For the VMs, we use the latest versions that target JDK11 at the time of writing.
GRAALCE_V=19.3.0
GRAALCE_DIR=graalvm-ce-java11-${GRAALCE_V}
GRAALCE_TGZ=graalvm-ce-java11-linux-amd64-${GRAALCE_V}.tar.gz

J9_V=0.17.0
J9_TGZ=OpenJDK11U-jdk_x64_linux_openj9_11.0.5_10_openj9-${J9_V}.tar.gz
J9_DIR=OpenJDK11U-jdk_x64_linux_openj9_11.0.5_10_openj9-${J9_V}

PATHS_SH=paths.sh

KRUN_SNIPPET=krun_snippet.py

TOP_DIR=`pwd`

KRUN_DIR=krun
KRUN=${KRUN_DIR}/krun.py
KRUN_VERSION=8f59b2b2c96733bf05d75fa9481a539094a94008
LIBKRUNTIME=${KRUN_DIR}/libkrun/libkruntime.so

PEXECS=10
INPROC_ITERS=2000

TEST_PEXECS=1
TEST_INPROC_ITERS=3

.PHONY: setup
setup: ${GRAALCE_DIR} ${J9_DIR} ${RENAISSANCE_JAR} ${DACAPO_JAR} ${SPECJVM_DIR}/${SPECJVM_JAR} ${LIBKRUNTIME} ${KRUN_SNIPPET}
	echo OPENJ9_DIR=${TOP_DIR}/${J9_DIR} > ${PATHS_SH}
	echo GRAALCE_DIR=${TOP_DIR}/${GRAALCE_DIR} >> ${PATHS_SH}
	echo RENAISSANCE_JAR=${TOP_DIR}/${RENAISSANCE_JAR} >> ${PATHS_SH}
	echo DACAPO_JAR=${DACAPO_JAR} >> ${PATHS_SH}
	echo SPECJVM_JAR=${TOP_DIR}/${SPECJVM_DIR}/${SPECJVM_JAR} >> ${PATHS_SH}
	echo SPECJVM_DIR=${TOP_DIR}/${SPECJVM_DIR} >> ${PATHS_SH}

${RENAISSANCE_JAR}:
	${FETCH} https://github.com/renaissance-benchmarks/renaissance/releases/download/v${RENAISSANCE_V}/${RENAISSANCE_JAR}

${DACAPO_JAR}:
	${FETCH} https://downloads.sourceforge.net/project/dacapobench/${DACAPO_V}-bach-MR1/${DACAPO_JAR}

${SPECJVM_INSTALL_JAR}:
	${FETCH} http://spec.cs.miami.edu/downloads/osg/java/${SPECJVM_INSTALL_JAR}

${SPECJVM_DIR}/${SPECJVM_JAR}: ${SPECJVM_INSTALL_JAR}
	# We are downloading from a mirror, as spec.org uses magic to obfuscate
	# their FTP link. To be sure it's the same JAR, we check the md5 hash.
	[ "`md5sum ${SPECJVM_INSTALL_JAR} | awk '{print $$1}'`" = "144fc07007fc099befd3d51d5992cbcf" ]
	${GRAALCE_DIR}/bin/java -jar ${SPECJVM_INSTALL_JAR} \
		-DUSER_INSTALL_DIR=${SPECJVM_DIR} -i silent
	# To prevent make re-running the installer.
	# (installer extracts with a datestamp from 2009).
	touch ${SPECJVM_DIR}/${SPECJVM_JAR}

${GRAALCE_TGZ}:
	${FETCH} https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-${GRAALCE_V}/${GRAALCE_TGZ}

${GRAALCE_DIR}: ${GRAALCE_TGZ}
	tar xfz ${GRAALCE_TGZ}

${J9_TGZ}:
	${FETCH} https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.5%2B10_openj9-${J9_V}/${J9_TGZ}

${J9_DIR}: ${J9_TGZ}
	tar xzf ${J9_TGZ}
	mv jdk-11.0.5+10 ${J9_DIR}

.PHONY: krun
krun: ${LIBKRUNTIME}

${KRUN}:
	git clone https://github.com/softdevteam/krun ${KRUN_DIR}
	cd ${KRUN_DIR} && git checkout ${KRUN_VERSION}

${LIBKRUNTIME}: ${KRUN}
	cd ${KRUN_DIR} && ${MAKE} NO_MSRS=1

${KRUN_SNIPPET}: krun_ext_common.py mk_krun_snippet.py
	${PYTHON} mk_krun_snippet.py $@

run-standalone: run-renaissance-standalone run-dacapo-standalone run-spec-standalone

run-renaissance-standalone: setup
	${PYTHON} run_standalone.py renaissance ${PEXECS} ${INPROC_ITERS}

run-dacapo-standalone: setup
	${PYTHON} run_standalone.py dacapo ${PEXECS} ${INPROC_ITERS}

run-spec-standalone: setup
	${PYTHON} run_standalone.py spec ${PEXECS} ${INPROC_ITERS}

# Run a small set of quick tests to check things are not obviously broken.
test: setup
	# Test Krun ext scripts run OK and generate valid JSON.
	${PYTHON} -c "import json; json.loads('`${PYTHON} krun_ext_graal_ce.py renaissance__akka-uct ${TEST_INPROC_ITERS} 0 0`')"
	${PYTHON} -c "import json; json.loads('`${PYTHON} krun_ext_graal_ce.py dacapo__avrora ${TEST_INPROC_ITERS} 0 0`')"
	${PYTHON} -c "import json; json.loads('`${PYTHON} krun_ext_graal_ce.py specjvm__compress ${TEST_INPROC_ITERS} 0 0`')"

	# Quick standalone runs.
	${PYTHON} run_standalone.py renaissance ${TEST_PEXECS} ${TEST_INPROC_ITERS}
	${PYTHON} run_standalone.py dacapo ${TEST_PEXECS} ${TEST_INPROC_ITERS}
	${PYTHON} run_standalone.py spec ${TEST_PEXECS} ${TEST_INPROC_ITERS}

.PHONY: clean
clean: clean-krun-results clean-temp-files
	rm -rf ${RENAISSANCE_JAR} ${GRAALCE_TGZ} ${GRAALCE_DIR} ${J9_TGZ} \
		${J9_DIR} ${SPECJVM_DIR} ${SPECJVM_INSTALL_JAR} ${KRUN_SNIPPET}

clean-krun-results:
	rm -rf experiment_results.json.bz2 experiment.log experiment.manifest \
		experiment_envlogs

# The suites have a tendency to write stuff all over the experiment dir.
clean-temp-files:
	rm -rf page_rank* scratch target
